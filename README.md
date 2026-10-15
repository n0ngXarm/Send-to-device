# Send to Device

แอปส่งไฟล์ระหว่าง **เครื่องของคุณเอง** ผ่าน Tailscale Taildrop รองรับ Linux, Windows และ macOS

- แสดงชื่อเครื่อง **พร้อม IP เสมอ** รองรับเครื่องชื่อซ้ำกัน
- แยกสถานะพร้อมรับ / ออนไลน์แต่รับไม่ได้ / ออฟไลน์ และตรวจซ้ำก่อนส่ง
- เลือกหลายไฟล์หรือโฟลเดอร์ (ส่งโฟลเดอร์เป็น ZIP ไม่ลดคุณภาพ)
- ทำงานเบื้องหลัง หน้าต่างไม่ค้างระหว่างอ่านรายชื่อหรือส่งไฟล์
- หยุดส่งได้ ลองใหม่เฉพาะไฟล์ที่ล้มเหลว และจำปลายทางล่าสุด
- ประวัติการส่ง พร้อม IP และตั้งเวลา 5–240 นาทีต่อไฟล์

## ดาวน์โหลดพร้อมติดตั้ง

ไปที่ [Releases](https://github.com/n0ngXarm/Send-to-device/releases/latest) เลือก ZIP ให้ตรงระบบ แล้ว **แตก ZIP ก่อน**:

| ระบบ | ไฟล์ | วิธีติดตั้ง |
|---|---|---|
| Linux x64 | `Send-to-device-linux-x64.zip` | `sh install-linux.sh` |
| Windows x64 | `Send-to-device-windows-x64.zip` | ดับเบิลคลิก `install-windows.cmd` |
| macOS Apple Silicon | `Send-to-device-macos-arm64.zip` | เปิด `install-macos.command` |
| macOS Intel | `Send-to-device-macos-x64.zip` | เปิด `install-macos.command` |

ไฟล์ release รวม Python/Tk ไว้แล้ว **ไม่ต้องติดตั้ง Python เพิ่ม** แต่ต้องติดตั้ง [Tailscale](https://tailscale.com/download) และเข้าสู่ระบบบนทั้งสองเครื่อง เปิด Taildrop / Send Files ตามนโยบาย tailnet ของคุณก่อน

ตัวติดตั้งลงเฉพาะบัญชีผู้ใช้ ไม่ต้องใช้ sudo/Administrator ไม่แก้ firewall หรือสิทธิ์ Tailscale รองรับ Linux glibc 2.35+ แบบ desktop (X11 หรือ XWayland), Windows 10/11 และ macOS รุ่นที่ Python/Tk กับ Tailscale รองรับ โปรดดูผล CI ของรุ่นนั้นสำหรับ OS ที่ทดสอบจริง

Windows และ macOS builds ยังไม่มีใบรับรอง publisher / Apple notarization ระบบอาจแสดงคำเตือน ดาวน์โหลดเฉพาะ release จาก repository นี้และตรวจสอบแหล่งที่มาก่อนอนุญาตเปิด บน macOS ใช้ System Settings → Privacy & Security → Open Anyway หากถูก Gatekeeper บล็อก ไม่จำเป็นต้องปิดระบบความปลอดภัยทั้งเครื่อง

## ใช้งาน

1. เปิด **Send to Device** จากเมนูแอป
2. เพิ่มไฟล์/โฟลเดอร์ หรือส่ง path จาก command line
3. เลือกเครื่องที่พร้อมรับ ตรวจชื่อและ IP แล้วกด **ส่งไฟล์**

Linux: Nautilus → คลิกขวา → Scripts → **Send-to-Device**; ตัวติดตั้งไม่ลบสคริปต์เก่า `Send-to-Android`

Windows: คลิกขวาไฟล์ → Show more options → Send to → **Send to Device** หรือเปิดจาก Start Menu

macOS: เปิด `~/Applications/Send to Device.app` แล้วเลือกไฟล์ในแอป (ไม่มี Finder Quick Action ในรุ่นนี้)

แถบความคืบหน้าแสดง **จำนวนรายการที่ส่งสำเร็จ** ไม่ใช่เปอร์เซ็นต์ไบต์ของไฟล์ปัจจุบัน คงหน้าต่างไว้จนส่งเสร็จ การหยุดส่งไม่ลบไฟล์ที่ถึงปลายทางแล้ว เมื่อ retry โปรแกรมไม่ส่งไฟล์ก่อนหน้าที่สำเร็จไปซ้ำ

## ไฟล์อยู่ไหนที่ปลายทาง

- Android: ตรวจการแจ้งเตือน / Downloads / โฟลเดอร์รับที่ตั้งในแอป Tailscale
- Windows, macOS: ตรวจ Downloads หรือการตั้งค่ารับของ Tailscale
- Linux: ใช้ตัวรับอัตโนมัติที่ตั้งไว้ หรือรัน `tailscale file get /path/to/receive` (อาจต้องใช้ sudo ตามสิทธิ์)

“ส่งสำเร็จ” หมายถึง Tailscale ปลายทางรับแล้ว ไม่ได้หมายถึงผู้รับเปิดไฟล์ และแอปนี้ไม่ได้ติดตั้งตัวรับอัตโนมัติให้เครื่องอื่น

Taildrop ใช้กับเครื่องของเจ้าของเดียวกัน ลิงก์แชร์เครื่องเพื่อนไม่ทำให้ส่ง Taildrop ให้เพื่อนได้ รุ่นนี้ไม่มี SSH/SFTP และไม่แสดงเครื่องเพื่อนเป็นปลายทางของตัวเอง

อ้างอิง: [เอกสาร Taildrop](https://tailscale.com/docs/features/taildrop)

## ติดตั้งจาก source

ต้องมี Python 3.10+ พร้อม Tk ไม่มี pip dependency สำหรับรันแอป:

```sh
git clone https://github.com/n0ngXarm/Send-to-device.git
cd Send-to-device
python3 installer.py --install
```

- Linux Debian/Ubuntu: `sudo apt install python3 python3-tk`; Fedora: `sudo dnf install python3 python3-tkinter`
- Windows: Python จาก python.org เลือก Tcl/Tk และ Python launcher จากนั้นเปิด `install-windows.cmd`
- macOS: Python จาก python.org ที่มี Tk แล้วเปิด `install-macos.command`

ทดสอบแบบยังไม่ติดตั้ง: `python3 app.py` หรือ `python3 app.py /path/to/file`

## อัปเดต / ถอนการติดตั้ง

ปิดแอปก่อนติดตั้งรุ่นใหม่ ตัวติดตั้งจะอัปเดตไฟล์แอปและคงข้อมูลผู้ใช้ไว้

Source checkout: `python3 installer.py --uninstall` (Windows ใช้ `py -3`)

Bundled download: เรียก executable ใน **โฟลเดอร์ที่แตก ZIP ไว้** พร้อม `--uninstall`:

- Linux: `./SendToDevice/SendToDevice --uninstall`
- Windows: `SendToDevice\SendToDevice.exe --uninstall`
- macOS: `"./Send to Device.app/Contents/MacOS/SendToDevice" --uninstall`

อย่ารันถอนการติดตั้งจาก executable ที่อยู่ในโฟลเดอร์ติดตั้งเองบน Windows เพราะระบบอาจล็อกไฟล์นั้นอยู่

เก็บ settings, history และ `last-transfer.log` แยกจากแอป (ไม่ถูกลบเมื่อ uninstall):

- Linux: `$XDG_STATE_HOME/send-to-device` หรือ `~/.local/state/send-to-device`
- Windows: `%LOCALAPPDATA%\SendToDevice\state`
- macOS: `~/Library/Application Support/SendToDevice/state`

ประวัติและ log อาจมีชื่อไฟล์และ IP ส่วนตัว จัดเก็บเฉพาะเครื่อง ไม่อัปโหลดเข้า GitHub อัตโนมัติ

## ทดสอบและ build

```sh
python3 -m unittest discover -s tests -v
python3 tests/gui_smoke.py  # ต้องมี desktop; Linux headless ใช้ xvfb-run -a
python3 -m pip install pyinstaller==6.20.0
python3 -m PyInstaller --clean --windowed --onedir --name SendToDevice app.py
```

GitHub Actions ทดสอบและ build แบบ native บน Linux, Windows, macOS ARM/Intel ทุก push บน main เมื่อ push tag `v*` จะสร้าง release ZIP หลังทุก platform ผ่านแล้ว ไม่มีการส่งไฟล์จริงระหว่าง CI
