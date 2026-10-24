# Windows installer distribution

Players download `VoxelEngineSetup-0.1.0-windows-x64.exe`, run the setup wizard,
and then launch **Voxel Engine** from the Start Menu. A desktop shortcut is optional.
Windows Settings provides the normal uninstall entry. Python is bundled with the
game; players do not install it separately. A compatible OpenGL 3.3 graphics driver
is still required.

## Build with GitHub Actions

1. Push these changes to GitHub.
2. Open **Actions → Build Windows game → Run workflow**.
3. Choose the branch and enter a numeric version such as `0.1.0`.
4. Once the build succeeds, download the **VoxelEngine-installer-windows** artifact.
5. Extract GitHub's artifact ZIP and upload the enclosed **setup EXE** to itch.io
   as the Windows download. Players receive that one installer file.

Pushing a tag such as `v0.1.0` also builds the installer, using the tag as its
version. Three or four numeric version components are supported, each at most
65535. The workflow does not automatically publish to itch.io or GitHub Releases.
The existing portable ZIP remains a separate build artifact.

## How the packaging works

`.github/workflows/build-windows.yml` first runs PyInstaller in `--onedir` mode,
collecting the executable, Python runtime, dependencies, assets, and shaders into
`dist/VoxelEngine`. Inno Setup then packages that whole folder into one installer;
its configuration lives in `installer/windows.iss`.

The installer places the files in `%LOCALAPPDATA%\Programs\VoxelEngine` by default.
It installs for the current user without requesting administrator rights. It
creates the Start Menu shortcut and uninstaller, and optionally a desktop shortcut.
Its application ID stays fixed across versions so subsequent installers recognize
the same application. Close the game before installing an update. Updates are
distributed as another setup EXE; there is no automatic updater.

After compilation, CI silently installs into a temporary directory, verifies the
executable and texture/shader files, then uninstalls and verifies executable
removal. This checks packaging; it does not launch the OpenGL game or replace a
manual test on a Windows PC. Before publishing, test launching from the installed
shortcut, placing/removing blocks, updating an older installation, and uninstalling.

## Build locally on Windows

Install Python 3.12 x64 and Inno Setup 6 (6.3 or newer). From the repository root
in PowerShell:

```powershell
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --clean --noconfirm --onedir --windowed --name VoxelEngine --add-data "assets:assets" --add-data "shaders:shaders" main.py
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" /DAppVersion=0.1.0 installer/windows.iss
```

The output is `dist/installer/VoxelEngineSetup-0.1.0-windows-x64.exe`.
Build outputs are generated files; do not commit them.
