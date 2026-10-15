"""Real Tk widget smoke test, with no network and no file transfers."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tempfile
import tkinter as tk
from send_to_device import core
from send_to_device.gui import App

with tempfile.TemporaryDirectory() as d:
    root = tk.Tk()
    app = App(root, state=core.State(Path(d)), autoload=False)
    app.rows = {f'100.64.0.{i}': dict(ip=f'100.64.0.{i}', name='same name', online=ready,
                ready=ready, capable=True, os='linux') for i,ready in [(1,True),(2,False)]}
    app.render_devices(); root.update()
    assert len(app.tree.get_children()) == 2
    assert 'ip' in app.tree['columns']
    assert app.tree.item('100.64.0.1')['values'][1] == '100.64.0.1'
    app.only_ready.set(True); app.filter_changed(); root.update()
    assert len(app.tree.get_children()) == 1
    file=Path(d)/'sample.txt'; file.write_text('test'); app.paths=[file]
    app.tree.selection_set('100.64.0.1'); app.render_files(); root.update()
    assert app.send_button.instate(['!disabled'])
    app.busy=True; app.controls(); root.update()
    assert app.send_button.instate(['disabled'])
    assert app.cancel_button.instate(['!disabled'])
    root.destroy()
print('Tk desktop smoke test passed')
