[Setup]
AppId=n0ngXarm.SendToDevice
AppName=Send-to-device
AppVersion=1.0.1
AppPublisher=n0ngXarm
AppPublisherURL=https://github.com/n0ngXarm/Send-to-device
DefaultDirName={localappdata}\Programs\SendToDevice
DefaultGroupName=Send-to-device
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=SendToDevice-1.0.1-windows-x64-setup
SetupIconFile=..\assets\app.ico
UninstallDisplayIcon={app}\SendToDevice.exe
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
WizardStyle=modern
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked
[Files]
Source: "..\dist\SendToDevice\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Send-to-device"; Filename: "{app}\SendToDevice.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Send-to-device"; Filename: "{app}\SendToDevice.exe"; Tasks: desktopicon
Name: "{usersendto}\Send to Device"; Filename: "{app}\SendToDevice.exe"; WorkingDir: "{app}"
[Run]
Filename: "{app}\SendToDevice.exe"; Description: "Open Send-to-device"; Flags: nowait postinstall skipifsilent
