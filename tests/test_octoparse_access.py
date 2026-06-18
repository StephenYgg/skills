import base64
import importlib.util
import json
import tempfile
import time
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "octoparse-access"
    / "scripts"
    / "octoparse_access.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("octoparse_access", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def jwt_with_claims(claims):
    payload = json.dumps(claims, separators=(",", ":")).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    return f"header.{encoded}.signature"


class OctoparseAccessTests(unittest.TestCase):
    def test_extracts_octoparse_identity_claim_uris(self):
        module = load_module()

        token = jwt_with_claims(
            {
                "sub": "2ef31bbe-bdf5-472a-b7d8-9246ec1898f0",
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier": "legacy-id",
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name": "Stephen000",
                "preferred_username": "PreferredName",
                "unique_name": "UniqueName",
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress": "schema@example.com",
                "email": "email@example.com",
            }
        )

        user = module.user_from_token(
            "op-pre",
            "fallback@example.com",
            {
                "access_token": token,
                "refresh_token": "refresh",
                "expires_in": 60,
            },
            make_default=False,
            now_fn=lambda: 1000,
        )

        self.assertEqual(user["userId"], "2ef31bbe-bdf5-472a-b7d8-9246ec1898f0")
        self.assertEqual(user["userName"], "Stephen000")
        self.assertEqual(user["email"], "schema@example.com")
        self.assertNotIn("phone", user)

    def test_login_success_saves_user_without_password_and_sets_default(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            access_home = Path(tmp)
            token = jwt_with_claims(
                {
                    "sub": "user-1",
                    "name": "Stephen",
                    "email": "stephen@example.com",
                    "phone_number": "123456",
                }
            )

            def post(url, data, headers):
                self.assertEqual(
                    url, "https://pre-identity.bazhuayu.com/connect/token"
                )
                self.assertEqual(data["grant_type"], "password")
                self.assertEqual(data["client_id"], "Octopus")
                self.assertEqual(headers["User-Agent"], "electron")
                return {
                    "access_token": token,
                    "refresh_token": "refresh-1",
                    "expires_in": 3600,
                }

            user = module.login(
                "bzy-pre",
                "stephen@example.com",
                "secret",
                make_default=True,
                access_home=access_home,
                http_post=post,
                now_ms=lambda: 1000,
            )

            self.assertEqual(user["userId"], "user-1")
            self.assertTrue(user["env_default_account"])
            saved = json.loads((access_home / "access.json").read_text())
            self.assertNotIn("password", saved["users"][0])
            self.assertEqual(saved["users"][0]["access_token_expired"], 3601000)

    def test_setting_default_account_clears_previous_default_in_same_env(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            access_home = Path(tmp)
            access_home.mkdir(exist_ok=True)
            (access_home / "access.json").write_text(
                json.dumps(
                    {
                        "users": [
                            {
                                "env": "bzy-pre",
                                "userId": "old",
                                "userName": "Old",
                                "email": "old@example.com",
                                "access_token": "old-token",
                                "refresh_token": "old-refresh",
                                "access_token_expired": 999999,
                                "env_default_account": True,
                            }
                        ]
                    }
                )
            )

            def post(url, data, headers):
                return {
                    "access_token": jwt_with_claims(
                        {"sub": "new", "email": "new@example.com", "name": "New"}
                    ),
                    "refresh_token": "new-refresh",
                    "expires_in": 60,
                }

            module.login(
                "bzy-pre",
                "new@example.com",
                "secret",
                make_default=True,
                access_home=access_home,
                http_post=post,
                now_ms=lambda: 1000,
            )

            users = json.loads((access_home / "access.json").read_text())["users"]
            defaults = [user for user in users if user["env_default_account"]]
            self.assertEqual([user["email"] for user in defaults], ["new@example.com"])

    def test_get_returns_valid_default_token_without_refreshing(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            access_home = Path(tmp)
            access_home.mkdir(exist_ok=True)
            (access_home / "access.json").write_text(
                json.dumps(
                    {
                        "users": [
                            {
                                "env": "op-prod",
                                "userId": "u1",
                                "userName": "User",
                                "email": "user@example.com",
                                "access_token": "valid-token",
                                "refresh_token": "refresh-token",
                                "access_token_expired": 5000,
                                "env_default_account": True,
                            }
                        ]
                    }
                )
            )

            def post(url, data, headers):
                raise AssertionError("refresh should not be called")

            token = module.get_token(
                "op-prod", access_home=access_home, http_post=post, now_ms=lambda: 1000
            )

            self.assertEqual(token, "valid-token")

    def test_get_refreshes_expired_token_and_persists_new_values(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            access_home = Path(tmp)
            access_home.mkdir(exist_ok=True)
            (access_home / "access.json").write_text(
                json.dumps(
                    {
                        "users": [
                            {
                                "env": "op-pre",
                                "userId": "u1",
                                "userName": "User",
                                "email": "user@example.com",
                                "access_token": "expired-token",
                                "refresh_token": "old-refresh",
                                "access_token_expired": 1000,
                                "env_default_account": True,
                            }
                        ]
                    }
                )
            )

            def post(url, data, headers):
                self.assertEqual(url, "https://pre-identity.octoparse.com/connect/token")
                self.assertEqual(data["grant_type"], "refresh_token")
                self.assertEqual(data["refresh_token"], "old-refresh")
                return {
                    "access_token": "new-token",
                    "refresh_token": "new-refresh",
                    "expires_in": 10,
                }

            token = module.get_token(
                "op-pre", access_home=access_home, http_post=post, now_ms=lambda: 2000
            )

            self.assertEqual(token, "new-token")
            saved_user = json.loads((access_home / "access.json").read_text())["users"][
                0
            ]
            self.assertEqual(saved_user["refresh_token"], "new-refresh")
            self.assertEqual(saved_user["access_token_expired"], 12000)

    def test_refresh_failure_does_not_overwrite_existing_token(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            access_home = Path(tmp)
            access_home.mkdir(exist_ok=True)
            before = {
                "users": [
                    {
                        "env": "bzy-prod",
                        "userId": "u1",
                        "userName": "User",
                        "email": "user@example.com",
                        "access_token": "expired-token",
                        "refresh_token": "old-refresh",
                        "access_token_expired": 1000,
                        "env_default_account": True,
                    }
                ]
            }
            (access_home / "access.json").write_text(json.dumps(before))

            def post(url, data, headers):
                raise module.TokenRequestError("invalid_grant")

            with self.assertRaises(module.TokenRefreshError):
                module.get_token(
                    "bzy-prod",
                    access_home=access_home,
                    http_post=post,
                    now_ms=lambda: 2000,
                )

            after = json.loads((access_home / "access.json").read_text())
            self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
