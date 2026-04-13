# Building kakao2notion as Windows Executable

Convert kakao2notion into a standalone `.exe` file that doesn't require Python installation.

## Quick Start

```bash
# 1. Clone repo
git clone https://github.com/leehogwang/kakao2notion.git
cd kakao2notion

# 2. Install build tools
pip install -r requirements-build.txt

# 3. Build exe
python build_exe.py

# 4. Output
# ✅ kakao2notion.exe in ./dist/
```

## Requirements

- Python 3.10+ (for building)
- ~500MB free disk space
- Windows 10+ (exe is Windows-only)

## Build Process

### Automatic Build

```bash
python build_exe.py
```

This will:
1. Verify PyInstaller is installed
2. Bundle kakao2notion with all dependencies
3. Create standalone `.exe` file
4. Generate batch launcher script

### Manual Build with PyInstaller

```bash
pip install pyinstaller

pyinstaller \
  --onefile \
  --windowed \
  --name kakao2notion \
  --add-data kakao2notion:kakao2notion \
  --hidden-import=sklearn \
  --hidden-import=sklearn.cluster \
  --hidden-import=sklearn.metrics \
  --hidden-import=notion_client \
  --hidden-import=rich \
  --hidden-import=click \
  --collect-all=rich \
  --collect-all=prompt_toolkit \
  kakao2notion/__main__.py
```

## Output Files

After successful build:

```
dist/
├── kakao2notion.exe          # Main executable (200-300 MB)
└── kakao2notion.exe.manifest # (Windows metadata)

kakao2notion.bat              # Optional batch launcher
```

## Usage

### Double-click to run
```
dist/kakao2notion.exe
```

### From terminal
```bash
# Same directory
.\kakao2notion.exe

# Or from anywhere if added to PATH
kakao2notion.exe
```

### Using batch launcher
```bash
kakao2notion.bat
# Opens with command window and pauses at end
```

## Distribution

### Option 1: Single File
Just distribute `kakao2notion.exe` - it's self-contained!

### Option 2: Installer
Create Windows installer using NSIS:

```bash
pip install pyinstaller-nsis
# Follow NSIS documentation
```

### Option 3: Zip File
```bash
# Create distributable zip
cd dist
zip -r kakao2notion-windows.zip kakao2notion.exe
# Send to users
```

## Troubleshooting

### Build fails with missing imports

```
ImportError: No module named 'sklearn'
```

**Solution:**
```bash
pip install scikit-learn notion-client rich click
python build_exe.py
```

### Executable is very large (300+ MB)

**This is normal!** PyInstaller bundles Python runtime + all dependencies.

To reduce size:
```bash
# Use UPX compression
pip install upx-lzma
pyinstaller --upx-dir=/path/to/upx ...
```

### Antivirus warns about .exe

PyInstaller executables sometimes trigger false positives.

**Solution:**
1. Add folder to antivirus whitelist
2. Build on your own machine (trusted)
3. Sign the executable (requires code signing certificate)

### Can't find config file when running from exe

The exe looks for config in: `~/.kakao2notion/config.json`

Make sure this directory exists:

```bash
mkdir %USERPROFILE%\.kakao2notion
```

## Customization

### Change application icon

1. Create `kakao2notion.ico` (256x256 pixels)
2. Place in project root
3. Build will automatically use it

### Hide console window

The build script uses `--windowed` flag:
- ✅ GUI-only mode (no console window)
- ❌ Can't see output logs

To show console:

```bash
# Remove --windowed from command
pyinstaller --onefile --name kakao2notion kakao2notion/__main__.py
```

### Include additional files

```bash
pyinstaller \
  --add-data "config:config" \
  --add-data "templates:templates" \
  ...
```

## Advanced Usage

### Cross-platform building

To build for macOS/Linux on Windows, use Docker:

```dockerfile
FROM python:3.10-slim
RUN apt-get install -y pyinstaller
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN pyinstaller --onefile kakao2notion/__main__.py
```

### CI/CD Integration

GitHub Actions auto-build:

```yaml
# .github/workflows/build.yml
name: Build Executable
on: [push, release]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements-build.txt
      - run: python build_exe.py
      - uses: actions/upload-artifact@v3
        with:
          name: kakao2notion-exe
          path: dist/kakao2notion.exe
```

### Code Signing (Optional)

Sign the exe for professional distribution:

```bash
signtool sign /f certificate.pfx /p password dist/kakao2notion.exe
```

Requires:
- Code signing certificate (.pfx file)
- Microsoft SignTool (Windows SDK)

## Performance

| Metric | Value |
|--------|-------|
| Startup time | 2-3 seconds (first run) |
| File size | 200-300 MB |
| Runtime memory | 100-150 MB |
| Process | kakao2notion.exe (visible in Task Manager) |

## Verification

```bash
# Check exe is executable
kakao2notion.exe --version

# Test interactive mode
kakao2notion.exe

# Test specific command
kakao2notion.exe test
```

## Common Scenarios

### Scenario 1: Distribute to non-technical users

```bash
# Create installer using NSIS
# Users download installer → click → done
# No terminal needed!
```

### Scenario 2: Corporate deployment

```bash
# Sign exe with company certificate
# Use SCCM or Group Policy for deployment
# Users get official kakao2notion
```

### Scenario 3: Portable version

```bash
# Just exe + batch file
# Put on USB drive
# Run from anywhere
```

### Scenario 4: Quick testing

```bash
# Build once
python build_exe.py

# Share exe with testers
# They run without Python installed
```

## Next Steps

1. Build exe: `python build_exe.py`
2. Test locally: `dist/kakao2notion.exe`
3. Share with others!
4. (Optional) Create installer or sign

Enjoy! 🎉
