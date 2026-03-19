# spine_export_08.py
# Change vs _07: support selecting folders — scans for .spine files and batch-exports with default settings.
# Change vs _07b: collect all selected folders from every available context attribute; ignore folders without .spine files.

import os, re, json, shlex, platform, subprocess, tempfile, time, shutil
from typing import Optional, Tuple, Dict, List, Callable

import anchorpoint as ap
import apsync as aps

def dprint(msg: str):
    print(f"[Spine Export] {msg}", flush=True)

ctx = ap.get_context()
ui = ap.UI()
settings = aps.Settings("spine_export")

DEFAULT_SPINE_WIN = "C:/Program Files/Spine/Spine.com"
DEFAULT_SPINE_MAC = "/Applications/Spine.app/Contents/MacOS/Spine"

# Default export settings used for batch folder exports
BATCH_DEFAULTS = dict(
    fps=60.0,
    bg='black',
    single_file=True,
    video_format='mov',
    width=1920,
    height=1080,
    use_fixed_viewport=False,
    center_viewport=True,
    viewport_x=0,
    viewport_y=0,
    user_output_override='',
    chosen_skeletons=None,
)

def _subprocess_kwargs_hidden() -> dict:
    kw = dict(shell=False)
    if platform.system().lower().startswith('win'):
        CREATE_NO_WINDOW = 0x08000000
        kw['creationflags'] = CREATE_NO_WINDOW
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kw['startupinfo'] = si
    return kw

def ensure_file_exists(path: str, label: str) -> bool:
    if not path or not os.path.isfile(path):
        ui.show_error(f"{label} not found", description=str(path))
        dprint(f"Missing {label}: {path}")
        return False
    return True

def ensure_dir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        dprint(f"Could not create directory '{path}': {e}")

def looks_like_file(path: str) -> bool:
    return bool(path and os.path.splitext(path)[1])

def next_available_filename(path: str) -> str:
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while True:
        cand = f"{base}_{i}{ext}"
        if not os.path.exists(cand):
            return cand
        i += 1

def latest_file_in(dir_path: str, exts: Optional[List[str]] = None) -> Optional[str]:
    try:
        latest, latest_t = None, -1
        for name in os.listdir(dir_path):
            if exts and not any(name.lower().endswith(e) for e in exts):
                continue
            full = os.path.join(dir_path, name)
            try:
                t = os.path.getmtime(full)
            except FileNotFoundError:
                continue
            if t > latest_t:
                latest, latest_t = full, t
        return latest
    except Exception:
        return None

def get_spine_executable() -> str:
    system = platform.system().lower()
    if system.startswith('win'):
        return settings.get('spine_path_win', DEFAULT_SPINE_WIN)
    elif system == 'darwin':
        return settings.get('spine_path_mac', DEFAULT_SPINE_MAC)
    else:
        return settings.get('spine_path_win', DEFAULT_SPINE_WIN)

def build_spine_command(spine_exec: str, project_file: str, output_target: str, export_json: str) -> List[str]:
    return [spine_exec, '-i', project_file, '-o', output_target, '-e', export_json]

def parse_bg_choice(choice: str) -> Dict[str, float]:
    choice = (choice or '').strip().lower()
    if choice == 'black':
        return {'r': 0, 'g': 0, 'b': 0, 'a': 1}
    if choice == 'white':
        return {'r': 1, 'g': 1, 'b': 1, 'a': 1}
    if choice == 'transparent':
        return {'r': 0, 'g': 0, 'b': 0, 'a': 0}
    if choice.startswith('#') and len(choice) == 7:
        try:
            r = int(choice[1:3], 16) / 255.0
            g = int(choice[3:5], 16) / 255.0
            b = int(choice[5:7], 16) / 255.0
            return {'r': r, 'g': g, 'b': b, 'a': 1}
        except Exception:
            pass
    return {'r': 0, 'g': 0, 'b': 0, 'a': 1}

def _viewport_fields(width: int, height: int, use_fixed_viewport: bool, center_viewport: bool, viewport_x: int, viewport_y: int):
    if use_fixed_viewport:
        fit_width = 0
        fit_height = 0
        pad = False
        enlarge = False
        crop_w, crop_h = int(width), int(height)
        crop_x = -int(width)//2 if center_viewport else int(viewport_x)
        crop_y = -int(height)//2 if center_viewport else int(viewport_y)
    else:
        fit_width, fit_height, pad, enlarge = int(width), int(height), True, True
        crop_x = crop_y = crop_w = crop_h = 0
    return fit_width, fit_height, pad, enlarge, crop_x, crop_y, crop_w, crop_h

