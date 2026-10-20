"""Native Tk interface; network and disk work never runs on the UI thread."""
import datetime
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk
from . import __version__, core, runtime

TITLE = 'Send to Device'

def is_dark_mode():
    """Detects system dark mode preference across Linux GNOME, Windows, and macOS."""
    if sys.platform.startswith('linux'):
        try:
            res = subprocess.run(
                ['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'],
                capture_output=True, text=True, timeout=1
            )
            if 'prefer-dark' in res.stdout.lower():
                return True
            if 'prefer-light' in res.stdout.lower():
                return False
        except Exception:
            pass
        return True
    elif sys.platform == 'win32':
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
        except Exception:
            return True
    elif sys.platform == 'darwin':
        try:
            res = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                capture_output=True, text=True, timeout=1
            )
            return 'dark' in res.stdout.lower()
        except Exception:
            return False
    return True

def get_theme_colors(dark=True):
    if dark:
        return {
            'bg': '#242424',
            'card': '#2e2e2e',
            'card_header': '#383838',
            'border': '#424242',
            'fg': '#ffffff',
            'fg_dim': '#9a9996',
            'primary': '#3584e4',
            'primary_hover': '#4f9cf8',
            'primary_active': '#1c71d8',
            'primary_fg': '#ffffff',
            'danger': '#c01c28',
            'danger_hover': '#e01b24',
            'success': '#33d17a',
            'warning': '#f6d32d',
            'list_bg': '#1e1e1e',
            'list_fg': '#f6f6f6',
            'trough': '#202020',
        }
    else:
        return {
            'bg': '#f6f6f6',
            'card': '#ffffff',
            'card_header': '#f0f0f0',
            'border': '#dedede',
            'fg': '#242424',
            'fg_dim': '#77767b',
            'primary': '#3584e4',
            'primary_hover': '#1c71d8',
            'primary_active': '#185fb4',
            'primary_fg': '#ffffff',
            'danger': '#c01c28',
            'danger_hover': '#a51d2d',
            'success': '#26a269',
            'warning': '#e5a50a',
            'list_bg': '#ffffff',
            'list_fg': '#242424',
            'trough': '#e1e1e1',
        }


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
        self.root.geometry('940x700')
        self.root.minsize(780, 600)
        self.root.protocol('WM_DELETE_WINDOW', self.close)

        dark = is_dark_mode()
        self.colors = get_theme_colors(dark)
        self.root.configure(bg=self.colors['bg'])

        # Font configuration
        available_fonts = set(font.families(self.root))
        for f in ('Cantarell', 'Noto Sans', 'Segoe UI', 'SF Pro Text', 'Ubuntu', 'DejaVu Sans'):
            if f in available_fonts:
                font_name = f
                break
        else:
            font_name = 'TkDefaultFont'

        self.font_main = (font_name, 10)
        self.font_bold = (font_name, 10, 'bold')
        self.font_title = (font_name, 18, 'bold')
        self.font_heading = (font_name, 11, 'bold')
        self.font_small = (font_name, 9)

        # Style setup with clam theme
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        style.configure('TFrame', background=self.colors['bg'])
        style.configure('Card.TFrame', background=self.colors['card'], relief='flat', borderwidth=0)
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'], font=self.font_main)
        style.configure('Card.TLabel', background=self.colors['card'], foreground=self.colors['fg'], font=self.font_main)
        style.configure('Title.TLabel', background=self.colors['bg'], foreground=self.colors['fg'], font=self.font_title)
        style.configure('Heading.TLabel', background=self.colors['bg'], foreground=self.colors['fg'], font=self.font_heading)
        style.configure('CardHeading.TLabel', background=self.colors['card'], foreground=self.colors['fg'], font=self.font_heading)
        style.configure('Muted.TLabel', background=self.colors['bg'], foreground=self.colors['fg_dim'], font=self.font_small)
        style.configure('CardMuted.TLabel', background=self.colors['card'], foreground=self.colors['fg_dim'], font=self.font_small)

        style.configure('TNotebook', background=self.colors['bg'], borderwidth=1, bordercolor=self.colors['border'], darkcolor=self.colors['border'], lightcolor=self.colors['border'])
        style.configure('TNotebook.Tab', background=self.colors['card'], foreground=self.colors['fg_dim'], padding=[18, 9], font=self.font_bold, borderwidth=1, bordercolor=self.colors['border'], darkcolor=self.colors['border'], lightcolor=self.colors['border'])
        style.map('TNotebook.Tab',
            background=[('selected', self.colors['bg']), ('active', self.colors['card_header'])],
            foreground=[('selected', self.colors['primary']), ('active', self.colors['fg'])],
            bordercolor=[('selected', self.colors['border']), ('!selected', self.colors['border'])],
            darkcolor=[('selected', self.colors['border']), ('!selected', self.colors['border'])],
            lightcolor=[('selected', self.colors['border']), ('!selected', self.colors['border'])],
        )

        style.configure('TButton', background=self.colors['card_header'], foreground=self.colors['fg'], borderwidth=1, bordercolor=self.colors['border'], darkcolor=self.colors['border'], lightcolor=self.colors['border'], relief='flat', padding=[10, 5], font=self.font_main)
        style.map('TButton',
            background=[('disabled', self.colors['card']), ('pressed', self.colors['primary_active']), ('active', '#444444' if dark else '#e2e2e2')],
            foreground=[('disabled', self.colors['fg_dim']), ('pressed', '#ffffff'), ('active', self.colors['fg'])],
            bordercolor=[('active', self.colors['primary'])]
        )

        style.configure('Primary.TButton', background=self.colors['primary'], foreground='#ffffff', borderwidth=1, bordercolor=self.colors['primary'], darkcolor=self.colors['primary'], lightcolor=self.colors['primary'], relief='flat', padding=[18, 8], font=self.font_bold)
        style.map('Primary.TButton',
            background=[('disabled', '#333333'), ('pressed', self.colors['primary_active']), ('active', self.colors['primary_hover']), ('!disabled', self.colors['primary'])],
            foreground=[('disabled', self.colors['fg_dim']), ('!disabled', '#ffffff')],
            bordercolor=[('disabled', '#424242'), ('!disabled', self.colors['primary'])],
            darkcolor=[('disabled', '#424242'), ('!disabled', self.colors['primary'])],
            lightcolor=[('disabled', '#424242'), ('!disabled', self.colors['primary'])],
        )

        style.configure('Danger.TButton', background=self.colors['card_header'], foreground=self.colors['danger'], borderwidth=1, bordercolor=self.colors['border'], darkcolor=self.colors['border'], lightcolor=self.colors['border'], relief='flat', padding=[14, 8], font=self.font_main)
        style.map('Danger.TButton',
            background=[('disabled', self.colors['card']), ('active', self.colors['card_header'])],
            foreground=[('disabled', self.colors['fg_dim']), ('active', self.colors['danger_hover'])],
            bordercolor=[('active', self.colors['danger'])]
        )

        style.configure('TCheckbutton', background=self.colors['bg'], foreground=self.colors['fg'], font=self.font_main)
        style.configure('Card.TCheckbutton', background=self.colors['card'], foreground=self.colors['fg'], font=self.font_main)

        style.configure('Horizontal.TProgressbar', background=self.colors['primary'], troughcolor=self.colors['trough'], borderwidth=0)
        style.configure('Treeview', background=self.colors['card'], fieldbackground=self.colors['card'], foreground=self.colors['fg'], rowheight=32, borderwidth=0, font=self.font_main)
        style.configure('Treeview.Heading', background=self.colors['card_header'], foreground=self.colors['fg'], font=self.font_bold, relief='flat', borderwidth=0, padding=[8, 8])
        style.map('Treeview', background=[('selected', self.colors['primary'])], foreground=[('selected', '#ffffff')])
        style.map('Treeview.Heading', background=[('active', self.colors['card_header'])])
        style.configure('Vertical.TScrollbar', background=self.colors['card_header'], troughcolor=self.colors['card'], borderwidth=0, relief='flat', arrowsize=11)
        style.configure('TSeparator', background=self.colors['border'])

        main = ttk.Frame(root, padding=(20, 18, 20, 18))
        main.pack(fill='both', expand=True)

        # Header section (top)
        header = ttk.Frame(main)
        header.pack(side='top', fill='x', pady=(0, 4))
        ttk.Label(header, text='ส่งไปเครื่องของฉัน', style='Title.TLabel').pack(side='left')
        ttk.Label(header, text=f'Taildrop · v{__version__}', style='Muted.TLabel').pack(side='right')

        sub_header = ttk.Frame(main)
        sub_header.pack(side='top', fill='x', pady=(0, 10))
        ttk.Label(sub_header, text='เลือกไฟล์และโฟลเดอร์  →  เลือกเครื่องปลายทาง  →  ส่งไฟล์', style='Muted.TLabel').pack(side='left')

        # Footer section (bottom) - Packed before tabs so it is NEVER clipped
        footer = ttk.Frame(main)
        footer.pack(side='bottom', fill='x', pady=(12, 0))

        self.status = ttk.Label(footer, text='พร้อมใช้งาน', wraplength=650, style='TLabel')
        self.status.pack(anchor='w', pady=(0, 6))

        actions = ttk.Frame(footer)
        actions.pack(fill='x')

        self.send_button = ttk.Button(actions, text='ส่งไฟล์', command=self.send, state='disabled', style='Primary.TButton')
        self.send_button.pack(side='right')

        self.cancel_button = ttk.Button(actions, text='หยุดส่ง', command=self.cancel_transfer, state='disabled', style='Danger.TButton')
        self.cancel_button.pack(side='right', padx=(0, 12))

        self.progress = ttk.Progressbar(actions, maximum=100, style='Horizontal.TProgressbar')
        self.progress.pack(side='left', fill='x', expand=True, padx=(0, 16))

        # Tabs (middle, takes all remaining space)
        tabs = ttk.Notebook(main)
        tabs.pack(side='top', fill='both', expand=True)

        send_tab = ttk.Frame(tabs, padding=(14, 14, 14, 10))
        history_tab = ttk.Frame(tabs, padding=14)
        settings_tab = ttk.Frame(tabs, padding=18)

        tabs.add(send_tab, text='  ส่งไฟล์  ')
        tabs.add(history_tab, text='  ประวัติ  ')
        tabs.add(settings_tab, text='  ตั้งค่า / วิธีรับไฟล์  ')
        tabs.bind('<<NotebookTabChanged>>', lambda e: self.history())

        # Send Tab - Files Card
        files_card = ttk.Frame(send_tab, style='Card.TFrame', padding=12)
        files_card.pack(fill='x', pady=(0, 12))

        files_bar = ttk.Frame(files_card, style='Card.TFrame')
        files_bar.pack(fill='x', pady=(0, 8))
        ttk.Label(files_bar, text='ไฟล์และโฟลเดอร์ที่จะส่ง', style='CardHeading.TLabel').pack(side='left')
        self.summary = ttk.Label(files_bar, style='CardMuted.TLabel')
        self.summary.pack(side='left', padx=(10, 0))

        toolbar = ttk.Frame(files_bar, style='Card.TFrame')
        toolbar.pack(side='right')

        self.edit_buttons = []
        btn_add = ttk.Button(toolbar, text='เพิ่มไฟล์', command=self.add_files)
        btn_add.pack(side='left', padx=3)
        self.edit_buttons.append(btn_add)

        btn_folder = ttk.Button(toolbar, text='เพิ่มโฟลเดอร์', command=self.add_folder)
        btn_folder.pack(side='left', padx=3)
        self.edit_buttons.append(btn_folder)

        btn_remove = ttk.Button(toolbar, text='นำออก', command=self.remove_files)
        btn_remove.pack(side='left', padx=3)
        self.edit_buttons.append(btn_remove)

        btn_clear = ttk.Button(toolbar, text='ล้าง', command=self.clear_files)
        btn_clear.pack(side='left', padx=3)
        self.edit_buttons.append(btn_clear)

        list_frame = ttk.Frame(files_card, style='Card.TFrame')
        list_frame.pack(fill='x')
        self.file_list = tk.Listbox(
            list_frame, height=4, selectmode='extended', relief='flat', borderwidth=0,
            highlightthickness=1, highlightcolor=self.colors['border'], highlightbackground=self.colors['border'],
            bg=self.colors['list_bg'], fg=self.colors['list_fg'],
            selectbackground=self.colors['primary'], selectforeground='#ffffff',
            font=self.font_main
        )
        file_scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=file_scroll.set)
        file_scroll.pack(side='right', fill='y')
        self.file_list.pack(side='left', fill='x', expand=True)

        # Send Tab - Target Devices Card
        devices_card = ttk.Frame(send_tab, style='Card.TFrame', padding=12)
        devices_card.pack(fill='both', expand=True)

        device_bar = ttk.Frame(devices_card, style='Card.TFrame')
        device_bar.pack(fill='x', pady=(0, 8))
        ttk.Label(device_bar, text='เลือกเครื่องปลายทาง', style='CardHeading.TLabel').pack(side='left')

        self.refresh_button = ttk.Button(device_bar, text='รีเฟรช', command=self.refresh)
        self.refresh_button.pack(side='right')

        self.only_ready = tk.BooleanVar(value=self.prefs['ready_only'])
        self.filter_button = ttk.Checkbutton(device_bar, text='เฉพาะเครื่องพร้อมรับ', variable=self.only_ready, command=self.filter_changed, style='Card.TCheckbutton')
        self.filter_button.pack(side='right', padx=12)

        self.tree = self.table(devices_card, [
            ('name', 'ชื่อเครื่อง', 230),
            ('ip', 'Tailscale IP', 160),
            ('status', 'สถานะ', 190),
            ('os', 'ระบบ', 95),
            ('last', 'ล่าสุด', 95)
        ])
        self.tree.bind('<<TreeviewSelect>>', lambda e: self.controls())
        self.tree.tag_configure('ready', foreground=self.colors['success'])
        self.tree.tag_configure('online', foreground=self.colors['warning'])
        self.tree.tag_configure('offline', foreground=self.colors['fg_dim'])

        self.device_status = ttk.Label(devices_card, text='กำลังโหลดรายชื่อ…', style='CardMuted.TLabel')
        self.device_status.pack(anchor='w', pady=(8, 0))

        # History Tab
        history_card = ttk.Frame(history_tab, style='Card.TFrame', padding=12)
        history_card.pack(fill='both', expand=True)
        self.history_tree = self.table(history_card, [
            ('time', 'วัน / เวลา', 160),
            ('target', 'เครื่อง', 180),
            ('ip', 'IP', 150),
            ('count', 'สำเร็จ / ทั้งหมด', 110),
            ('result', 'ผล', 110)
        ])
        ttk.Button(history_tab, text='เปิดโฟลเดอร์บันทึก (State Folder)', command=self.open_state).pack(anchor='e', pady=(10, 0))

        # Settings Tab
        settings_card = ttk.Frame(settings_tab, style='Card.TFrame', padding=16)
        settings_card.pack(fill='both', expand=True)

        ttk.Label(settings_card, text='การตั้งค่าการส่งไฟล์', style='CardHeading.TLabel').pack(anchor='w')
        ttk.Label(settings_card, text='เวลาสูงสุดต่อไฟล์ (นาที)', style='Card.TLabel').pack(anchor='w', pady=(14, 4))
        self.minutes = tk.StringVar(value=str(self.prefs['timeout_minutes']))
        self.timeout_combo = ttk.Combobox(settings_card, textvariable=self.minutes, values=(5, 15, 30, 60, 120, 240), state='readonly', width=16)
        self.timeout_combo.pack(anchor='w')

        self.save_button = ttk.Button(settings_card, text='บันทึกการตั้งค่า', command=self.save_settings)
        self.save_button.pack(anchor='w', pady=(12, 16))

        ttk.Separator(settings_card).pack(fill='x', pady=12)

        ttk.Label(settings_card, text='วิธีค้นหาและรับไฟล์ปลายทาง', style='CardHeading.TLabel').pack(anchor='w', pady=(0, 6))
        guide_text = (
            "• Android: ดูการแจ้งเตือน หรือโฟลเดอร์รับที่กำหนดใน Tailscale\n"
            "• Windows / macOS: ตรวจสอบโฟลเดอร์ Downloads หรือการตั้งค่ารับไฟล์ของ Tailscale\n"
            "• Linux: ใช้ตัวรับอัตโนมัติที่ตั้งไว้ หรือรัน tailscale file get <โฟลเดอร์>\n\n"
            "หมายเหตุสำคัญ:\n"
            "- ส่งสำเร็จหมายถึง Tailscale ปลายทางได้รับไฟล์แล้ว ไม่ได้ยืนยันว่าผู้รับเปิดไฟล์\n"
            "- โฟลเดอร์จะถูกส่งเป็น ZIP โดยไม่ลดทอนคุณภาพไฟล์ รูปภาพ หรือวิดีโอ\n"
            "- เครื่องของผู้ใช้อื่น (คนละบัญชี Tailscale) ไม่รองรับการส่งผ่าน Taildrop"
        )
        ttk.Label(settings_card, wraplength=700, justify='left', text=guide_text, style='CardMuted.TLabel').pack(anchor='w', pady=6)

        self.render_files()
        self.history()
        root.after(100, self.drain)
        if autoload:
            root.after(100, self.refresh)

    def table(self, parent, columns):
        frame = ttk.Frame(parent, style='Card.TFrame')
        frame.pack(fill='both', expand=True)
        tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show='headings', selectmode='browse', height=6)
        for key, title, width in columns:
            tree.heading(key, text=title)
            tree.column(key, width=width, minwidth=75)
        scroll = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)
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
                    folders += 1
                    label = '[ZIP โฟลเดอร์] '
                else:
                    total += path.stat().st_size
                    label = ''
            except OSError:
                label = '[ไม่สามารถเข้าถึง] '
            self.file_list.insert('end', f"  {label}{path}")

        if not self.paths:
            self.summary.configure(text='(ยังไม่ได้เลือกไฟล์ — เพิ่มไฟล์ด้านขวา หรือคลิกขวาใน Nautilus)')
        else:
            self.summary.configure(text=f'{len(self.paths)} รายการ · ขนาด {total / 1048576:,.1f} MB' + (f' · {folders} โฟลเดอร์' if folders else ''))
        self.controls()

    def add_files(self):
        for name in filedialog.askopenfilenames(parent=self.root, title='เลือกไฟล์'):
            if Path(name) not in self.paths:
                self.paths.append(Path(name))
        self.render_files()

    def add_folder(self):
        name = filedialog.askdirectory(parent=self.root, title='เลือกโฟลเดอร์ที่จะส่งเป็น ZIP')
        if name and Path(name) not in self.paths:
            self.paths.append(Path(name))
        self.render_files()

    def clear_files(self):
        self.paths.clear()
        self.render_files()

    def remove_files(self):
        for index in reversed(self.file_list.curselection()):
            self.paths.pop(index)
        self.render_files()

    def refresh(self):
        if self.busy or self.refreshing:
            return
        self.refreshing = True
        self.controls()
        self.device_status.configure(text='กำลังตรวจเช็ค Tailscale…')

        def work():
            try:
                self.events.put(('devices', core.discover(core.find_tailscale())))
            except Exception as error:
                self.events.put(('discovery_error', str(error)))

        threading.Thread(target=work, daemon=True).start()

    def render_devices(self):
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        rows = sorted(self.rows.values(), key=lambda r: (not r['ready'], r['ip'] != self.prefs['last_target'], r['name'].casefold()))
        for row in rows:
            if self.only_ready.get() and not row['ready']:
                continue
            if row['ready']:
                status = 'พร้อมรับไฟล์'
                tag = 'ready'
            elif row['online']:
                status = 'ออนไลน์ · ยังรับไม่ได้'
                tag = 'online'
            else:
                status = 'ออฟไลน์'
                tag = 'offline'

            last_text = 'ใช้ล่าสุด' if row['ip'] == self.prefs['last_target'] else ''
            self.tree.insert('', 'end', iid=row['ip'], values=(row['name'], row['ip'], status, row['os'], last_text), tags=(tag,))

        pick = selected[0] if selected else self.prefs['last_target']
        if pick and self.tree.exists(pick):
            self.tree.selection_set(pick)
        ready = sum(r['ready'] for r in rows)
        self.device_status.configure(text=f'พร้อมรับ {ready} / {len(rows)} เครื่อง · ตรวจสอบสถานะก่อนส่ง' if rows else 'ไม่พบเครื่องของคุณ เปิด Tailscale บนปลายทาง แล้วกดรีเฟรช')
        self.controls()

    def filter_changed(self):
        self.prefs['ready_only'] = self.only_ready.get()
        self.persist()
        self.render_devices()

    def persist(self):
        try:
            self.state.save(self.prefs)
        except OSError as error:
            messagebox.showerror(TITLE, str(error), parent=self.root)

    def save_settings(self):
        self.prefs['timeout_minutes'] = int(self.minutes.get())
        self.persist()
        self.status.configure(text='บันทึกการตั้งค่าเรียบร้อยแล้ว')

    def history(self):
        self.history_tree.delete(*self.history_tree.get_children())
        for row in self.state.history():
            try:
                when = datetime.datetime.fromisoformat(row['time']).strftime('%d/%m/%Y %H:%M')
            except (ValueError, TypeError):
                when = str(row['time'])
            self.history_tree.insert('', 'end', values=(when, row['target'], row.get('ip', ''), f"{row['sent']}/{row['total']}", row['result']))

    def open_state(self):
        try:
            if sys.platform == 'win32':
                os.startfile(str(self.state.root))
            else:
                runtime.popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(self.state.root)])
        except OSError as error:
            messagebox.showerror(TITLE, str(error), parent=self.root)

    def send(self):
        selected = self.tree.selection()
        if self.busy or not selected:
            return
        target = self.rows[selected[0]].copy()
        paths = self.paths[:]
        try:
            core.validate(paths)
        except ValueError as error:
            messagebox.showerror(TITLE, str(error), parent=self.root)
            return

        self.busy = True
        self.cancel.clear()
        self.progress['value'] = 0
        self.controls()
        self.status.configure(text='กำลังตรวจเช็คเครื่องปลายทาง…')

        def retry(name, code, sent):
            answer = queue.Queue()
            self.events.put(('retry', (name, code, sent, answer)))
            while True:
                core.check_cancel(self.cancel)
                try:
                    return answer.get(timeout=.15)
                except queue.Empty:
                    pass

        def work():
            try:
                result = core.transfer(
                    core.find_tailscale(), paths, target, self.state, self.cancel,
                    lambda count, text: self.events.put(('progress', (count, len(paths), text))), retry
                )
                self.events.put(('done', (result, len(paths), target)))
            except Exception as error:
                self.events.put(('transfer_error', str(error)))

        threading.Thread(target=work, daemon=True).start()

    def cancel_transfer(self):
        self.cancel.set()
        self.status.configure(text='กำลังหยุดการส่งไฟล์…')
        self.controls()

    def close(self):
        if self.busy:
            if not messagebox.askyesno(TITLE, 'หยุดการส่งและปิดหน้าต่าง?', parent=self.root):
                return
            self.closing = True
            self.cancel_transfer()
        else:
            self.root.destroy()

    def drain(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == 'devices':
                    self.refreshing = False
                    self.rows = {r['ip']: r for r in data}
                    self.render_devices()
                elif kind == 'discovery_error':
                    self.refreshing = False
                    self.rows = {}
                    self.render_devices()
                    self.device_status.configure(text='โหลดรายชื่อไม่สำเร็จ — กดรีเฟรชเพื่อลองใหม่')
                    messagebox.showerror(TITLE, data, parent=self.root)
                elif kind == 'progress':
                    count, total, text = data
                    self.progress['value'] = count * 100 / total
                    self.status.configure(text=f'{text} · สำเร็จ {count}/{total} รายการ')
                elif kind == 'retry':
                    name, code, sent, answer = data
                    value = False if self.cancel.is_set() else messagebox.askretrycancel(
                        TITLE,
                        f'ส่ง {name} ไม่สำเร็จ (รหัส {code})\nส่งสำเร็จแล้ว {sent} รายการ\nลองใหม่เฉพาะไฟล์นี้?\nรายละเอียดอยู่ใน last-transfer.log',
                        parent=self.root
                    )
                    answer.put(value)
                elif kind in ('done', 'transfer_error'):
                    self.busy = False
                    self.prefs = self.state.settings()
                    self.controls()
                    self.history()
                    self.render_devices()
                    if self.closing:
                        self.root.destroy()
                        return
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
    if os.name != 'nt':
        os.umask(0o077)
    root = tk.Tk()
    App(root, paths)
    root.mainloop()
