"""Native Tk interface; network and disk work never runs on the UI thread."""
import datetime
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from . import __version__, core

TITLE = 'Send to Device'

class App:
    def __init__(self, root, paths=(), state=None, autoload=True):
        self.root = root
        self.state = state or core.State()
        self.prefs = self.state.settings()
        self.paths = list(dict.fromkeys(Path(os.path.abspath(p)) for p in paths))
        self.rows = {}
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.busy = False
        self.refreshing = False
        self.closing = False
        self.root.title(TITLE)
        self.root.geometry('920x680')
        self.root.minsize(760, 590)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        style = ttk.Style()
        style.configure('Title.TLabel', font=('TkDefaultFont', 20, 'bold'))
        style.configure('Treeview', rowheight=30)
        style.configure('Heading.TLabel', font=('TkDefaultFont', 11, 'bold'))
        main = ttk.Frame(root, padding=22); main.pack(fill='both', expand=True)
        header = ttk.Frame(main); header.pack(fill='x')
        ttk.Label(header, text='ส่งไปเครื่องของฉัน', style='Title.TLabel').pack(side='left')
        ttk.Label(header, text=f'Taildrop · v{__version__}').pack(side='right')
        ttk.Label(main, text='เลือกไฟล์  →  เลือกเครื่อง  →  ส่ง', padding=(0, 5, 0, 15)).pack(anchor='w')
        tabs = ttk.Notebook(main); tabs.pack(fill='both', expand=True)
        send_tab = ttk.Frame(tabs, padding=12)
        history_tab = ttk.Frame(tabs, padding=12)
        settings_tab = ttk.Frame(tabs, padding=16)
        tabs.add(send_tab, text='  ส่งไฟล์  '); tabs.add(history_tab, text='  ประวัติ  '); tabs.add(settings_tab, text='  ตั้งค่า / วิธีรับไฟล์  ')
        tabs.bind('<<NotebookTabChanged>>', lambda e: self.history())
        files_bar = ttk.Frame(send_tab); files_bar.pack(fill='x')
        self.summary = ttk.Label(files_bar, style='Heading.TLabel'); self.summary.pack(side='left')
        self.edit_buttons = []
        for title, command in [('เพิ่มไฟล์', self.add_files), ('เพิ่มโฟลเดอร์', self.add_folder), ('ล้าง', self.clear_files)]:
            button = ttk.Button(files_bar, text=title, command=command); button.pack(side='right', padx=3)
            self.edit_buttons.append(button)
        self.file_list = tk.Listbox(send_tab, height=3, selectmode='extended', borderwidth=0, highlightthickness=1)
        self.file_list.pack(fill='x', pady=(10, 3))
        remove = ttk.Button(send_tab, text='เอารายการที่เลือกออก', command=self.remove_files)
        remove.pack(anchor='e'); self.edit_buttons.append(remove)
        bar = ttk.Frame(send_tab); bar.pack(fill='x', pady=(15, 8))
        ttk.Label(bar, text='เครื่องปลายทาง', style='Heading.TLabel').pack(side='left')
        self.refresh_button = ttk.Button(bar, text='รีเฟรช', command=self.refresh); self.refresh_button.pack(side='right')
        self.only_ready = tk.BooleanVar(value=self.prefs['ready_only'])
        self.filter_button = ttk.Checkbutton(bar, text='เฉพาะเครื่องพร้อมรับ', variable=self.only_ready, command=self.filter_changed)
        self.filter_button.pack(side='right', padx=12)
        self.tree = self.table(send_tab, [('name', 'ชื่อเครื่อง', 220), ('ip', 'Tailscale IP', 155), ('status', 'สถานะ', 190), ('os', 'ระบบ', 90), ('last', 'ล่าสุด', 90)])
        self.tree.bind('<<TreeviewSelect>>', lambda e: self.controls())
        self.device_status = ttk.Label(send_tab, text='กำลังโหลดรายชื่อ…'); self.device_status.pack(anchor='w', pady=7)
        self.history_tree = self.table(history_tab, [('time', 'วัน / เวลา', 160), ('target', 'เครื่อง', 170), ('ip', 'IP', 145), ('count', 'สำเร็จ / ทั้งหมด', 100), ('result', 'ผล', 100)])
        ttk.Button(history_tab, text='เปิดโฟลเดอร์บันทึก', command=self.open_state).pack(anchor='e', pady=10)
        ttk.Label(settings_tab, text='การส่งไฟล์', style='Heading.TLabel').pack(anchor='w')
        ttk.Label(settings_tab, text='เวลาสูงสุดต่อไฟล์ (นาที)').pack(anchor='w', pady=(15, 4))
        self.minutes = tk.StringVar(value=str(self.prefs['timeout_minutes']))
        self.timeout_combo = ttk.Combobox(settings_tab, textvariable=self.minutes, values=(5, 15, 30, 60, 120, 240), state='readonly', width=15)
        self.timeout_combo.pack(anchor='w')
        self.save_button = ttk.Button(settings_tab, text='บันทึกการตั้งค่า', command=self.save_settings)
        self.save_button.pack(anchor='w', pady=10)
        ttk.Separator(settings_tab).pack(fill='x', pady=12)
        ttk.Label(settings_tab, text='หาไฟล์ที่รับได้จากที่ไหน?', style='Heading.TLabel').pack(anchor='w')
        ttk.Label(settings_tab, wraplength=680, justify='left', text='Android: ดูการแจ้งเตือน หรือโฟลเดอร์รับที่กำหนดใน Tailscale\nWindows / macOS: ตรวจโฟลเดอร์ Downloads หรือการตั้งค่ารับไฟล์ของ Tailscale\nLinux: ใช้ตัวรับอัตโนมัติที่ตั้งไว้ หรือ tailscale file get <โฟลเดอร์>\n\nส่งสำเร็จหมายถึง Tailscale ปลายทางรับไฟล์แล้ว ไม่ได้ยืนยันว่าผู้รับเปิดไฟล์\nโฟลเดอร์จะส่งเป็น ZIP โดยไม่ลดคุณภาพไฟล์ รูปภาพ หรือวิดีโอ\nเครื่องของผู้ใช้อื่นไม่รองรับ Taildrop').pack(anchor='w', pady=10)
        footer = ttk.Frame(main); footer.pack(fill='x', pady=(16, 0))
        self.status = ttk.Label(footer, text='พร้อมใช้งาน', wraplength=630); self.status.pack(anchor='w')
        actions = ttk.Frame(footer); actions.pack(fill='x', pady=(8, 0))
        self.progress = ttk.Progressbar(actions, maximum=100); self.progress.pack(side='left', fill='x', expand=True, padx=(0, 14))
        self.cancel_button = ttk.Button(actions, text='หยุดส่ง', command=self.cancel_transfer, state='disabled'); self.cancel_button.pack(side='right', padx=(6, 0))
        self.send_button = ttk.Button(actions, text='ส่งไฟล์', command=self.send, state='disabled'); self.send_button.pack(side='right')
        self.render_files(); self.history()
        root.after(100, self.drain)
        if autoload:
            root.after(100, self.refresh)

    def table(self, parent, columns):
        frame = ttk.Frame(parent); frame.pack(fill='both', expand=True)
        tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show='headings', selectmode='browse', height=6)
        for key, title, width in columns:
            tree.heading(key, text=title); tree.column(key, width=width, minwidth=75)
        scroll = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y'); tree.pack(fill='both', expand=True)
        return tree

    def controls(self):
        selected = self.tree.selection()
        ready = bool(selected and self.rows.get(selected[0], {}).get('ready'))
        self.send_button.configure(state='normal' if self.paths and ready and not self.busy and not self.refreshing else 'disabled')
        for button in self.edit_buttons + [self.save_button, self.filter_button]:
            button.configure(state='disabled' if self.busy else 'normal')
        self.refresh_button.configure(state='disabled' if self.busy or self.refreshing else 'normal')
        self.cancel_button.configure(state='normal' if self.busy and not self.cancel.is_set() else 'disabled')
        self.timeout_combo.configure(state='disabled' if self.busy else 'readonly')

    def render_files(self):
        self.file_list.delete(0, 'end')
        total = 0
        folders = 0
        for path in self.paths:
            try:
                if path.is_dir():
                    folders += 1; label = '[ZIP] '
                else:
                    total += path.stat().st_size; label = ''
            except OSError:
                label = '[อ่านไม่ได้] '
            self.file_list.insert('end', label + str(path))
        self.summary.configure(text=f'{len(self.paths)} รายการ · ไฟล์ {total / 1048576:,.1f} MB' + (f' · {folders} โฟลเดอร์' if folders else ''))
        self.controls()

    def add_files(self):
        for name in filedialog.askopenfilenames(parent=self.root, title='เลือกไฟล์'):
            if Path(name) not in self.paths: self.paths.append(Path(name))
        self.render_files()

    def add_folder(self):
        name = filedialog.askdirectory(parent=self.root, title='เลือกโฟลเดอร์ที่จะส่งเป็น ZIP')
        if name and Path(name) not in self.paths: self.paths.append(Path(name))
        self.render_files()

    def clear_files(self):
        self.paths.clear(); self.render_files()

    def remove_files(self):
        for index in reversed(self.file_list.curselection()): self.paths.pop(index)
        self.render_files()

    def refresh(self):
        if self.busy or self.refreshing: return
        self.refreshing = True; self.controls()
        self.device_status.configure(text='กำลังตรวจ Tailscale…')
        def work():
            try: self.events.put(('devices', core.discover(core.find_tailscale())))
            except Exception as error: self.events.put(('discovery_error', str(error)))
        threading.Thread(target=work, daemon=True).start()

    def render_devices(self):
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        rows = sorted(self.rows.values(), key=lambda r: (not r['ready'], r['ip'] != self.prefs['last_target'], r['name'].casefold()))
        for row in rows:
            if self.only_ready.get() and not row['ready']: continue
            status = 'พร้อมรับไฟล์' if row['ready'] else ('ออนไลน์ · ยังรับไม่ได้' if row['online'] else 'ออฟไลน์')
            self.tree.insert('', 'end', iid=row['ip'], values=(row['name'], row['ip'], status, row['os'], 'ใช้ล่าสุด' if row['ip'] == self.prefs['last_target'] else ''))
        pick = selected[0] if selected else self.prefs['last_target']
        if pick and self.tree.exists(pick): self.tree.selection_set(pick)
        ready = sum(r['ready'] for r in rows)
        self.device_status.configure(text=f'พร้อมรับ {ready} / {len(rows)} เครื่อง · ตรวจซ้ำก่อนส่ง' if rows else 'ไม่พบเครื่องของคุณ เปิด Tailscale บนปลายทาง แล้วกดรีเฟรช')
        self.controls()

    def filter_changed(self):
        self.prefs['ready_only'] = self.only_ready.get()
        self.persist(); self.render_devices()

    def persist(self):
        try: self.state.save(self.prefs)
        except OSError as error: messagebox.showerror(TITLE, str(error), parent=self.root)

    def save_settings(self):
        self.prefs['timeout_minutes'] = int(self.minutes.get()); self.persist()
        self.status.configure(text='บันทึกการตั้งค่าแล้ว')

    def history(self):
        self.history_tree.delete(*self.history_tree.get_children())
        for row in self.state.history():
            try: when = datetime.datetime.fromisoformat(row['time']).strftime('%d/%m/%Y %H:%M')
            except (ValueError, TypeError): when = str(row['time'])
            self.history_tree.insert('', 'end', values=(when, row['target'], row.get('ip', ''), f"{row['sent']}/{row['total']}", row['result']))

    def open_state(self):
        try:
            if sys.platform == 'win32': os.startfile(str(self.state.root))
            else: subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(self.state.root)])
        except OSError as error: messagebox.showerror(TITLE, str(error), parent=self.root)

    def send(self):
        selected = self.tree.selection()
        if self.busy or not selected: return
        target = self.rows[selected[0]].copy()
        paths = self.paths[:]
        try: core.validate(paths)
        except ValueError as error:
            messagebox.showerror(TITLE, str(error), parent=self.root); return
        self.busy = True; self.cancel.clear(); self.progress['value'] = 0; self.controls()
        self.status.configure(text='กำลังตรวจปลายทาง…')
        def retry(name, code, sent):
            answer = queue.Queue()
            self.events.put(('retry', (name, code, sent, answer)))
            while True:
                core.check_cancel(self.cancel)
                try: return answer.get(timeout=.15)
                except queue.Empty: pass
        def work():
            try:
                result = core.transfer(core.find_tailscale(), paths, target, self.state, self.cancel,
                    lambda count, text: self.events.put(('progress', (count, len(paths), text))), retry)
                self.events.put(('done', (result, len(paths), target)))
            except Exception as error: self.events.put(('transfer_error', str(error)))
        threading.Thread(target=work, daemon=True).start()

    def cancel_transfer(self):
        self.cancel.set(); self.status.configure(text='กำลังหยุดส่ง…'); self.controls()

    def close(self):
        if self.busy:
            if not messagebox.askyesno(TITLE, 'หยุดส่งและปิดหน้าต่าง?', parent=self.root): return
            self.closing = True; self.cancel_transfer()
        else: self.root.destroy()

    def drain(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == 'devices':
                    self.refreshing = False; self.rows = {r['ip']: r for r in data}; self.render_devices()
                elif kind == 'discovery_error':
                    self.refreshing = False; self.rows = {}; self.render_devices()
                    self.device_status.configure(text='โหลดรายชื่อไม่สำเร็จ — กดรีเฟรชเพื่อลองใหม่')
                    messagebox.showerror(TITLE, data, parent=self.root)
                elif kind == 'progress':
                    count, total, text = data
                    self.progress['value'] = count * 100 / total
                    self.status.configure(text=f'{text} · สำเร็จ {count}/{total} รายการ')
                elif kind == 'retry':
                    name, code, sent, answer = data
                    value = False if self.cancel.is_set() else messagebox.askretrycancel(TITLE,
                        f'ส่ง {name} ไม่สำเร็จ (รหัส {code})\nส่งสำเร็จแล้ว {sent} รายการ\nลองใหม่เฉพาะไฟล์นี้?\nรายละเอียดอยู่ใน last-transfer.log', parent=self.root)
                    answer.put(value)
                elif kind in ('done', 'transfer_error'):
                    self.busy = False; self.prefs = self.state.settings(); self.controls(); self.history(); self.render_devices()
                    if self.closing:
                        self.root.destroy(); return
                    if kind == 'transfer_error':
                        self.status.configure(text='ส่งไม่สำเร็จ — ดูประวัติและบันทึกข้อผิดพลาด')
                        messagebox.showerror(TITLE, data, parent=self.root)
                    else:
                        (sent, outcome), total, target = data
                        text = f'{outcome} · {sent}/{total} รายการ → {target["name"]} ({target["ip"]})'
                        self.status.configure(text=text)
                        messagebox.showinfo(TITLE, text + '\nไฟล์ที่ส่งสำเร็จแล้วจะอยู่ที่ปลายทาง\nดูวิธีรับไฟล์ในแท็บตั้งค่า', parent=self.root)
        except queue.Empty:
            pass
        self.root.after(100, self.drain)


def main(paths=()):
    if os.name != 'nt': os.umask(0o077)
    root = tk.Tk()
    App(root, paths)
    root.mainloop()