def build_export_settings_json_dict(video_format: str, width: int, height: int, fps: float, background_choice: str, single_file: bool, use_fixed_viewport: bool, center_viewport: bool, viewport_x: int, viewport_y: int, skeleton_target: Optional[str]) -> dict:
    clazz = 'export-mov' if video_format.lower() == 'mov' else 'export-avi'
    output_type = 'singleFile' if single_file else 'filePerAnimation'
    bg = parse_bg_choice(background_choice)
    fit_width, fit_height, pad, enlarge, crop_x, crop_y, crop_w, crop_h = _viewport_fields(width, height, use_fixed_viewport, center_viewport, viewport_x, viewport_y)
    skeleton_type = 'single' if skeleton_target else 'all'
    settings_dict = {
        'class': clazz,
        'name': 'MOV' if clazz == 'export-mov' else 'AVI',
        'open': False,
        'exportType': 'animation',
        'skeletonType': skeleton_type,
        'animationType': 'all',
        'skinType': 'current',
        'maxBounds': False,
        'renderImages': True,
        'renderBones': False,
        'renderOthers': False,
        'linearFiltering': True,
        'scale': 100,
        'fitWidth': fit_width,
        'fitHeight': fit_height,
        'enlarge': enlarge,
        'pad': pad,
        'background': bg,
        'fps': float(fps),
        'lastFrame': False,
        'cropX': crop_x,
        'cropY': crop_y,
        'cropWidth': crop_w,
        'cropHeight': crop_h,
        'rangeStart': -1,
        'rangeEnd': -1,
        'msaa': 0,
        'outputType': output_type,
        'animationRepeat': 1,
        'animationPause': 0.0,
        'encoding': 'PNG',
        'quality': 0,
        'compression': 6,
        'audio': False
    }
    if skeleton_target:
        settings_dict['skeleton'] = skeleton_target
    return settings_dict

def build_data_export_settings_json_dict() -> dict:
    return {'class': 'export-json', 'name': 'JSON', 'open': False, 'skeletonType': 'all', 'animationType': 'all', 'skinType': 'current'}

def write_temp_export_json(settings_dict: dict) -> str:
    fd, path = tempfile.mkstemp(prefix='spine_export_', suffix='.json')
    os.close(fd)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(settings_dict, f, ensure_ascii=False, indent=2)
    dprint(f'Wrote temp export settings JSON: {path}')
    return path

def _extract_skeleton_names_from_stdout(stdout: str) -> List[str]:
    names = set()
    for line in (stdout or '').splitlines():
        m = re.search(r'skeleton:\s*([^\]\r\n]+)', line, re.IGNORECASE)
        if m:
            names.add(m.group(1).strip())
    return sorted(names)


def probe_skeletons_sync(project_file: str, spine_exec: str) -> List[str]:
    """Probe skeleton names from a .spine file synchronously. Returns [] on any failure."""
    tmp_dir = tempfile.mkdtemp(prefix='spine_anim_probe_')
    settings_path = write_temp_export_json(build_data_export_settings_json_dict())
    cmd = build_spine_command(spine_exec, project_file, tmp_dir, settings_path)
    dprint('Probe cmd: ' + ' '.join(shlex.quote(p) for p in cmd))

    out = ''
    try:
        kw = _subprocess_kwargs_hidden()
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kw)
        out = res.stdout or ''
        dprint(out.strip())
    except Exception as e:
        dprint(f'probe_skeletons_sync failed: {e}')
        return []
    finally:
        try: os.remove(settings_path)
        except Exception: pass

    json_files = [
        os.path.join(tmp_dir, n) for n in os.listdir(tmp_dir)
        if n.lower().endswith('.json') and os.path.join(tmp_dir, n) != settings_path
    ]

    skeletons: List[str] = []
    for jf in json_files:
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                data = json.load(f)
            meta = data.get('skeleton') or {}
            nm = meta.get('name')
            name = nm.strip() if isinstance(nm, str) and nm.strip() else os.path.splitext(os.path.basename(jf))[0]
            skeletons.append(name)
        except Exception as e:
            dprint(f'Failed to parse {jf}: {e}')

    if not skeletons:
        skeletons = _extract_skeleton_names_from_stdout(out)

    try:
        import shutil; shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass

    unique, seen = [], set()
    for s in skeletons:
        if s not in seen:
            seen.add(s); unique.append(s)
    return unique


def probe_skeletons_async(project_file: str, on_done: Callable[[List[str]], None]):
    progress = ap.Progress('Extracting Skeletons...', infinite=True)
    progress.set_cancelable(False)
    progress.set_text('Reading project and extracting skeleton list...')

    spine_exec = get_spine_executable()
    if not ensure_file_exists(spine_exec, 'Spine executable'):
        progress.finish(); on_done([]); return
    if not ensure_file_exists(project_file, '.spine file'):
        progress.finish(); on_done([]); return

    skeletons = probe_skeletons_sync(project_file, spine_exec)
    progress.finish()
    on_done(skeletons)

