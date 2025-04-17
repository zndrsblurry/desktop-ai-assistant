"""
Release Build Script

This script handles the process of building distributable packages
for the AI Desktop Assistant using PyInstaller.

Usage: python scripts/build_release.py [--target windows|macos|linux] [--clean] [--onedir|--onefile]

Creates an executable bundle in the 'dist' directory.
Requires PyInstaller to be installed in the environment.
"""

import subprocess
import sys
import platform
import shutil
import argparse
from pathlib import Path

# --- Configuration ---
APP_NAME = "AIDesktopAssistant"  # Name for executable/bundle
ENTRY_POINT = "ai_desktop_assistant/main.py"
OUTPUT_DIR = "dist"
BUILD_DIR = "build"  # PyInstaller build cache directory
ICON_PATH_WINDOWS = (
    "ai_desktop_assistant/ui/assets/icons/app_icon.ico"  # Needs .ico for Windows
)
ICON_PATH_MACOS = (
    "ai_desktop_assistant/ui/assets/icons/app_icon.icns"  # Needs .icns for macOS
)
ICON_PATH_LINUX = (
    "ai_desktop_assistant/ui/assets/icons/app_icon.png"  # .png often works for Linux
)

# Add data files/directories needed by the application at runtime
# Paths are relative to the project root
# Format: add-data "source:destination_in_bundle" (use ';' for Win, ':' for Mac/Linux)
# Destination '.' means root of the bundle
INCLUDED_DATA = [
    "ai_desktop_assistant/ui/qml:ai_desktop_assistant/ui/qml",
    "ai_desktop_assistant/ui/assets:ai_desktop_assistant/ui/assets",
    # Add .env.example if needed, but NOT .env
    # ".env.example:.",
    # Add config schema if used
    # "config/schema.json:config",
]

# Add hidden imports if PyInstaller fails to detect them
HIDDEN_IMPORTS = [
    "pynput.keyboard._win32",  # Example for Windows
    "pynput.mouse._win32",  # Example for Windows
    "pynput.keyboard._darwin",  # Example for macOS
    "pynput.mouse._darwin",  # Example for macOS
    "pynput.keyboard._xorg",  # Example for Linux
    "pynput.mouse._xorg",  # Example for Linux
    "pkg_resources.py2_warn",  # Common hidden import issue
    "sklearn.utils._typedefs",  # Examples if using ML libraries
    "sklearn.utils._heap",
    "sklearn.utils._sorting",
    "plyer.platforms.win.notification",  # If using plyer notifications
    "plyer.platforms.macosx.notification",
    "plyer.platforms.linux.notification",
    "qasync",  # Ensure qasync is included
    "langchain_google_genai",  # Ensure provider is included
    # Add others as needed based on build errors
]

# --- Script Logic ---
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def run_command(
    command: list[str], cwd: Path = PROJECT_ROOT, error_msg: str = "Command failed"
):
    """Runs a command and prints output/errors."""
    print(f"\n▶️ Running: {' '.join(command)}")
    try:
        # Use shell=True carefully if needed, but prefer list form
        subprocess.run(
            command,
            cwd=str(cwd),
            check=True,  # Raise exception on non-zero exit code
            stdout=sys.stdout,  # Stream output directly
            stderr=sys.stderr,
            text=True,
            encoding="utf-8",
        )
        print(f"✅ Command finished successfully: {' '.join(command)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {error_msg}")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Return Code: {e.returncode}")
        return False
    except FileNotFoundError:
        print(
            f"❌ Error: Command '{command[0]}' not found. Is PyInstaller installed in your environment?"
        )
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred running command: {' '.join(command)}")
        print(e)
        return False


def check_pyinstaller():
    """Checks if PyInstaller is installed."""
    print("🔎 Checking for PyInstaller...")
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
        print("✅ PyInstaller found.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller not found.")
        print("Please install it in your environment: pip install pyinstaller")
        return False


