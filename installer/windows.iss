; Compile after PyInstaller has created dist\VoxelEngine.
; Keep AppId stable across releases so upgrades use the existing installation.
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId=VoxelEngine.Desktop
AppName=Voxel Engine
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\VoxelEngine
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DefaultGroupName=Voxel Engine
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\VoxelEngine.exe
OutputDir=..\dist\installer
OutputBaseFilename=VoxelEngineSetup-{#AppVersion}-windows-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\VoxelEngine\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Voxel Engine"; Filename: "{app}\VoxelEngine.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Voxel Engine"; Filename: "{app}\VoxelEngine.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\VoxelEngine.exe"; WorkingDir: "{app}"; Description: "Launch Voxel Engine"; Flags: nowait postinstall skipifsilent unchecked
