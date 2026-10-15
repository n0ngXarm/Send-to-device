"""Keep bundled Python libraries out of system-program subprocesses."""
from contextlib import contextmanager
import os
import subprocess
import sys
import threading

_spawn_lock = threading.Lock()


def environment():
    env = os.environ.copy()
    if getattr(sys, 'frozen', False):
        for key in ('LD_LIBRARY_PATH', 'LIBPATH'):
            original = env.get(key + '_ORIG')
            if original is None: env.pop(key, None)
            else: env[key] = original
    return env


@contextmanager
def system_libraries():
    with _spawn_lock:
        if sys.platform == 'win32' and getattr(sys, 'frozen', False):
            import ctypes
            ctypes.windll.kernel32.SetDllDirectoryW(None)
            try:
                yield
            finally:
                ctypes.windll.kernel32.SetDllDirectoryW(str(sys._MEIPASS))
        else:
            yield


def popen(*args, **kwargs):
    kwargs.setdefault('env', environment())
    with system_libraries():
        return subprocess.Popen(*args, **kwargs)


def run(*args, **kwargs):
    kwargs.setdefault('env', environment())
    with system_libraries():
        return subprocess.run(*args, **kwargs)
