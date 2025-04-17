"""
Development Environment Setup Script

This script automates the setup of the development environment using Conda and Poetry.

Usage: python scripts/setup_dev.py [--force] [--skip-precommit]

Creates/updates a Conda environment named 'ai-desktop-assistant' based on environment.yml,
installs Python dependencies using Poetry, and sets up pre-commit hooks.
"""

import os
import subprocess
import sys
import platform
import argparse
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
ENV_NAME = "ai-desktop-assistant-4"
ENV_FILE = PROJECT_ROOT / "environment.yml"
LOCK_FILE = PROJECT_ROOT / "poetry.lock"
PYPROJECT_FILE = PROJECT_ROOT / "pyproject.toml"


def run_command(
    command: list[str],
    cwd: Path = PROJECT_ROOT,
    error_msg: str = "Command failed",
    check: bool = True,
):
    """Runs a command and prints output/errors."""
    print(f"\n▶️ Running: {' '.join(command)}")
    try:
        process = subprocess.run(
            command,
            cwd=str(cwd),
            check=check,  # Raise exception on non-zero exit code if True
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        if process.stdout:
            print(process.stdout)
        if process.stderr:
            # Print stderr even if check=False
            print(f"⚠️ STDERR:\n{process.stderr}", file=sys.stderr)
        print(f"✅ Command finished: {' '.join(command)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {error_msg}")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Return Code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            print(f"STDERR:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print(
            f"❌ Error: Command '{command[0]}' not found. Is it installed and in your PATH?"
        )
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred running command: {' '.join(command)}")
        print(e)
        return False


def check_conda_installed():
    """Checks if Conda is installed and available."""
    print("🔎 Checking for Conda installation...")
    try:
        result = subprocess.run(
            ["conda", "--version"], capture_output=True, text=True, check=True
        )
        print(f"✅ Conda found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Conda not found or not in PATH.")
        print(
            "Please install Miniconda or Anaconda and ensure it's added to your system's PATH."
        )
        print(
            "Installation guide: https://docs.conda.io/projects/conda/en/latest/user-guide/install/"
        )
        return False


def check_poetry_installed():
    """Checks if Poetry is installed and available."""
    # Check within potential conda env first
    print("🔎 Checking for Poetry installation...")
    conda_prefix = os.environ.get("CONDA_PREFIX")
    poetry_cmd = "poetry"
    if conda_prefix:
        # Look in conda env scripts/bin path
        bindir = "Scripts" if platform.system() == "Windows" else "bin"
        conda_poetry = Path(conda_prefix) / bindir / "poetry"
        if conda_poetry.is_file() or (
            platform.system() == "Windows"
            and conda_poetry.with_suffix(".exe").is_file()
        ):
            poetry_cmd = str(conda_poetry)
            print(f"ℹ️ Found Poetry in Conda env: {poetry_cmd}")

    try:
        result = subprocess.run(
            [poetry_cmd, "--version"], capture_output=True, text=True, check=True
        )
        print(f"✅ Poetry found: {result.stdout.strip()}")
        return True, poetry_cmd
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Poetry not found or not in PATH (or Conda env).")
        print(
            "Poetry should be installed via the Conda environment file, but wasn't found."
        )
        print("Ensure 'poetry>=...' is listed under dependencies in environment.yml.")
        return False, "poetry"  # Return default command name


def main():
    parser = argparse.ArgumentParser(
        description="Set up the AI Desktop Assistant development environment."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force update/reinstallation of environment and dependencies.",
    )
    parser.add_argument(
        "--skip-precommit",
        action="store_true",
        help="Skip installation of pre-commit hooks.",
    )
    args = parser.parse_args()

    print("🚀 Starting Development Environment Setup...")

    # 1. Check Prerequisites
    if not check_conda_installed():
        sys.exit(1)

    # 2. Create/Update Conda Environment
    print(f"\n🔄 Setting up Conda environment '{ENV_NAME}' from {ENV_FILE.name}...")
    conda_create_cmd = [
        "conda",
        "env",
        "create",
        "-f",
        str(ENV_FILE),
        "--name",
        ENV_NAME,
    ]
    conda_update_cmd = [
        "conda",
        "env",
        "update",
        "-f",
        str(ENV_FILE),
        "--name",
        ENV_NAME,
        "--prune",
    ]

    # Check if env exists
    try:
        envs_output = subprocess.run(
            ["conda", "env", "list"], capture_output=True, text=True, check=True
        ).stdout
        env_exists = (
            f"\n{ENV_NAME} " in envs_output or f"\n{ENV_NAME}*" in envs_output
        )  # Check for active marker too
    except Exception:
        env_exists = False  # Assume not if command fails

    if not env_exists or args.force:
        print(f"Creating {'or recreating ' if args.force else ''}Conda environment...")
        if not run_command(
            conda_create_cmd,
            error_msg=f"Failed to create Conda environment '{ENV_NAME}'.",
        ):
            # If creation failed but env exists (e.g., partial create), try updating
            if env_exists:
                print(
                    f"⚠️ Creation failed, attempting update for existing env '{ENV_NAME}'..."
                )
                if not run_command(
                    conda_update_cmd,
                    error_msg=f"Failed to update Conda environment '{ENV_NAME}'.",
                ):
                    sys.exit(1)
            else:
                sys.exit(1)
    else:
        print(f"Updating existing Conda environment '{ENV_NAME}'...")
        if not run_command(
            conda_update_cmd,
            error_msg=f"Failed to update Conda environment '{ENV_NAME}'.",
        ):
            sys.exit(1)

    print(f"✅ Conda environment '{ENV_NAME}' is ready.")
    print(f"👉 Activate it using: conda activate {ENV_NAME}")

    # 3. Check Poetry (should be installed by Conda env)
    poetry_ok, poetry_cmd = check_poetry_installed()
    if not poetry_ok:
        print(
            "🚨 Poetry check failed after Conda setup. Please investigate environment.yml."
        )
        sys.exit(1)

    # 4. Install Dependencies with Poetry
    # Note: This should be run *after* activating the conda env usually.
    # However, we can try running poetry from its installed path directly.
    print("\n📦 Installing Python dependencies using Poetry...")
    poetry_install_cmd = [poetry_cmd, "install"]
    if not args.force:
        # Check if lock file matches pyproject - prevents unnecessary installs if up-to-date
        try:
            subprocess.run(
                [poetry_cmd, "lock", "--check"],
                cwd=str(PROJECT_ROOT),
                check=True,
                capture_output=True,
            )
            print("ℹ️ Dependencies are up-to-date with lock file.")
            run_install = False
        except subprocess.CalledProcessError:
            print("⚠️ Lock file out of sync or dependencies missing. Running install.")
            run_install = True
        except FileNotFoundError:
            print("Could not run 'poetry lock --check', proceeding with install.")
            run_install = True
    else:
        print("Forcing dependency installation...")
        run_install = True

    if run_install:
        if not run_command(poetry_install_cmd, error_msg="Poetry install failed."):
            print(
                "🚨 Make sure you have activated the conda environment first if running poetry globally:"
            )
            print(f"conda activate {ENV_NAME}")
            print("Then run: poetry install")
            sys.exit(1)
    print("✅ Python dependencies installed.")

    # 5. Setup Pre-commit Hooks
    if not args.skip_precommit:
        print("\n🎣 Setting up pre-commit hooks...")
        precommit_cmd = [poetry_cmd, "run", "pre-commit", "install"]
        if not run_command(
            precommit_cmd, error_msg="Failed to install pre-commit hooks."
        ):
            print(
                "⚠️ Pre-commit hook setup failed. You can try running it manually after activating the environment:"
            )
            print(f"conda activate {ENV_NAME}")
            print("pre-commit install")
            # Don't exit, just warn
        else:
            print("✅ Pre-commit hooks installed.")
    else:
        print("⏭️ Skipping pre-commit hook installation.")

    print("\n🎉 Development environment setup complete!")
    print(f"👉 Activate the environment using: conda activate {ENV_NAME}")
    print("👉 Start the application using: python -m ai_desktop_assistant.main")


if __name__ == "__main__":
    main()