def _format_bytes_to_mb(size_bytes: int) -> float:
    try:
        return size_bytes / (1024.0 * 1024.0)
    except Exception:
        return 0.0

def _scan_for_active_sidefile(folder: str) -> Optional[str]:
    exts = ['.mov', '.avi', '.tmp', '.part', '.partial', '.mp4', '.m4v']
    try:
        names = os.listdir(folder)
    except Exception:
        names = []
    newest, newest_t = None, -1
    for n in names:
        if not any(n.lower().endswith(e) for e in exts):
            continue
        full = os.path.join(folder, n)
        try:
            t = os.path.getmtime(full)
        except Exception:
            continue
        if t > newest_t:
            newest, newest_t = full, t
    return newest

def _probe_current_output(target_path: str) -> Optional[str]:
    if not target_path: return None
    if looks_like_file(target_path):
        if os.path.isfile(target_path): return target_path
        parent = os.path.dirname(target_path) or os.getcwd()
        return _scan_for_active_sidefile(parent)
    else:
        return _scan_for_active_sidefile(target_path)

def _human_rate(delta_mb: float, dt: float) -> str:
    if dt <= 0: return '0 MB/s'
    rate = max(0.0, delta_mb / dt)
    return f'{rate:.2f} MB/s'


def open_path_in_os(path: str):
    try:
        if platform.system().lower().startswith('win'):
            os.startfile(path)  # type: ignore[attr-defined]
        elif platform.system().lower() == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])
    except Exception as e:
        ui.show_error("Failed to open log", description=str(e))

def show_open_log_prompt(log_path: str):
    if not log_path:
        ui.show_error("Export failed", description="No log path available.")
        return
    d = ap.Dialog()
    d.title = "Export failed"
    d.add_info("The Spine CLI reported an error.")
    d.add_text("Log file\t").add_input(log_path, var="logp", enabled=False)
    d.add_button("Open log", callback=lambda dlg: open_path_in_os(log_path))
    d.add_button("Close", callback=lambda dlg: dlg.close())
    d.show()

def run_spine_cli_with_progress(spine_exec: str, project_file: str, output_target: str, export_json: str, progress: ap.Progress, poll_secs: float = 0.5, repaint_nudge: float = None) -> Tuple[bool, str]:
    # LOG NOW GOES TO OS TEMP DIR (not project/output). Removed on success.
    temp_dir = tempfile.gettempdir()
    fd, log_path = tempfile.mkstemp(prefix='spine_cli_', suffix='.log', dir=temp_dir)
    os.close(fd)
    logf = open(log_path, 'a', encoding='utf-8')

    command = build_spine_command(spine_exec, project_file, output_target, export_json)
    dprint('CLI command: ' + ' '.join(shlex.quote(p) for p in command))
    dprint(f'Redirecting CLI output to temp log: {log_path}')

    if not ensure_file_exists(spine_exec, 'Spine executable'): return False, ''
    if not ensure_file_exists(project_file, '.spine file'): return False, ''
    if not export_json or not os.path.isfile(export_json):
        ui.show_error('Export settings (.json) missing'); return False, ''

    if looks_like_file(output_target):
        ensure_dir(os.path.dirname(output_target) or os.getcwd())
    else:
        ensure_dir(output_target)

    try:
        kw = _subprocess_kwargs_hidden()
        p = subprocess.Popen(command, stdout=logf, stderr=logf, text=True, **kw)
    except FileNotFoundError:
        logf.close(); ui.show_error('Failed to start Spine CLI', description=spine_exec); return False, ''

    last_probe_t = time.time()
    last_size_mb = -1.0
    stagnant_checks = 0
    active_path: Optional[str] = None

    try:
        while True:
            if progress.canceled:
                try: p.terminate()
                except Exception: pass
                try: p.wait(timeout=3)
                except Exception:
                    try: p.kill()
                    except Exception: pass
                ui.show_info('Canceled', 'The export has been canceled by the user.')
                return False, 'canceled'

            now = time.time()
            if now - last_probe_t >= poll_secs:
                if not active_path:
                    active_path = _probe_current_output(output_target)
                if not active_path or (active_path and not os.path.exists(active_path)):
                    folder = os.path.dirname(output_target) if looks_like_file(output_target) else output_target
                    active_path = _scan_for_active_sidefile(folder or os.getcwd())

                size_mb = None
                if active_path and os.path.exists(active_path):
                    try: size_mb = _format_bytes_to_mb(os.path.getsize(active_path))
                    except Exception: size_mb = None

                if size_mb is not None:
                    dt = now - last_probe_t
                    delta_mb = 0.0 if last_size_mb < 0 else (size_mb - last_size_mb)
                    speed_txt = _human_rate(delta_mb, dt)
                    progress.set_text(f'Size: {size_mb:.2f} MB  â¢  Write speed: {speed_txt}')
                    if repaint_nudge is not None: progress.report_progress(repaint_nudge)
                    if last_size_mb >= 0 and size_mb <= last_size_mb + 1e-6: stagnant_checks += 1
                    else: stagnant_checks = 0
                    last_size_mb = size_mb
                else:
                    progress.set_text('Size: â  â¢  Write speed: â')
                    if repaint_nudge is not None: progress.report_progress(repaint_nudge)

                if stagnant_checks >= 3:
                    folder = os.path.dirname(output_target) if looks_like_file(output_target) else output_target
                    new_cand = _scan_for_active_sidefile(folder or os.getcwd())
                    if new_cand and new_cand != active_path:
                        active_path = new_cand; stagnant_checks = 0

                last_probe_t = now

            ret = p.poll()
            if ret is not None: break
            time.sleep(0.05)

    finally:
        try:
            if p and p.poll() is None: p.wait(timeout=0.5)
        except Exception: pass
        try:
            logf.flush(); logf.close()
        except Exception: pass

    if p.returncode != 0:
        # Keep the temp log and return its path
        return False, log_path

    # Success: dprint the CLI output for diagnostics, then delete the log
    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            log_content = f.read()
        dprint('--- Spine CLI output (exit 0) ---')
        for line in log_content.splitlines():
            if line.strip():
                dprint(line.rstrip())
        dprint('--- end of CLI output ---')
    except Exception as e:
        dprint(f'Could not read CLI log: {e}')
    try:
        if os.path.exists(log_path):
            os.remove(log_path)
    except Exception:
        pass

    return True, ''

