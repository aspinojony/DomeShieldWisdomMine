; 穹盾智矿 Windows 安装包脚本（Inno Setup 6）
; 编译：ISCC.exe /DAPP_VERSION=1.0.0 installer.iss

#ifndef APP_VERSION
  #define APP_VERSION "1.0.0"
#endif

#define AppName       "穹盾智矿"
#define AppNameEn     "DomeShield Wisdom Mine"
#define AppPublisher  "DomeShield"
#define AppURL        "https://github.com/aspinojony/DomeShieldWisdomMine"
#define AppExeName    "穹盾智矿.exe"

[Setup]
AppId={{D0B5E3A2-4F7C-4D6A-9C1A-DOMESHIELD2026}}
AppName={#AppName}
AppVersion={#APP_VERSION}
AppVerName={#AppName} {#APP_VERSION}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=穹盾智矿-Setup-{#APP_VERSION}
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
; 防止 LZMA 在大体积（>3GB onedir + torch）时崩内存
LZMAUseSeparateProcess=yes

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english";    MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "在桌面创建快捷方式"; GroupDescription: "附加任务:"; Flags: checkedonce
Name: "startup";     Description: "开机自启"; GroupDescription: "附加任务:"; Flags: unchecked

[Files]
; 整个 PyInstaller onedir 产物
Source: "dist\DomeShield\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; 用户手册
Source: "用户手册.html"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}";    Filename: "{app}\{#AppExeName}"
Name: "{group}\使用手册";       Filename: "{app}\用户手册.html"
Name: "{group}\卸载 {#AppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{commondesktop}\穹盾智矿-使用手册"; Filename: "{app}\用户手册.html"; Tasks: desktopicon
Name: "{commonstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#AppExeName}"; Description: "立即启动 {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; 卸载时停掉残留进程
Filename: "{cmd}"; Parameters: "/C taskkill /IM ""{#AppExeName}"" /F /T"; Flags: runhidden; RunOnceId: "KillApp"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
