import anchorpoint as ap
import apsync as aps
import time

SETTINGS_NAME = "GitRepo"


# ── Visibility hook ───────────────────────────────────────────────────────────
#
# on_is_action_enabled runs every time a folder context menu is opened. The
# previous version built a cloud-backed SharedSettings object twice per call
# (once for the show switch, once for the role switches) and looked up the
# workspace access level on every right click. All of it is now read once and
# cached per workspace for a short window.

_VISIBILITY_CACHE_TTL = 30.0
_VISIBILITY_KEYS = ("show_lfs_push", "lfs_role_owner", "lfs_role_admin", "lfs_role_member")

_visibility_cache = {}  # workspace_id -> (timestamp, {key: value})
_access_cache = {}      # workspace_id -> (timestamp, access_str)


def _get_visibility(workspace_id) -> dict:
    now = time.monotonic()
    cached = _visibility_cache.get(workspace_id)
    if cached and (now - cached[0]) < _VISIBILITY_CACHE_TTL:
        return cached[1]

    shared = aps.SharedSettings(workspace_id, SETTINGS_NAME)
    values = {key: shared.get(key, True) for key in _VISIBILITY_KEYS}
    _visibility_cache[workspace_id] = (now, values)
    return values


def _get_access_str(workspace_id) -> str:
    now = time.monotonic()
    cached = _access_cache.get(workspace_id)
    if cached and (now - cached[0]) < _VISIBILITY_CACHE_TTL:
        return cached[1]

    access_str = str(aps.get_workspace_access(workspace_id)).lower()
    _access_cache[workspace_id] = (now, access_str)
    return access_str


def _is_enabled_for_role(ctx, visibility: dict) -> bool:
    try:
        access_str = _get_access_str(ctx.workspace_id)

        if "owner" in access_str:
            return bool(visibility.get("lfs_role_owner", True))
        if "admin" in access_str:
            return bool(visibility.get("lfs_role_admin", True))
        return bool(visibility.get("lfs_role_member", True))
    except Exception as e:
        print(f"[GIT LFS Push] on_is_action_enabled role check failed: {e}")
        return True


def on_is_action_enabled(path, type, ctx):
    try:
        visibility = _get_visibility(ctx.workspace_id)
        if not visibility.get("show_lfs_push", True):
            return False
        return _is_enabled_for_role(ctx, visibility)
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