def check_missing_images_in_project(project_file: str, spine_exec: str) -> dict:
    """Run a JSON export and scan the CLI output for missing-image error lines.
    Spine reports missing images as lines containing both
    'Image for attachment' and 'not found'.

    Returns a dict with keys:
      'missing'  – list of raw error lines (one per missing image)
      'cli_out'  – full CLI output from the JSON export run
    """
    import shutil

    result = {'missing': [], 'cli_out': ''}

    tmp_dir = tempfile.mkdtemp(prefix='spine_missing_chk_')
    settings_path = write_temp_export_json(build_data_export_settings_json_dict())
    cmd = build_spine_command(spine_exec, project_file, tmp_dir, settings_path)
    dprint('Missing-image check cmd: ' + ' '.join(shlex.quote(p) for p in cmd))

    try:
        kw = _subprocess_kwargs_hidden()
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kw)
        result['cli_out'] = res.stdout or ''
        dprint(result['cli_out'].strip())
    except Exception as e:
        dprint(f'check_missing_images: CLI failed: {e}')
        result['cli_out'] = f'CLI error: {e}'
        return result
    finally:
        try: os.remove(settings_path)
        except Exception: pass

    try: shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception: pass

    # Detect lines that match Spine's missing-image format:
    # "Image for attachment [...] not found: <name>"
    missing_lines = [
        line.strip()
        for line in result['cli_out'].splitlines()
        if 'Image for attachment' in line and 'not found' in line
    ]
    result['missing'] = missing_lines

    if missing_lines:
        dprint(f'Missing images detected ({len(missing_lines)}):')
        for ln in missing_lines:
            dprint(f'  {ln}')
    else:
        dprint('No missing image lines found in CLI output')

    return result


