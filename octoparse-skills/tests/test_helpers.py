import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("octoparse_installer", ROOT / "install.py")
admin = load("datahub_admin", ROOT / "octoparse-datahub-job-admin/scripts/patch_datahub.py")
monitor = load("cdc_monitor", ROOT / "octoparse-cdc-verify-repair/scripts/monitor_cdc.py")


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.destination = self.root / "global"
        self.source.mkdir()
        for name in ["skill-a", "skill-b"]:
            (self.source / name).mkdir()
            (self.source / name / "SKILL.md").touch()

    def test_preview_does_not_create_destination(self):
        actions = installer.install(self.source, self.destination)
        self.assertEqual(len(actions), 2)
        self.assertFalse(self.destination.exists())

    def test_install_and_repeat_preserve_links(self):
        installer.install(self.source, self.destination, True)
        self.assertEqual((self.destination / "skill-a").resolve(), (self.source / "skill-a").resolve())
        actions = installer.install(self.source, self.destination, True)
        self.assertEqual([item[2] for item in actions], ["already-linked", "already-linked"])

    def test_conflict_preflight_leaves_all_paths_untouched(self):
        self.destination.mkdir()
        (self.destination / "skill-b").mkdir()
        with self.assertRaises(FileExistsError):
            installer.install(self.source, self.destination, True)
        self.assertFalse((self.destination / "skill-a").exists())
        self.assertTrue((self.destination / "skill-b").is_dir())

    def test_broken_link_is_a_conflict(self):
        self.destination.mkdir()
        link = self.destination / "skill-a"
        link.symlink_to(self.root / "missing")
        with self.assertRaises(FileExistsError):
            installer.install(self.source, self.destination, True)
        self.assertTrue(link.is_symlink())

    def test_install_failure_rolls_back_only_new_links(self):
        original = Path.symlink_to

        def interrupted(link, target, **kwargs):
            if link.name == "skill-b":
                raise OSError("simulated filesystem failure")
            return original(link, target, **kwargs)

        with patch.object(Path, "symlink_to", interrupted), self.assertRaises(OSError):
            installer.install(self.source, self.destination, True)
        self.assertFalse(os.path.lexists(self.destination / "skill-a"))


