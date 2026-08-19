[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{ARGOS-V3-2-1}}
AppName=Argos
AppVersion=3.2.1
AppPublisher=Gadnic / BIDCOM
DefaultDirName={localappdata}\Argos
PrivilegesRequired=lowest
DefaultGroupName=Argos
AllowNoIcons=yes
CloseApplications=yes
CloseApplicationsFilter=*Argos*

; Output folder and installer name
OutputDir=.\
OutputBaseFilename=Argos_Setup_v3_2_1

Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile=icon.ico
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable and its required dependencies inside dist dir
Source: "dist\Argos\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Argos"; Filename: "{app}\Argos.exe"; IconFilename: "{app}\icon.ico"
Name: "{group}\{cm:UninstallProgram,Argos}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Argos"; Filename: "{app}\Argos.exe"; Tasks: desktopicon; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\Argos.exe"; Description: "{cm:LaunchProgram,Argos}"; Flags: nowait postinstall skipifsilent
