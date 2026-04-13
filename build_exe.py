#!/usr/bin/env python3
"""Build kakao2notion as standalone Windows executable

Usage:
    python build_exe.py

Requirements:
    pip install pyinstaller
"""

import os
import sys
import subprocess
from pathlib import Path


def build_exe():
    """Build executable using PyInstaller"""

    script_dir = Path(__file__).parent

    # Verify PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    print("🔨 Building kakao2notion.exe...")

    # PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",  # Single executable file
        "--windowed",  # Hide console window (remove for CLI)
        "--name", "kakao2notion",
        "--hidden-import=sklearn",
        "--hidden-import=sklearn.cluster",
        "--hidden-import=sklearn.metrics",
        "--hidden-import=sklearn.feature_extraction",
        "--hidden-import=notion_client",
        "--hidden-import=rich",
        "--hidden-import=click",
        "--hidden-import=prompt_toolkit",
        "--collect-all=rich",
        "--collect-all=prompt_toolkit",
        str(script_dir / "__main__.py"),
    ]

    # Add icon if it exists
    if Path("kakao2notion.ico").exists():
        cmd.insert(6, "kakao2notion.ico")
        cmd.insert(6, "--icon")

    print(f"📦 Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=str(script_dir))

    if result.returncode == 0:
        exe_path = script_dir / "dist" / "kakao2notion.exe"
        if exe_path.exists():
            print(f"\n✅ Build successful!")
            print(f"📁 Executable: {exe_path}")
            print(f"📊 Size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
            print(f"\n🎉 Run with: kakao2notion.exe")
            return True
        else:
            print(f"❌ Executable not found at {exe_path}")
            return False
    else:
        print(f"❌ Build failed with exit code {result.returncode}")
        return False


def create_batch_launcher():
    """Create batch file launcher for easier access"""

    batch_content = """@echo off
REM kakao2notion launcher for Windows
REM Add this directory to PATH or double-click to run

cd /d "%~dp0"
kakao2notion.exe %*
pause
"""

    with open("kakao2notion.bat", "w") as f:
        f.write(batch_content)

    print("✅ Created kakao2notion.bat launcher")


def create_shortcut():
    """Create Windows shortcut (requires pywin32)"""

    try:
        import win32com.client

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut("kakao2notion.lnk")
        shortcut.Targetpath = str(Path.cwd() / "dist" / "kakao2notion.exe")
        shortcut.WorkingDirectory = str(Path.cwd())
        shortcut.IconLocation = str(Path.cwd() / "kakao2notion.ico")
        shortcut.save()

        print("✅ Created kakao2notion.lnk shortcut")
    except Exception as e:
        print(f"⚠️  Could not create shortcut: {e}")


if __name__ == "__main__":
    try:
        # Build exe
        if build_exe():
            # Create launcher files
            create_batch_launcher()

            print("\n" + "="*50)
            print("🎉 Build complete!")
            print("="*50)
            print("\nDistribution files in ./dist/:")
            print("  - kakao2notion.exe       (main executable)")
            print("  - kakao2notion.bat       (batch launcher)")
            print("\nUsage:")
            print("  1. Double-click kakao2notion.exe")
            print("  2. Or run: kakao2notion.exe from terminal")
            print("  3. Or use: kakao2notion.bat (with pause)")
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n❌ Build cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