class AdminTests(unittest.TestCase):
    def setUp(self):
        self.job = {
            "id": "sync-example", "name": "Example", "description": "before",
            "jobType": 0, "jobConfig": json.dumps({"password": "not-a-real-secret"}),
            "jobParameters": [{"name": "@from", "description": "window"}],
        }
        self.plan = {"id": "plan-id", "name": "plan", "description": "before",
                     "cron": "0 0 31 2 *", "runType": 2,
                     "jobPlanSteps": [{"id": "step-id", "jobId": "sync-example"}]}

    def test_default_is_read_only_preview(self):
        with patch.object(admin, "call", side_effect=[{"environment": "test"}, self.job]) as calls:
            report = admin.patch_definition("job", "sync-example", {"description": "after"}, "test")
        self.assertFalse(report["applied"])
        self.assertEqual(calls.call_count, 2)
        self.assertNotIn("not-a-real-secret", json.dumps(report))

    def test_parameter_get_only_metadata_is_not_submitted(self):
        document = copy.deepcopy(self.job)
        document["jobParameters"][0]["id"] = "get-only-metadata"
        request = admin.body("job", document)
        self.assertEqual(request["jobParameters"], self.job["jobParameters"])
        self.assertEqual(document["jobParameters"][0]["id"], "get-only-metadata")

    def test_environment_mismatch_prevents_definition_read_or_write(self):
        with patch.object(admin, "call", return_value={"environment": "wrong"}) as calls:
            with self.assertRaises(admin.ContractError):
                admin.patch_definition("job", "sync-example", {"description": "after"}, "test", True)
        self.assertEqual(calls.call_count, 1)

    def test_wrong_identity_rejected(self):
        with patch.object(admin, "call", side_effect=[{"environment": "test"}, self.job]):
            with self.assertRaises(admin.ContractError):
                admin.patch_definition("job", "other-id", {"description": "after"}, "test", True)

    def test_apply_private_body_and_cleanup_preserves_configuration(self):
        state = copy.deepcopy(self.job)
        submitted_paths = []

        def fake(args):
            if args == ["info"]:
                return {"environment": "test"}
            if "update" in args:
                path = Path(args[args.index("--file") + 1])
                submitted_paths.append(path)
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
                self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
                request = json.loads(path.read_text())
                self.assertEqual(request["jobConfig"], self.job["jobConfig"])
                self.assertEqual(request["jobParameters"], self.job["jobParameters"])
                state.update(request)
                return state
            return copy.deepcopy(state)

        with patch.object(admin, "call", side_effect=fake):
            report = admin.patch_definition("job", "sync-example", {"description": "after"}, "test", True)
        self.assertTrue(report["applied"])
        self.assertEqual(state["description"], "after")
        self.assertEqual(len(submitted_paths), 1)
        self.assertFalse(submitted_paths[0].exists())

    def test_concurrent_configuration_change_aborts(self):
        fresh = {**self.job, "jobConfig": "changed by user"}
        responses = [{"environment": "test"}, self.job, {"environment": "test"}, fresh]
        with patch.object(admin, "call", side_effect=responses) as calls:
            with self.assertRaisesRegex(admin.ContractError, "concurrently"):
                admin.patch_definition("job", "sync-example", {"description": "after"}, "test", True)
        self.assertFalse(any("update" in item.args[0] for item in calls.call_args_list))

    def test_environment_change_before_write_aborts(self):
        responses = [{"environment": "test"}, self.job, {"environment": "other"}]
        with patch.object(admin, "call", side_effect=responses) as calls:
            with self.assertRaises(admin.ContractError):
                admin.patch_definition("job", "sync-example", {"description": "after"}, "test", True)
        self.assertEqual(calls.call_count, 3)

    def test_plan_steps_not_submitted_or_modified(self):
        state = copy.deepcopy(self.plan)

        def fake(args):
            if args == ["info"]:
                return {"environment": "test"}
            if "update" in args:
                request = json.loads(Path(args[args.index("--file") + 1]).read_text())
                self.assertNotIn("jobPlanSteps", request)
                self.assertNotIn("id", request)
                state.update(request)
                return state
            return copy.deepcopy(state)

        with patch.object(admin, "call", side_effect=fake):
            report = admin.patch_definition("plan", "plan-id", {"cron": "*/30 * * * *"}, "test", True)
        self.assertTrue(report["applied"])
        self.assertEqual(state["jobPlanSteps"], self.plan["jobPlanSteps"])
        self.assertEqual(state["runType"], 2)

    def test_failed_update_cleanup_and_no_retry(self):
        submitted = []

        def fake(args):
            if args == ["info"]:
                return {"environment": "test"}
            if "update" in args:
                submitted.append(Path(args[args.index("--file") + 1]))
                raise admin.ContractError("ambiguous write; inspect first")
            return self.job

        with patch.object(admin, "call", side_effect=fake), self.assertRaises(admin.ContractError):
            admin.patch_definition("job", "sync-example", {"description": "after"}, "test", True)
        self.assertEqual(len(submitted), 1)
        self.assertFalse(submitted[0].exists())

    def test_readback_change_is_failure(self):
        responses = [{"environment": "test"}, self.job, {"environment": "test"}, self.job, {}, self.job]
        with patch.object(admin, "call", side_effect=responses):
            with self.assertRaisesRegex(admin.ContractError, "Readback"):
                admin.patch_definition("job", "sync-example", {"description": "after"}, "test", True)

    def test_noop_does_not_write(self):
        with patch.object(admin, "call", side_effect=[{"environment": "test"}, self.job]) as calls:
            report = admin.patch_definition("job", "sync-example", {"description": "before"}, "test", True)
        self.assertEqual(report["changedFields"], [])
        self.assertEqual(calls.call_count, 2)

    def test_unknown_fields_and_plan_rename_rejected(self):
        with self.assertRaises(admin.ContractError):
            admin.patch_definition("plan", "plan-id", {"jobPlanSteps": []}, "test", True)
        with patch.object(admin, "call", side_effect=[{"environment": "test"}, self.plan]):
            with self.assertRaisesRegex(admin.ContractError, "rename"):
                admin.patch_definition("plan", "plan-id", {"name": "another"}, "test", True)

    def test_raw_cli_errors_not_echoed(self):
        response = subprocess.CompletedProcess([], 1, '{"status":"fail","msg":"password=secret"}', "token=private")
        with patch.object(admin.subprocess, "run", return_value=response):
            with self.assertRaises(admin.ContractError) as raised:
                admin.call(["info"])
        self.assertNotIn("secret", str(raised.exception))
        self.assertNotIn("private", str(raised.exception))

    def test_timeout_has_no_automatic_retry(self):
        with patch.object(admin.subprocess, "run", side_effect=subprocess.TimeoutExpired("bccc", 45)) as run:
            with self.assertRaisesRegex(admin.ContractError, "re-read"):
                admin.call(["datahub", "job", "update", "sync-example"])
        self.assertEqual(run.call_count, 1)

    def test_plan_steps_changed_after_update_are_detected(self):
        after = {**self.plan, "cron": "*/30 * * * *", "jobPlanSteps": []}
        responses = [{"environment": "test"}, self.plan, {"environment": "test"}, self.plan, {}, after]
        with patch.object(admin, "call", side_effect=responses):
            with self.assertRaisesRegex(admin.ContractError, "Steps"):
                admin.patch_definition("plan", "plan-id", {"cron": "*/30 * * * *"}, "test", True)


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.document = {"jobId": "9223372036854775807", "jobStatus": "RUNNING",
                         "metrics": {"SourceReceivedCount": 12, "SinkWriteCount": 12},
                         "errorMsg": None}

    def test_failed_row_never_in_summary(self):
        document = {**self.document, "jobStatus": "FAILED",
                    "errorMsg": 'Value length is beyond the capacity. capacity=65533 Row: {"password":"secret","content":"private"}'}
        summary = monitor.summary(document)
        self.assertIn("column_capacity", summary["errorCategories"])
        self.assertEqual(summary["reportedCapacities"], [65533])
        self.assertNotIn("secret", json.dumps(summary))
        self.assertNotIn("private", json.dumps(summary))

    def test_duration_zero_reads_once_and_preserves_int64(self):
        output = []
        with patch.object(monitor, "call", side_effect=[{"environment": "test"}, {"environment": "test"}, self.document]) as calls:
            code = monitor.monitor("test", self.document["jobId"], 30, 0, output.append)
        self.assertEqual(code, 0)
        self.assertEqual(calls.call_count, 3)
        self.assertEqual(json.loads(output[0])["jobId"], self.document["jobId"])

    def test_failure_exits_immediately(self):
        document = {**self.document, "jobStatus": "FAILED", "errorMsg": "unknown private details"}
        output = []
        with patch.object(monitor, "call", side_effect=[{"environment": "test"}, {"environment": "test"}, document]), patch.object(monitor.time, "sleep") as sleeping:
            code = monitor.monitor("test", document["jobId"], 30, 300, output.append)
        self.assertEqual(code, 2)
        sleeping.assert_not_called()

    def test_bounded_monitor_does_not_sleep_past_next_interval(self):
        output = []
        responses = [{"environment": "test"}, {"environment": "test"}, self.document,
                     {"environment": "test"}, self.document]
        with patch.object(monitor, "call", side_effect=responses), patch.object(monitor.time, "monotonic", side_effect=[0, 1, 1, 31, 31]), patch.object(monitor.time, "sleep") as sleeping:
            code = monitor.monitor("test", self.document["jobId"], 30, 35, output.append)
        self.assertEqual(code, 0)
        self.assertEqual(len(output), 2)
        sleeping.assert_called_once_with(30)

    def test_mismatched_runtime_id_rejected(self):
        document = {**self.document, "jobId": "123"}
        with patch.object(monitor, "call", side_effect=[{"environment": "test"}, {"environment": "test"}, document]):
            with self.assertRaises(monitor.MonitorError):
                monitor.monitor("test", self.document["jobId"], 30, 0)

    def test_invalid_limits_rejected_before_any_calls(self):
        for identity, interval, duration in [("1", 0, 5), ("1", 30, 901), ("9223372036854775808", 30, 0), ("abc", 30, 0)]:
            with patch.object(monitor, "call") as calls, self.assertRaises(monitor.MonitorError):
                monitor.monitor("test", identity, interval, duration)
            calls.assert_not_called()

    def test_environment_mismatch_prevents_status_read(self):
        with patch.object(monitor, "call", return_value={"environment": "other"}) as calls:
            with self.assertRaises(monitor.MonitorError):
                monitor.monitor("test", self.document["jobId"], 30, 0)
        self.assertEqual(calls.call_count, 1)


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        fixture = ROOT / "tests/fixtures/fake_bccc.py"
        (self.directory / "bccc").symlink_to(fixture)
        self.state = self.directory / "state.json"
        self.state.write_text(json.dumps({
            "environment": "offline-test",
            "job": {"id": "offline-job", "name": "Offline", "description": "before",
                    "jobType": 0, "jobParameters": [],
                    "jobConfig": '{"password":"not-real-private-value"}'},
            "runtime": {"jobId": "123", "jobStatus": "FAILED", "metrics": {},
                        "errorMsg": 'Value length is beyond the capacity. capacity=65533 Row: {"content":"never-print-this"}'},
            "writes": 0,
        }))
        self.environment = {**os.environ, "PATH": str(self.directory) + os.pathsep + os.environ.get("PATH", ""),
                            "OCTOPARSE_SKILL_TEST_STATE": str(self.state)}
        self.patch_file = self.directory / "patch.json"
        self.patch_file.write_text('{"description":"after"}')

    def command(self, script, arguments):
        import sys
        return subprocess.run([sys.executable, str(script), *arguments], env=self.environment,
                              capture_output=True, text=True, timeout=15)

    def test_preview_and_apply_via_actual_entrypoint(self):
        arguments = ["--kind", "job", "--id", "offline-job", "--environment", "offline-test",
                     "--patch", str(self.patch_file)]
        script = ROOT / "octoparse-datahub-job-admin/scripts/patch_datahub.py"
        preview = self.command(script, arguments)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertFalse(json.loads(preview.stdout)["applied"])
        self.assertEqual(json.loads(self.state.read_text())["writes"], 0)
        applied = self.command(script, [*arguments, "--apply"])
        self.assertEqual(applied.returncode, 0, applied.stderr)
        current = json.loads(self.state.read_text())
        self.assertEqual(current["writes"], 1)
        self.assertEqual(current["job"]["description"], "after")
        self.assertEqual(current["job"]["jobConfig"], '{"password":"not-real-private-value"}')
        self.assertNotIn("not-real-private-value", applied.stdout + applied.stderr)

    def test_monitor_failure_is_redacted_via_actual_entrypoint(self):
        result = self.command(ROOT / "octoparse-cdc-verify-repair/scripts/monitor_cdc.py",
                              ["--environment", "offline-test", "--runtime-id", "123", "--duration", "0"])
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)["reportedCapacities"], [65533])
        self.assertNotIn("never-print-this", result.stdout + result.stderr)
        self.assertEqual(json.loads(self.state.read_text())["writes"], 0)


