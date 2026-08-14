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

def _resolve_git():
    """Return (git_exe, env) usable inside Anchorpoint's action runtime.

    Anchorpoint's Python process does not necessarily have git on PATH, so a
    bare "git" call dies with [WinError 2]. Prefer Anchorpoint's bundled git
    plus the official vc environment (credential manager, GIT_EXEC_PATH);
    fall back to whatever git a PATH lookup finds.
    """
    import os
    import sys
    import shutil

    env = os.environ.copy()

    try:
        actions_dir = os.path.join(
            ap.get_application_dir(), "scripts", "git", "versioncontrol", "actions"
        )
        if os.path.isdir(actions_dir) and actions_dir not in sys.path:
            sys.path.insert(0, actions_dir)

        from vc.apgit_utility import install_git
        from vc.apgit.repository import GitRepository

        git_exe = install_git.get_git_cmd_path()
        if os.path.exists(git_exe):
            env.update(GitRepository.get_git_environment())
            # git-lfs spawns git itself, so its folder must be on PATH too
            env["PATH"] = os.path.dirname(git_exe) + os.pathsep + env.get("PATH", "")
            return git_exe, env
    except Exception as e:
        print(f"[GIT LFS Push] vc helpers unavailable, falling back to PATH git: {e}")

    git_exe = shutil.which("git")
    if not git_exe:
        raise RuntimeError(
            "Git executable not found: neither Anchorpoint's bundled git nor "
            "a system git on PATH is available."
        )
    env["PATH"] = os.path.dirname(git_exe) + os.pathsep + env.get("PATH", "")
    return git_exe, env


def _parse_uploaded_files(progress_file: str) -> list:
    """Collect distinct file names actually uploaded, from the GIT_LFS_PROGRESS log.

    git-lfs writes one line per transfer update in the documented format
    "<direction> <current>/<total> <bytes>/<total_bytes> <name>", and only
    objects that are really transferred show up — objects origin already has
    never appear. Names may contain spaces, hence maxsplit.
    """
    uploaded = []
    seen = set()
    try:
        with open(progress_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                parts = line.rstrip("\n").split(" ", 3)
                if len(parts) < 4 or parts[0] != "upload":
                    continue
                name = parts[3].strip()
                if name and name not in seen:
                    seen.add(name)
                    uploaded.append(name)
    except OSError:
        pass
    return uploaded


def _run_lfs_push(project_path: str):
    import os
    import re
    import subprocess
    import sys
    import tempfile

    ui = ap.UI()
    progress = ap.Progress(
        "GIT LFS Push",
        "Pushing LFS objects to origin...",
        infinite=True,
        cancelable=False,
        show_loading_screen=True,
    )
    lfs_progress_path = None
    try:
        git_exe, env = _resolve_git()

        # Machine-readable transfer log: this is how we tell re-uploaded
        # objects apart from ones origin already had.
        fd, lfs_progress_path = tempfile.mkstemp(prefix="ap_lfs_push_", suffix=".log")
        os.close(fd)
        env["GIT_LFS_PROGRESS"] = lfs_progress_path

        kwargs = dict(
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=env,
        )
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            [git_exe, "-C", project_path, "lfs", "push", "origin", "--all"],
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

        uploaded = _parse_uploaded_files(lfs_progress_path)

        # Fallback for --all pushes of historical objects that no longer map
        # to a file name: take the count from git's own upload meter.
        meter_total = 0
        for m in re.finditer(
            r"Uploading LFS objects:\s+\d+%\s+\((\d+)/(\d+)\)", stdout + "\n" + stderr
        ):
            meter_total = max(meter_total, int(m.group(2)))
        upload_count = max(len(uploaded), meter_total)

        progress.finish()
        if upload_count == 0:
            ui.show_info(
                "LFS Push - no changes",
                "All LFS objects were already present on origin.",
            )
        elif uploaded:
            print(f"[GIT LFS Push] re-uploaded {len(uploaded)} file(s): {', '.join(uploaded)}")
            shown = "\n".join(uploaded[:10])
            if len(uploaded) > 10:
                shown += f"\n... and {len(uploaded) - 10} more (see console log)"
            ui.show_success(f"LFS Push complete - {len(uploaded)} file(s) uploaded", shown)
        else:
            ui.show_success(
                "LFS Push complete",
                f"{upload_count} LFS object(s) uploaded to origin.",
            )
    except Exception as e:
        progress.finish()
        ui.show_error("LFS Push failed", str(e))
        raise
    finally:
        if lfs_progress_path:
            try:
                os.remove(lfs_progress_path)
            except OSError:
                pass


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ctx = ap.get_context()
    ui  = ap.UI()

    if not ctx.project_path:
        ui.show_error("No project", "Open an Anchorpoint project and try again.")
        exit()

    print(f"[GIT LFS Push] project_path={ctx.project_path}")
    ctx.run_async(_run_lfs_push, ctx.project_path)