def clean_build_dirs():
    """Removes previous build artifacts."""
    print("🧹 Cleaning previous build directories...")
    build_path = PROJECT_ROOT / BUILD_DIR
    dist_path = PROJECT_ROOT / OUTPUT_DIR
    spec_file = PROJECT_ROOT / f"{APP_NAME}.spec"

    if build_path.exists():
        print(f"   Removing {build_path}")
        shutil.rmtree(build_path, ignore_errors=True)
    if dist_path.exists():
        print(f"   Removing {dist_path}")
        shutil.rmtree(dist_path, ignore_errors=True)
    if spec_file.exists():
        print(f"   Removing {spec_file}")
        spec_file.unlink()
    print("✅ Clean finished.")


def main():
    parser = argparse.ArgumentParser(
        description="Build distributable packages for AI Desktop Assistant."
    )
    parser.add_argument(
        "--target",
        choices=["windows", "macos", "linux"],
        default=platform.system().lower(),
        help="Target operating system (defaults to current OS).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove previous build/dist directories before building.",
    )
    build_type = parser.add_mutually_exclusive_group()
    build_type.add_argument(
        "--onedir",
        action="store_true",
        help="Build as a directory containing all dependencies (default).",
    )
    build_type.add_argument(
        "--onefile", action="store_true", help="Build as a single executable file."
    )

    args = parser.parse_args()

    print(f"🚀 Starting Release Build for Target: {args.target.upper()}...")

    if not check_pyinstaller():
        sys.exit(1)

    if args.clean:
        clean_build_dirs()

    # Determine PyInstaller options
    pyinstaller_cmd = ["pyinstaller"]

    if args.onefile:
        pyinstaller_cmd.append("--onefile")
        print("ℹ️ Build Type: One File Executable")
    else:  # Default to onedir
        pyinstaller_cmd.append("--onedir")
        print("ℹ️ Build Type: One Directory Bundle")

    # Windowed mode (no console window)
    if args.target == "windows":
        pyinstaller_cmd.append("--windowed")
        icon_path = ICON_PATH_WINDOWS
    elif args.target == "macos":
        pyinstaller_cmd.append("--windowed")  # Also works for macOS bundles
        icon_path = ICON_PATH_MACOS
    else:  # Linux
        # '--windowed' is less common/needed on Linux, console can be useful
        icon_path = ICON_PATH_LINUX

    pyinstaller_cmd.extend(["--name", APP_NAME])

    # Add Icon
    icon_full_path = PROJECT_ROOT / icon_path
    if icon_full_path.exists():
        pyinstaller_cmd.extend(["--icon", str(icon_full_path)])
        print(f"ℹ️ Using icon: {icon_path}")
    else:
        print(f"⚠️ Icon not found at {icon_full_path}. Build will not have an icon.")

    # Add Data Files
    separator = ";" if args.target == "windows" else ":"
    for data in INCLUDED_DATA:
        # Ensure paths are relative to project root for PyInstaller
        source_path = PROJECT_ROOT / data.split(":")[0]
        if source_path.exists():
            # PyInstaller needs paths relative to the spec file location (project root)
            add_data_arg = data.replace(
                "\\", "/"
            )  # Use forward slashes for cross-platform compatibility in arg
            pyinstaller_cmd.extend(["--add-data", f"{add_data_arg}{separator}"])
        else:
            print(f"⚠️ Warning: Data source path not found, skipping: {source_path}")

    # Add Hidden Imports
    for imp in HIDDEN_IMPORTS:
        pyinstaller_cmd.extend(["--hidden-import", imp])

    # Add Entry Point
    pyinstaller_cmd.append(str(PROJECT_ROOT / ENTRY_POINT))

    # Define build directories explicitly
    pyinstaller_cmd.extend(["--distpath", str(PROJECT_ROOT / OUTPUT_DIR)])
    pyinstaller_cmd.extend(["--workpath", str(PROJECT_ROOT / BUILD_DIR)])
    pyinstaller_cmd.extend(["--specpath", str(PROJECT_ROOT)])  # Put spec file in root

    # Add log level for build process debugging if needed
    # pyinstaller_cmd.append('--log-level=DEBUG')

    # Execute PyInstaller
    if not run_command(
        pyinstaller_cmd, error_msg=f"PyInstaller build failed for {args.target}."
    ):
        sys.exit(1)

    print("\n🎉 Release build complete!")
    print(f"Output located in: {PROJECT_ROOT / OUTPUT_DIR}")

    # Post-build steps (optional)
    # - Create ZIP/DMG/Installer
    # - Code signing


if __name__ == "__main__":
    main()
