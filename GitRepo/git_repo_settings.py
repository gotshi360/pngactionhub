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
_VISIBILITY_KEYS = ("show_repo_settings", "rs_role_owner", "rs_role_admin", "rs_role_member")

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
            return bool(visibility.get("rs_role_owner", True))
        if "admin" in access_str:
            return bool(visibility.get("rs_role_admin", True))
        return bool(visibility.get("rs_role_member", True))
    except Exception as e:
        print(f"[Git Repo Settings] on_is_action_enabled role check failed: {e}")
        return True


def on_is_action_enabled(path, type, ctx):
    try:
        visibility = _get_visibility(ctx.workspace_id)
        if not visibility.get("show_repo_settings", True):
            return False
        return _is_enabled_for_role(ctx, visibility)
    except Exception as e:
        print(f"[Git Repo Settings] on_is_action_enabled failed: {e}")
        return True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_owner_repo(remote_url: str) -> tuple[str, str]:
    from urllib.parse import urlparse
    u = urlparse(remote_url)
    path = (u.path or "").lstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"Cannot parse owner/repo from remote: {remote_url}")
    return parts[0], parts[1]


def _open_edit_dialog(base_url: str, token: str, owner: str, repo: str, current: dict):
    ui = ap.UI()
    ctx = ap.get_context()

    is_private   = bool(current.get("private", False))
    current_desc = current.get("description") or ""
    html_url     = current.get("html_url") or ""

    dialog = ap.Dialog()
    dialog.title = "Git Repo Settings"

    info_lines = [f"<b>Repository:</b> {owner}/{repo}"]
    if html_url:
        info_lines.append(f"<b>Web:</b> {html_url}")
    dialog.add_info("<br>".join(info_lines))

    dialog.start_section("Settings", folded=False)

    dialog.add_text("Visibility:")
    dialog.add_dropdown(
        "Private" if is_private else "Public",
        ["Public", "Private"],
        var="visibility",
    )

    dialog.add_text("Description:")
    dialog.add_input(
        current_desc,
        placeholder="Repository description",
        var="description",
        width=520,
    )

    dialog.end_section()
    dialog.add_empty()

    def on_apply(d):
        visibility  = d.get_value("visibility") or "Private"
        new_private = visibility == "Private"
        new_desc    = (d.get_value("description") or "").strip()

        def save_task(_base_url, _token, _owner, _repo, _private, _desc):
            import requests
            progress = ap.Progress("Git Repo Settings", "Saving repository settings...", show_loading_screen=True)
            try:
                url     = f"{_base_url.rstrip('/')}/api/v1/repos/{_owner}/{_repo}"
                headers = {"Authorization": f"token {_token}", "Accept": "application/json"}
                payload = {"private": _private, "description": _desc}
                r = requests.patch(url, headers=headers, json=payload, timeout=20)
                if r.status_code >= 400:
                    raise RuntimeError(f"PATCH failed ({r.status_code}): {r.text}")
                return True
            finally:
                progress.finish()

        try:
            result = ctx.run_async(save_task, base_url, token, owner, repo, new_private, new_desc)
            if result is None:
                result = True
            ui.show_success("Updated", f"{owner}/{repo} saved (visibility: {visibility}).")
            d.close()
        except Exception as e:
            ui.show_error("Update failed", str(e))

    dialog.add_button("Apply",  callback=on_apply,              primary=True)
    dialog.add_button("Cancel", callback=lambda d: d.close(),   primary=False)
    dialog.show()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ui  = ap.UI()
    ctx = ap.get_context()

    if not ctx.project_id:
        ui.show_error("No project context", "Open an Anchorpoint project and try again.")
        exit()

    settings = aps.Settings(SETTINGS_NAME)
    base_url = (settings.get("base_url", "") or "").strip()
    token    = (settings.get("token",    "") or "").strip()

    if not base_url or not token:
        ui.show_error(
            "Not configured",
            "Base URL / Token is missing.\n\nOpen Action Settings for 'Git Repo Settings' and set them first.",
        )
        exit()

    def load_task(project_path: str, _base_url: str, _token: str):
        import subprocess
        import sys
        import requests

        progress = ap.Progress("Git Repo Settings", "Loading repository settings...", show_loading_screen=True)
        try:
            kwargs = dict(capture_output=True, text=True, check=False)
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                ["git", "-C", project_path, "remote", "get-url", "origin"],
                **kwargs,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "Git command failed")
            remote_url = (result.stdout or "").strip()

            owner, repo = _parse_owner_repo(remote_url)

            url     = f"{_base_url.rstrip('/')}/api/v1/repos/{owner}/{repo}"
            headers = {"Authorization": f"token {_token}", "Accept": "application/json"}
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code >= 400:
                raise RuntimeError(f"GET failed ({r.status_code}): {r.text}")
            current = r.json()
            return {"remote_url": remote_url, "owner": owner, "repo": repo, "current": current}
        finally:
            progress.finish()

    try:
        data = ctx.run_async(load_task, ctx.project_path, base_url, token)
    except Exception as e:
        ui.show_error(
            "Cannot load repo",
            f"{e}\n\nThis usually means the token is invalid or has no permissions.",
        )
        exit()

    if data is None:
        try:
            data = load_task(ctx.project_path, base_url, token)
        except Exception as e:
            ui.show_error("Cannot load repo", str(e))
            exit()

    if not isinstance(data, dict) or not isinstance(data.get("current"), dict):
        ui.show_error("Cannot load repo", f"Unexpected response: {data}")
        exit()

    print(f"[Git Repo Settings] origin={data.get('remote_url')}")
    print(f"[Git Repo Settings] owner/repo={data.get('owner')}/{data.get('repo')}")

    _open_edit_dialog(base_url, token, data["owner"], data["repo"], data["current"])
