"""Transfer operations with no dependency on a desktop UI."""
from collections import deque
from contextlib import contextmanager
import datetime
import ipaddress
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
import zipfile

CREATE_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

class Cancelled(Exception):
    pass


def state_directory():
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'SendToDevice' / 'state'
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/SendToDevice/state'
    return Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'send-to-device'


def find_tailscale():
    command = shutil.which('tailscale')
    candidates = [command] if command else []
    if sys.platform == 'win32':
        candidates.append(str(Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Tailscale/tailscale.exe'))
    elif sys.platform == 'darwin':
        candidates += ['/Applications/Tailscale.app/Contents/MacOS/Tailscale', '/opt/homebrew/bin/tailscale', '/usr/local/bin/tailscale']
    for candidate in candidates:
        if Path(candidate).is_file():
            return str(candidate)
    raise RuntimeError('ไม่พบ Tailscale กรุณาติดตั้งและเข้าสู่ระบบก่อนใช้งาน\nhttps://tailscale.com/download')


def clean(value):
    return ' '.join(str(value).split())


def devices(status, targets):
    if status.get('BackendState') != 'Running':
        raise RuntimeError('Tailscale ยังไม่เชื่อมต่อ กรุณาเปิดและเข้าสู่ระบบก่อน')
    eligible = {line.split()[0] for line in targets.splitlines() if line.strip()}
    owner = (status.get('Self') or {}).get('UserID')
    rows = []
    for peer in (status.get('Peer') or {}).values():
        ips = peer.get('TailscaleIPs') or []
        if not ips or peer.get('ShareeNode'):
            continue
        if owner is not None and peer.get('UserID') != owner:
            continue
        ip = next((item for item in ips if ':' not in item), ips[0])
        ipaddress.ip_address(ip)
        capable = any(item in eligible for item in ips)
        online = peer.get('Online') is True
        rows.append(dict(ip=ip, name=clean(peer.get('HostName') or peer.get('DNSName') or ip),
                         online=online, capable=capable, ready=online and capable,
                         os=clean(peer.get('OS') or 'Unknown')))
    return rows


def stop(process):
    if process.poll() is not None:
        return
    try:
        if os.name == 'nt':
            process.terminate()
        else:
            os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        if os.name == 'nt':
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
    except ProcessLookupError:
        process.wait()


def check_cancel(cancel):
    if cancel.is_set():
        raise Cancelled()


def query(binary, *args):
    result = subprocess.run([binary, *args], capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=20, creationflags=CREATE_FLAGS)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or 'อ่านข้อมูล Tailscale ไม่สำเร็จ')
    return result.stdout


def discover(binary):
    return devices(json.loads(query(binary, 'status', '--json')), query(binary, 'file', 'cp', '--targets'))


def validate(paths):
    if not paths:
        raise ValueError('เลือกไฟล์หรือโฟลเดอร์ก่อนส่ง')
    names = []
    for path in paths:
        if not (path.is_file() or path.is_dir()) or not os.access(path, os.R_OK):
            raise ValueError(f'อ่านไฟล์หรือโฟลเดอร์ไม่ได้: {path}')
        name = path.name + ('.zip' if path.is_dir() else '')
        if not path.name:
            raise ValueError('กรุณาเลือกโฟลเดอร์ย่อย ไม่ใช่ทั้งไดรฟ์')
        names.append(name.casefold())
    if len(names) != len(set(names)):
        raise ValueError('ชื่อไฟล์ปลายทางซ้ำกัน กรุณาเปลี่ยนชื่อหรือแยกส่ง')


def archive(source, destination, cancel):
    def walk_error(error):
        raise error
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as z:
        for root, dirs, files in os.walk(source, followlinks=False, onerror=walk_error):
            check_cancel(cancel)
            base = Path(root)
            for name in dirs + files:
                entry = base / name
                if entry.is_symlink() or (hasattr(entry, 'is_junction') and entry.is_junction()):
                    raise ValueError(f'กรุณาเลือกไฟล์ต้นฉบับแทนลิงก์: {entry}')
            z.write(base, str(Path(source.name) / base.relative_to(source)))
            for name in files:
                path = base / name
                if not path.is_file():
                    raise ValueError(f'ไม่รองรับไฟล์ชนิดนี้: {path}')
                with path.open('rb') as src, z.open(str(Path(source.name) / path.relative_to(source)), 'w', force_zip64=True) as dst:
                    while True:
                        check_cancel(cancel)
                        block = src.read(1024 * 1024)
                        if not block:
                            break
                        dst.write(block)


def push(binary, path, ip, log, cancel, timeout):
    ipaddress.ip_address(ip)
    target = f'[{ip}]:' if ':' in ip else ip + ':'
    process = subprocess.Popen([binary, 'file', 'cp', str(path), target], stdout=log, stderr=log,
                               start_new_session=os.name != 'nt', creationflags=CREATE_FLAGS)
    deadline = time.monotonic() + timeout
    try:
        while process.poll() is None:
            check_cancel(cancel)
            if time.monotonic() >= deadline:
                return 124
            cancel.wait(.15)
        return process.returncode
    finally:
        stop(process)


class State:
    def __init__(self, root=None):
        self.root = root or state_directory()
        self.root.mkdir(parents=True, exist_ok=True)

    def settings(self):
        defaults = dict(timeout_minutes=30, ready_only=False, last_target='')
        try:
            data = json.loads((self.root / 'settings.json').read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                return defaults
            minutes = data.get('timeout_minutes')
            if type(minutes) is int and minutes in (5, 15, 30, 60, 120, 240):
                defaults['timeout_minutes'] = minutes
            if type(data.get('ready_only')) is bool:
                defaults['ready_only'] = data['ready_only']
            if isinstance(data.get('last_target'), str):
                defaults['last_target'] = data['last_target']
        except (OSError, ValueError):
            pass
        return defaults

    def save(self, settings):
        target = self.root / 'settings.tmp'
        target.write_text(json.dumps(settings), encoding='utf-8')
        target.replace(self.root / 'settings.json')

    def record(self, target, sent, total, result):
        record = dict(time=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
                      target=target['name'], ip=target['ip'], sent=sent, total=total, result=result)
        with (self.root / 'history.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + '\n')

    def history(self):
        try:
            with (self.root / 'history.jsonl').open(encoding='utf-8') as stream:
                lines = deque(stream, maxlen=100)
        except FileNotFoundError:
            return []
        rows = []
        for line in reversed(lines):
            try:
                row = json.loads(line)
                if all(k in row for k in ('time', 'target', 'sent', 'total', 'result')):
                    rows.append(row)
            except (ValueError, TypeError):
                continue
        return rows

    @contextmanager
    def lock(self):
        with (self.root / 'transfer.lock').open('a+b') as stream:
            if os.name == 'nt':
                import msvcrt
                stream.seek(0); stream.write(b'0'); stream.flush(); stream.seek(0)
                try:
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as error:
                    raise RuntimeError('มีการส่งไฟล์จากหน้าต่างอื่นอยู่แล้ว') from error
            else:
                import fcntl
                try:
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as error:
                    raise RuntimeError('มีการส่งไฟล์จากหน้าต่างอื่นอยู่แล้ว') from error
            try:
                yield
            finally:
                if os.name == 'nt':
                    stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def transfer(binary, paths, target, state, cancel, update, retry):
    """Send sequentially; callbacks report progress and ask before retrying."""
    import tempfile
    validate(paths)
    sent = 0
    outcome = 'ไม่สำเร็จ'
    with state.lock():
        try:
            current = next((r for r in discover(binary) if r['ip'] == target['ip']), None)
            check_cancel(cancel)
            if not current or not current['ready']:
                raise RuntimeError('ปลายทางไม่พร้อมรับไฟล์แล้ว กรุณารีเฟรชรายชื่อ')
            timeout = state.settings()['timeout_minutes'] * 60
            with tempfile.TemporaryDirectory(prefix='send-to-device-') as temporary, (state.root / 'last-transfer.log').open('w', encoding='utf-8') as log:
                for index, original in enumerate(paths):
                    check_cancel(cancel)
                    path = original
                    if original.is_dir():
                        update(sent, f'กำลังรวมโฟลเดอร์ {original.name} เป็น ZIP')
                        folder = Path(temporary) / str(index); folder.mkdir()
                        path = folder / (original.name + '.zip')
                        archive(original, path, cancel)
                    while True:
                        check_cancel(cancel)
                        update(sent, f'กำลังส่ง {path.name} → {target["name"]} ({target["ip"]})')
                        log.write(f'\n{path.name!r} -> {target["ip"]}\n'); log.flush()
                        code = push(binary, path, target['ip'], log, cancel, timeout)
                        log.write(f'Exit status: {code}\n'); log.flush()
                        if code == 0:
                            sent += 1
                            prefs = state.settings(); prefs['last_target'] = target['ip']; state.save(prefs)
                            update(sent, f'ส่งสำเร็จ {sent}/{len(paths)} รายการ')
                            break
                        check_cancel(cancel)
                        if not retry(path.name, code, sent):
                            return sent, outcome
                    if path != original:
                        path.unlink()  # release temporary disk space after each folder
                outcome = 'สำเร็จ'
                return sent, outcome
        except Cancelled:
            outcome = 'ยกเลิก'
            return sent, outcome
        finally:
            state.record(target, sent, len(paths), outcome)