class CollectionTests(unittest.TestCase):
    def test_template_is_bounded_and_omits_empty_server_id(self):
        template = json.loads((ROOT / "octoparse-datahub-job-admin/assets/mysql-starrocks.template.json").read_text())
        source = template["source"][0]
        sink = template["sink"][0]
        self.assertNotIn("server-id", source)
        self.assertEqual(source["startup.mode"], "initial")
        self.assertGreater(template["env"]["read_limit.bytes_per_second"], 0)
        self.assertGreater(sink["batch_max_bytes"], 0)
        self.assertEqual(sink["schema_save_mode"], "ERROR_WHEN_SCHEMA_NOT_EXIST")
        self.assertTrue(sink["enable_upsert_delete"])
        self.assertEqual(sink["starrocks.config"]["max_filter_ratio"], "0")

    def test_local_document_links_resolve(self):
        for path in ROOT.rglob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue((path.parent / target.split("#")[0]).exists(), (path, target))

    def test_each_skill_has_interface_and_correct_prompt(self):
        skills = sorted(path.parent for path in ROOT.glob("*/SKILL.md"))
        self.assertEqual(len(skills), 5)
        for skill in skills:
            content = (skill / "SKILL.md").read_text()
            self.assertIn(f"name: {skill.name}\n", content)
            ui = (skill / "agents/openai.yaml").read_text()
            self.assertIn(f"${skill.name}", ui)
            short = re.search(r'short_description: "([^"]+)"', ui).group(1)
            self.assertTrue(25 <= len(short) <= 64, short)


if __name__ == "__main__":
    unittest.main()