def write_missing_images_trace(trace_path: str, project_file: str, check_result: dict):
    """Write a trace file listing every missing-image error line plus the full CLI output."""
    import datetime
    missing = check_result.get('missing', [])
    cli_out = check_result.get('cli_out', '')

    lines = [
        'Spine Missing Images Report',
        '=' * 60,
        f'Project:  {os.path.basename(project_file)}',
        f'Date:     {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        '',
        f'MISSING IMAGES ({len(missing)}):',
    ]
    for ln in missing:
        lines.append(f'  {ln}')
    if cli_out.strip():
        lines += ['', 'FULL CLI OUTPUT:']
        lines += [f'  {ln}' for ln in cli_out.strip().splitlines()]

    try:
        with open(trace_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        dprint(f'Wrote trace: {trace_path}')
    except Exception as e:
        dprint(f'Failed to write trace file: {e}')


PREVIEW_STATUS_ATTR = 'Preview Status'
# apsync.TagColor members must be used — plain strings are silently ignored.
_PREVIEW_TAGS = [
    ('Done',          aps.TagColor.green),
    ('Missing IMG',   aps.TagColor.yellow),
    ('Export Failed', aps.TagColor.red),
    ('No Anim',       aps.TagColor.blue),
]

def ensure_preview_status_attribute(api):
    """Get (or create) the 'Preview Status' single-choice-tag attribute, adding any missing tags.
    Always returns the attribute object; tag-setting failures are logged but do not raise."""
    # Step 1 – get or create
    attr = api.attributes.get_attribute(PREVIEW_STATUS_ATTR)
    if not attr:
        dprint(f"Creating attribute '{PREVIEW_STATUS_ATTR}'")
        try:
            api.attributes.create_attribute(PREVIEW_STATUS_ATTR, aps.AttributeType.single_choice_tag)
        except Exception as e:
            dprint(f"create_attribute failed: {e}")
        # Always re-fetch — the object returned by create_attribute may be uncommitted
        attr = api.attributes.get_attribute(PREVIEW_STATUS_ATTR)
        if not attr:
            dprint("ERROR: attribute still not found after creation")
            return None

    dprint(f"Attribute '{PREVIEW_STATUS_ATTR}' found (id={getattr(attr, 'id', '?')})")

    # Step 2 – ensure all required tags are present
    try:
        existing_names = {t.name for t in (attr.tags or [])}
        dprint(f"Existing tags: {existing_names}")
        needed = [(n, c) for n, c in _PREVIEW_TAGS if n not in existing_names]
        if needed:
            all_tags = list(attr.tags or []) + [aps.AttributeTag(n, c) for n, c in needed]
            dprint(f"Setting tags: {[t.name for t in all_tags]}")
            api.attributes.set_attribute_tags(attr, all_tags)
            dprint("Tags set successfully")
        else:
            dprint("All tags already present")
    except Exception as e:
        dprint(f"ERROR setting tags on '{PREVIEW_STATUS_ATTR}': {e}")

    return attr

def set_folder_preview_status(api, folder_path: str, status: str):
    try:
        # Use attribute name string — most robust form for single-choice-tag value assignment
        api.attributes.set_attribute_value(folder_path, PREVIEW_STATUS_ATTR, status)
        dprint(f"Preview Status → '{status}' on {folder_path}")
    except Exception as e:
        dprint(f"Failed to set Preview Status on '{folder_path}': {e}")


def export_worker(selected_files: List[str], width: int, height: int, fps: float, bg: str, single_file: bool, video_format: str, user_output_override: str, use_fixed_viewport: bool, center_viewport: bool, viewport_x: int, viewport_y: int, chosen_skeletons: Optional[List[str]], export_local: bool = False):
    # When chosen_skeletons is None we probe each project at runtime, so the
    # total job count is unknown upfront — use an infinite progress bar.
    auto_probe = (chosen_skeletons is None)
    progress = ap.Progress('Spine Export', infinite=auto_probe)
    progress.set_cancelable(True)

    spine_exec = get_spine_executable()
    if not ensure_file_exists(spine_exec, 'Spine executable'):
        progress.finish(); return

    # Set up attribute tracking (non-fatal if API unavailable)
    _api = None
    try:
        _api = ap.get_api()
        dprint(f'API obtained: {_api}')
        ensure_preview_status_attribute(_api)
    except Exception as e:
        dprint(f'Attribute API unavailable, status tagging disabled: {e}')
        _api = None

    try:
        total_jobs = len(selected_files) * max(1, len(chosen_skeletons)) if not auto_probe else None
        job_index = 0

        for proj in selected_files:
            proj_dir = os.path.dirname(proj)
            base_name = os.path.splitext(os.path.basename(proj))[0]
            ext = '.mov' if video_format == 'mov' else '.avi'

            # --- Local-drive export setup ---
            actual_proj = proj
            actual_proj_dir = proj_dir
            local_tmp_parent: Optional[str] = None
            files_before_export: set = set()

            if export_local:
                progress.set_text(f'Copying to local drive: {os.path.basename(proj_dir)}')
                try:
                    local_tmp_parent = tempfile.mkdtemp(prefix='spine_local_')
                    tmp_copy = os.path.join(local_tmp_parent, os.path.basename(proj_dir))
                    shutil.copytree(proj_dir, tmp_copy)
                    actual_proj_dir = tmp_copy
                    actual_proj = os.path.join(tmp_copy, os.path.basename(proj))
                    files_before_export = {os.path.join(actual_proj_dir, n) for n in os.listdir(actual_proj_dir)}
                    dprint(f'Local copy: {proj_dir} → {tmp_copy}')
                except Exception as e:
                    dprint(f'Failed to copy to local drive: {e}')
                    ui.show_error('Local copy failed', description=str(e))
                    local_tmp_parent = None  # fall back to original paths

            if auto_probe:
                progress.set_text(f'Probing skeletons: {os.path.basename(actual_proj)}')
                probed = probe_skeletons_sync(actual_proj, spine_exec)
                skeletons_to_do = probed if len(probed) > 1 else [None]
                dprint(f'Auto-probe {os.path.basename(actual_proj)}: {probed} → skeletons_to_do={skeletons_to_do}')
            else:
                skeletons_to_do = chosen_skeletons

            # Per-project status accumulators
            proj_failed = False
            proj_canceled = False

            for sk in skeletons_to_do:
                job_index += 1
                if progress.canceled:
                    proj_canceled = True
                    break

                settings_dict = build_export_settings_json_dict(video_format, width, height, fps, bg, single_file, use_fixed_viewport, center_viewport, viewport_x, viewport_y, sk)
                temp_json = write_temp_export_json(settings_dict)

                if user_output_override:
                    if single_file:
                        if looks_like_file(user_output_override):
                            if sk:
                                base_override, ext_override = os.path.splitext(user_output_override)
                                target = next_available_filename(f'{base_override}_{sk}{ext_override}')
                            else:
                                target = next_available_filename(user_output_override)
                        else:
                            fname = f'{base_name}{("_" + sk) if sk else ""}{ext}'
                            target = next_available_filename(os.path.join(user_output_override, fname))
                    else:
                        target = os.path.dirname(user_output_override) if looks_like_file(user_output_override) else user_output_override
                        if not target:
                            target = os.path.join(actual_proj_dir, f'{base_name}_{video_format}{("_" + sk) if sk else ""}')
                else:
                    if single_file:
                        fname = f'{base_name}{("_" + sk) if sk else ""}{ext}'
                        target = next_available_filename(os.path.join(actual_proj_dir, fname))
                    else:
                        target = os.path.join(actual_proj_dir, f'{base_name}_{video_format}{("_" + sk) if sk else ""}')

                ensure_dir(os.path.dirname(target) if looks_like_file(target) else target)

                label = f'{os.path.basename(proj)}'
                if sk: label += f' · skeleton: {sk}'
                if auto_probe:
                    progress.set_text(f'Exporting: {label}')
                else:
                    progress.set_text(f'{job_index}/{total_jobs} → Exporting: {label}')

                repaint_nudge = None if auto_probe else ((job_index - 1) / max(1.0, float(total_jobs)) + 0.0001)
                ok, maybe_log = run_spine_cli_with_progress(spine_exec, actual_proj, target, temp_json, progress, 0.5, repaint_nudge=repaint_nudge)

                try: os.remove(temp_json)
                except Exception: pass

                if maybe_log == 'canceled':
                    proj_canceled = True
                    break

                if not ok:
                    proj_failed = True
                    label_failed = f'{os.path.basename(proj)}{(" · " + sk) if sk else ""}'
                    if maybe_log:
                        dprint(f'Export failed for {label_failed} — log: {maybe_log}')
                        ui.show_error(f'Export failed: {label_failed}', description=f'Log saved to: {maybe_log}')
                    else:
                        dprint(f'Export failed for {label_failed}')
                        ui.show_error(f'Export failed: {label_failed}')
                else:
                    if single_file:
                        shown = target if (looks_like_file(target) and os.path.isfile(target)) else latest_file_in(os.path.dirname(target) if looks_like_file(target) else target, exts=['.mov', '.avi'])
                        ui.show_success('Export finished', os.path.basename(shown) if shown else 'Done.')
                    else:
                        ui.show_success('Export finished', f'Saved to folder: {target}')

                if not auto_probe:
                    progress.report_progress(job_index / float(total_jobs))

            # Check for missing images and write trace file
            check_result: dict = {}
            if not proj_failed and not proj_canceled:
                progress.set_text(f'Checking for missing images: {os.path.basename(actual_proj)}')
                check_result = check_missing_images_in_project(actual_proj, spine_exec)
                trace_path = os.path.join(actual_proj_dir, f'{base_name}_missing_images.txt')
                write_missing_images_trace(trace_path, actual_proj, check_result)

            # Move exported files back from local temp copy to original folder, then clean up
            if export_local and local_tmp_parent and os.path.isdir(actual_proj_dir):
                progress.set_text(f'Moving exported files back: {os.path.basename(proj_dir)}')
                try:
                    for name in os.listdir(actual_proj_dir):
                        full = os.path.join(actual_proj_dir, name)
                        if full not in files_before_export and os.path.isfile(full):
                            dest = os.path.join(proj_dir, name)
                            shutil.move(full, dest)
                            dprint(f'Moved {full} → {dest}')
                except Exception as e:
                    dprint(f'Failed to move files back: {e}')
                try:
                    shutil.rmtree(local_tmp_parent, ignore_errors=True)
                    dprint(f'Cleaned up local temp: {local_tmp_parent}')
                except Exception as e:
                    dprint(f'Failed to cleanup temp: {e}')

            # Write Preview Status attribute for this project's folder
            if _api is not None and not proj_canceled:
                if proj_failed:
                    folder_status = 'Export Failed'
                elif check_result.get('missing'):
                    folder_status = 'Missing IMG'
                else:
                    folder_status = 'Done'
                set_folder_preview_status(_api, proj_dir, folder_status)

            if proj_canceled:
                ui.show_info('Canceled', 'The export has been canceled by the user.')
                return

    except Exception as e:
        ui.show_error('Unexpected error during export', description=str(e))
    finally:
        progress.finish()

def find_spine_files_in_folders(folders: List[str]) -> List[str]:
    """Return .spine files found inside each folder.
    Scans recursively when the 'recursive_folder_scan' setting is enabled."""
    recursive = bool(settings.get("recursive_folder_scan", False))
    found = []
    seen = set()

    def _scan(dir_path: str):
        try:
            for name in sorted(os.listdir(dir_path)):
                full = os.path.join(dir_path, name)
                if name.lower().endswith('.spine') and os.path.isfile(full):
                    if full not in seen:
                        seen.add(full)
                        found.append(full)
                elif recursive and os.path.isdir(full):
                    _scan(full)
        except Exception as e:
            dprint(f"Could not scan folder '{dir_path}': {e}")

    for folder in folders:
        _scan(folder)
    return found

def show_batch_confirm_dialog(spine_files: List[str], on_confirm: Callable[[bool], None]):
    """Show a confirmation dialog listing found .spine files before batch export.
    Calls on_confirm(export_local) when the user clicks Export All."""
    d = ap.Dialog()
    d.icon = ctx.icon
    d.title = 'Batch Spine Export'

    count = len(spine_files)
    d.add_info(f'Found {count} Spine project{"s" if count != 1 else ""} in the selected folder{"s" if count != 1 else ""}.')
    d.add_info('Export all animations for each project with default settings?\n(60 fps · MOV · 1920×1080 · black background · saved alongside each project)')

    d.add_empty()
    for f in spine_files:
        folder_name = os.path.basename(os.path.dirname(f))
        d.add_text(f'{folder_name} / {os.path.basename(f)}')

    d.add_empty()
    d.add_checkbox(True, var='export_local', text='Export on Local Drive')

    d.add_empty()
    d.add_button('Export All', callback=lambda dlg: (on_confirm(bool(dlg.get_value('export_local'))), dlg.close()))
    d.add_button('Cancel', callback=lambda dlg: dlg.close())
    d.show()

def show_skeleton_picker(skeletons: List[str], on_done: Callable[[List[str]], None]):
    d = ap.Dialog()
    d.icon = ctx.icon
    d.title = 'Pick Skeletons'
    d.add_info('Step 1/2 â Choose skeletons for export')

    if not skeletons:
        d.add_info('(No skeletons detected â the project may contain a single skeleton or none.)')
        d.add_button('Continue', callback=lambda dlg: (dlg.close(), on_done([])))
        d.show()
        return

    for i, sk in enumerate(skeletons):
        d.add_checkbox(True, var=f'sk_{i}', text=sk)
        d.add_empty()

    def on_next(dialog: ap.Dialog):
        selected = [sk for i, sk in enumerate(skeletons) if dialog.get_value(f'sk_{i}')]
        if not selected:
            selected = skeletons[:]  # fallback to all
        dialog.close()
        on_done(selected)

    d.add_button('Next', callback=on_next)
    d.show()

def show_settings_and_run(chosen_skeletons: List[str]):
    d = ap.Dialog()
    d.icon = ctx.icon
    d.title = 'Spine Export Settings'
    d.add_info('Step 2/2 â Configure your export (all animations of each skeleton will be exported).')

    d.add_text('FPS\t').add_input('60', var='fps', width=100)
    d.add_text('Background\t').add_dropdown('black', ['black', 'white', 'transparent'], var='bg_choice')
    d.add_text('Output\t').add_dropdown('single', ['single', 'separate-per-animation'], var='out_mode')
    d.add_text('Format\t').add_dropdown('mov', ['mov', 'avi'], var='format')

    d.add_checkbox(True, var='export_local', text='Export on Local Drive')
    d.add_checkbox(False, var='fixed_viewport', text='Use Fixed Viewport (constant crop size)')
    d.add_text('Width\t').add_input('1920', var='res_w', width=100)
    d.add_text('Height\t').add_input('1080', var='res_h', width=100)
    d.start_section("Advanced settings", folded=True)
    d.add_checkbox(True, var='center_viewport', text='Center viewport on (0,0)')
    d.add_text('Viewport origin X\t').add_input('0', var='viewport_x', width=100)
    d.add_text('Viewport origin Y\t').add_input('0', var='viewport_y', width=100)
    d.add_empty()
    d.add_text('Custom BG color \t').add_input('', placeholder="#rrggbb", var='bg_hex', width=100)
    d.add_text('Output override \t').add_input('', placeholder="C:\\Animation", var='output_override')
    d.end_section()

    if chosen_skeletons:
        d.add_info('Skeletons: ' + ', '.join(chosen_skeletons))
    else:
        d.add_info('Skeletons: (all)')

    def on_export(dialog: ap.Dialog):
        fps = float(dialog.get_value('fps') or 60)
        bg_choice = dialog.get_value('bg_choice') or 'black'
        custom_hex = dialog.get_value('bg_hex') or ''
        bg = custom_hex if custom_hex.strip() else bg_choice

        mode = dialog.get_value('out_mode') or 'single'
        single = (mode == 'single')
        fmt = dialog.get_value('format') or 'mov'

        fixed = bool(dialog.get_value('fixed_viewport'))
        width = int(dialog.get_value('res_w') or 1920)
        height = int(dialog.get_value('res_h') or 1080)

        center = bool(dialog.get_value('center_viewport'))
        vx = int(dialog.get_value('viewport_x') or 0)
        vy = int(dialog.get_value('viewport_y') or 0)
        override = (dialog.get_value('output_override') or '').strip()
        exp_local = bool(dialog.get_value('export_local'))

        sel = [f for f in getattr(ctx, 'selected_files', []) if f.lower().endswith('.spine')]
        if not sel:
            ui.show_info('No .spine file selected', description='Select at least one .spine project.')
            return

        dialog.close()
        ctx.run_async(lambda: export_worker(sel, width, height, fps, bg, single, fmt, override, fixed, center, vx, vy, chosen_skeletons if chosen_skeletons else None, export_local=exp_local))

    d.add_button('Export', callback=on_export)
    d.show()

def main():
    dprint('Starting Spine Export _08')

    # Collect candidate paths from every context attribute Anchorpoint may populate.
    # - ctx.selected_files: documented for file actions; may include folder paths too.
    # - ctx.selected_folders: undocumented but may exist for folder multi-select.
    # - ctx.path: always the item the action was invoked on (reliable single-folder fallback).
    seen: set = set()
    all_paths: List[str] = []

    def _add(p: str):
        if p and p not in seen:
            seen.add(p)
            all_paths.append(p)

    for p in (getattr(ctx, 'selected_files', None) or []):
        _add(p)
    for p in (getattr(ctx, 'selected_folders', None) or []):
        _add(p)
    _add(getattr(ctx, 'path', '') or '')

    dprint(f'selected_files  = {getattr(ctx, "selected_files", None)}')
    dprint(f'selected_folders= {getattr(ctx, "selected_folders", None)}')
    dprint(f'ctx.path        = {getattr(ctx, "path", None)}')
    dprint(f'all_paths       = {all_paths}')

    # Separate .spine files from directories
    spine_files = [p for p in all_paths if p.lower().endswith('.spine') and os.path.isfile(p)]
    folders = [p for p in all_paths if os.path.isdir(p)]

    dprint(f'spine_files={spine_files}  folders={folders}')

    if spine_files:
        # Standard flow: skeleton picker → settings dialog
        project_file = spine_files[0]

        def after_probe(skeletons: List[str]):
            def after_skeletons(picked: List[str]):
                show_settings_and_run(picked)
            show_skeleton_picker(skeletons, after_skeletons)

        ctx.run_async(lambda: probe_skeletons_async(project_file, after_probe))

    elif folders:
        def scan_folders():
            progress = ap.Progress('Scanning folders...', infinite=True)
            progress.set_cancelable(False)

            folders_with_files: Dict[str, List[str]] = {}
            empty_folders: List[str] = []
            for folder in folders:
                progress.set_text(f'Scanning: {os.path.basename(folder)}')
                files = find_spine_files_in_folders([folder])
                if files:
                    folders_with_files[folder] = files
                else:
                    empty_folders.append(folder)

            progress.finish()

            all_spine_files = [f for files in folders_with_files.values() for f in files]

            def tag_no_anim(targets: List[str]):
                if not targets:
                    return
                try:
                    _api = ap.get_api()
                    ensure_preview_status_attribute(_api)
                    for folder in targets:
                        set_folder_preview_status(_api, folder, 'No Anim')
                except Exception as e:
                    dprint(f'Failed to set No Anim attributes: {e}')

            if not all_spine_files:
                ui.show_info('No Spine projects found', description='No .spine files were found in the selected folders.')
                tag_no_anim(empty_folders)
                return

            def do_batch(export_local: bool):
                tag_no_anim(empty_folders)
                d = BATCH_DEFAULTS
                export_worker(
                    all_spine_files,
                    d['width'], d['height'], d['fps'], d['bg'],
                    d['single_file'], d['video_format'], d['user_output_override'],
                    d['use_fixed_viewport'], d['center_viewport'],
                    d['viewport_x'], d['viewport_y'],
                    d['chosen_skeletons'],
                    export_local=export_local,
                )

            show_batch_confirm_dialog(all_spine_files, lambda loc: ctx.run_async(lambda: do_batch(loc)))

        ctx.run_async(scan_folders)

    else:
        ui.show_info('No selection', description='Select .spine files or folders containing .spine projects.')

if __name__ == '__main__':
    main()
