import anchorpoint
import apsync
import os
import re

SETTINGS_NAME    = "ProjectLinks"
DEFAULT_GDD_BASE = "https://gdds.playngo.com"
DEFAULT_LABEL    = "GDD"

YAML_PATH = os.path.join(os.path.dirname(__file__), "gdd_link.yaml")


def _read_yaml_name() -> str:
    try:
        with open(YAML_PATH, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r'\s+name:\s+"?([^"\n]+)"?\s*$', line)
                if m:
                    return m.group(1).strip()
    except OSError:
        pass
    return DEFAULT_LABEL


def _write_yaml_name(name: str):
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'(  name:\s+)"?[^"\n]+"?',
        f'\\1"{name}"',
        content,
        count=1,
    )
    with open(YAML_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


if __name__ == "__main__":
    ctx = anchorpoint.get_context()

    ss           = apsync.SharedSettings(ctx.workspace_id, SETTINGS_NAME)
    current_name = _read_yaml_name()
    gdd_base_url = ss.get("gdd_base_url", DEFAULT_GDD_BASE)

    def save(dialog):
        name    = (dialog.get_value("gdd_label")    or "").strip() or DEFAULT_LABEL
        base    = (dialog.get_value("gdd_base_url") or "").strip().rstrip("/")
        if not base:
            base = DEFAULT_GDD_BASE

        _write_yaml_name(name)

        s = apsync.SharedSettings(ctx.workspace_id, SETTINGS_NAME)
        s.set("gdd_base_url", base)
        s.store()

        anchorpoint.UI().show_success(
            "Settings Saved",
            f"Sidebar button renamed to \"{name}\".\n"
            "Restart Anchorpoint for the name change to appear.",
        )
        dialog.close()

    dialog = anchorpoint.Dialog()
    dialog.title = "Project Links: Settings"
    dialog.icon  = ":/icons/settings.svg"

    # ── GDD button ────────────────────────────────────────────────────────────
    dialog.start_section("GDD Link", foldable=False, folded=False)

    dialog.add_text("Sidebar button label:")
    dialog.add_info(
        "The name shown on the sidebar button. "
        "Saved directly into <b>gdd_link.yaml</b> — "
        "restart Anchorpoint after saving for the change to take effect."
    )
    dialog.add_input(current_name, placeholder=DEFAULT_LABEL, var="gdd_label", width=200)

    dialog.add_empty()
    dialog.add_text("GDD server base URL:")
    dialog.add_info(
        "Base URL of the GDD server. Change this only if the server address changes."
    )
    dialog.add_input(gdd_base_url, placeholder=DEFAULT_GDD_BASE,
                     var="gdd_base_url", width=340)

    dialog.end_section()

    dialog.add_empty()
    dialog.add_button("Save",   callback=save,                primary=True)
    dialog.add_button("Cancel", callback=lambda d: d.close(), primary=False)

    dialog.show()
