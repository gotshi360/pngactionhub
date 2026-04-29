import anchorpoint as ap
import apsync as aps

SETTINGS_NAME = "GitRepo"


# ── Visibility hook ───────────────────────────────────────────────────────────

def _is_enabled_for_role(ctx) -> bool:
    try:
        shared = aps.SharedSettings(ctx.workspace_id, SETTINGS_NAME)
        role_owner  = shared.get("lfs_role_owner",  True)
        role_admin  = shared.get("lfs_role_admin",  True)
        role_member = shared.get("lfs_role_member", True)

        access = aps.get_workspace_access(ctx.workspace_id)
        access_str = str(access).lower()

        if "owner" in access_str:
            return bool(role_owner)
        if "admin" in access_str:
            return bool(role_admin)
        return bool(role_member)
    except Exception as e:
        print(f"[GIT LFS Push] on_is_action_enabled role check failed: {e}")
        return True


def on_is_action_enabled(path, type, ctx):
    try:
        shared = aps.SharedSettings(ctx.workspace_id, SETTINGS_NAME)
        if not shared.get("show_lfs_push", True):
            return False
        return _is_enabled_for_role(ctx)
    except Exception as e:
        print(f"[GIT LFS Push] on_is_action_enabled failed: {e}")
        return True


# ── Async task ────────────────────────────────────────────────────────────────

def _run_lfs_push(project_path: str):
    import subprocess
    import sys

    ui = ap.UI()
    progress = ap.Progress(
        "GIT LFS Push",
        "Pushing LFS objects to origin...",
        infinite=True,
        cancelable=False,
        show_loading_screen=True,
    )
    try:
        kwargs = dict(capture_output=True, text=True, check=False)
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            ["git", "-C", project_path, "lfs", "push", "origin", "--all"],
            **kwargs,
        )
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if stdout:
            print(f"[GIT LFS Push] {stdout}")
        if stderr:
            print(f"[GIT LFS Push] {stderr}")
        if result.returncode != 0:
            raise RuntimeError(stderr or stdout or "git lfs push failed")

        progress.finish()
        ui.show_success("LFS Push complete", "All LFS objects have been pushed to origin.")
    except Exception as e:
        progress.finish()
        ui.show_error("LFS Push failed", str(e))
        raise


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ctx = ap.get_context()
    ui  = ap.UI()

    if not ctx.project_path:
        ui.show_error("No project", "Open an Anchorpoint project and try again.")
        exit()

    print(f"[GIT LFS Push] project_path={ctx.project_path}")
    ctx.run_async(_run_lfs_push, ctx.project_path)
