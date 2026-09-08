---
name: isolate-git-merge-conflicts
description: Protect source branches during Git merge, rebase, or cherry-pick conflict handling by using a sibling `_merge` branch, returning to the source branch after resolution, and synchronizing later source commits. Use when conflicts are expected or detected, or when a committed source branch has a corresponding `_merge` branch.
---

# Isolate Git Merge Conflicts

Keep integration history and conflict state off the source branch unless the user explicitly declines isolation.

## Non-Negotiable Invariants

- Record the source branch, source HEAD, integration target and HEAD, operation type, and worktree status before changing Git state.
- Use `<source-branch>_merge` as the default isolation branch. Append a numeric suffix only when that name already exists and cannot be safely reused. Never reset, overwrite, delete, or force-push an existing branch to make the name available.
- Treat branches already ending in `_merge` or `_merge_<number>` as isolation branches; never derive `_merge_merge` from them.
- Preserve unrelated staged, unstaged, and untracked work. Do not switch branches, stash, abort an operation, or clean files when doing so could lose or mix that work.
- Resolve conflicts only on the isolation branch unless the user explicitly chooses the source branch.
- This skill never supplies commit or push authority. A resolved merge that requires a commit must remain pending until the user explicitly authorizes that commit under the effective Git rules.
- Return to the source branch only after the resolved state is durably preserved by an authorized commit or another user-approved recoverable mechanism.

## Ask Before Conflict Work

When a merge, rebase, or cherry-pick is expected to conflict, or immediately after a conflict is detected, ask:

> 检测到需要处理 Git 合并冲突。是否创建 `<source-branch>_merge` 分支处理，避免污染源分支？默认：创建。

Interpret the answer as follows:

- An explicit rejection means continue on the source branch, subject to normal safety and authorization rules.
- An explicit acceptance, `按默认`, or an equivalent answer means use the `_merge` branch.
- If the user does not answer the choice but later directs the Agent to continue handling the conflict, use the default and create the `_merge` branch.
- Mere silence is not permission for asynchronous or destructive action. Do not invent a timeout.

If the conflict already exists on the source branch, inspect the active operation and determine whether its pre-operation state is recoverable. After the user accepts isolation, abort only that merge/rebase/cherry-pick, create the isolation branch from the recorded source HEAD, and replay the operation there. Stop for direction if aborting could affect unrelated work.

## Resolve On The Isolation Branch

1. Verify the source branch is named and the worktree is safe to switch.
2. Inspect local and remote refs before creating or reusing the isolation branch. If an existing `_merge` branch has unexpected history or work, ask whether to reuse it or create a numbered variant.
3. Create the isolation branch from the recorded source HEAD, then perform the intended integration against a freshly fetched target ref.
4. Resolve conflicts by comparing the merge base, source, and target. Preserve later target changes while retaining the source branch's intended behavior.
5. Check for unmerged paths and conflict markers, review the result relative to the integration target, and run verification proportional to the affected code.
6. Perform the required concurrency/resource review for production code and the code-quality gates before any authorized commit or push.
7. If commit authority is absent, leave the resolved merge pending and explain that switching back would lose or strand the resolution. Ask for explicit commit authorization.
8. After the resolution is committed, switch back to the recorded source branch and verify its HEAD and worktree were not changed by the integration.

## Synchronize Later Source Commits

After an authorized commit is created on a source branch, look for the corresponding local or remote `<source-branch>_merge` branch. If one exists and does not yet contain the new source commit, ask:

> 检测到 `<source-branch>_merge`。是否把源分支的新提交 `<sha>` 同步进去？默认：同步。若同步需要创建 merge commit，我会在获得明确 commit 授权后执行。

- An explicit rejection leaves the isolation branch unchanged.
- An explicit acceptance chooses synchronization. Merge the source branch into the isolation branch; do not cherry-pick by default because the branch relationship should remain visible.
- `按默认` selects synchronization, but it does not override a rule requiring explicit commit authorization. If a merge commit is needed, ask for that authorization before creating it.
- Resolve any new conflict on the isolation branch, rerun relevant verification and Git gates, then return to the source branch after the synchronized state is durably preserved.
- Push the isolation branch only when push is explicitly authorized.

Always report the source branch, isolation branch, integrated target, resulting commits, verification, current branch, and whether synchronization or push remains pending.
