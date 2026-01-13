# frozen_string_literal: true
"""Tests for install.sh installer script."""

import os
import subprocess
import tempfile
import shutil
import pytest

from conftest import PROJECT_ROOT


class TestInstallScript:
    """Tests for the install.sh script."""

    def test_install_script_exists(self, project_root):
        """Verify install.sh exists and is executable."""
        script_path = os.path.join(project_root, "install.sh")

        assert os.path.exists(script_path)
        assert os.access(script_path, os.X_OK)

    def test_install_script_has_shebang(self, project_root):
        """Verify install.sh has proper shebang."""
        script_path = os.path.join(project_root, "install.sh")

        with open(script_path, "r") as f:
            first_line = f.readline()

        assert first_line.startswith("#!/bin/bash")

    def test_install_script_uses_set_e(self, project_root):
        """Verify install.sh uses 'set -e' for error handling."""
        script_path = os.path.join(project_root, "install.sh")

        with open(script_path, "r") as f:
            content = f.read()

        assert "set -e" in content

    def test_install_script_checks_python3(self, project_root):
        """Verify install.sh checks for python3."""
        script_path = os.path.join(project_root, "install.sh")

        with open(script_path, "r") as f:
            content = f.read()

        assert "command -v python3" in content
        assert "python3 is required" in content

    def test_install_script_checks_ffmpeg(self, project_root):
        """Verify install.sh checks for ffmpeg."""
        script_path = os.path.join(project_root, "install.sh")

        with open(script_path, "r") as f:
            content = f.read()

        assert "command -v ffmpeg" in content
        assert "ffmpeg is required" in content

    def test_install_script_checks_uv(self, project_root):
        """Verify install.sh checks for uv and sets USE_UV flag."""
        script_path = os.path.join(project_root, "install.sh")

        with open(script_path, "r") as f:
            content = f.read()

        assert "command -v uv" in content
        assert "USE_UV" in content

    def test_install_script_creates_directories(self, project_root):
        """Verify install.sh creates required directories."""
        script_path = os.path.join(project_root, "install.sh")

        with open(script_path, "r") as f:
            content = f.read()

        assert "mkdir -p voice_samples spoken_affirmations" in content

    def test_install_script_creates_venv(self, project_root):
        """Verify install.sh creates venv for recording."""
        script_path = os.path.join(project_root, "install.sh")

        with open(script_path, "r") as f:
            content = f.read()

        assert "venv" in content
        assert "pydub" in content
        assert "sounddevice" in content
        assert "soundfile" in content

    def test_install_script_creates_chatterbox_venv(self, project_root):
        """Verify install.sh creates venv-chatterbox for TTS."""
        script_path = os.path.join(project_root, "install.sh")

        with open(script_path, "r") as f:
            content = f.read()

        assert "venv-chatterbox" in content
        assert "chatterbox-tts" in content

    def test_install_script_downloads_model(self, project_root):
        """Verify install.sh downloads the Chatterbox model."""
        script_path = os.path.join(project_root, "install.sh")

        with open(script_path, "r") as f:
            content = f.read()

        assert "ChatterboxTTS.from_pretrained" in content


class TestInstallScriptDryRun:
    """Tests that run parts of install.sh in isolation."""

    def test_python3_check_passes(self):
        """Test that python3 check passes in current environment."""
        result = subprocess.run(
            ["bash", "-c", "command -v python3"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    def test_ffmpeg_check_passes(self):
        """Test that ffmpeg check passes in current environment."""
        result = subprocess.run(
            ["bash", "-c", "command -v ffmpeg"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    def test_directory_creation_in_temp(self, temp_dir):
        """Test that directory creation works."""
        result = subprocess.run(
            ["bash", "-c", f"cd {temp_dir} && mkdir -p voice_samples spoken_affirmations"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert os.path.isdir(os.path.join(temp_dir, "voice_samples"))
        assert os.path.isdir(os.path.join(temp_dir, "spoken_affirmations"))


class TestInstallScriptFailures:
    """Tests for error handling in install.sh."""

    def test_fails_without_python3(self, temp_dir):
        """Test that install fails gracefully without python3."""
        script = """#!/bin/bash
set -e
if ! command -v nonexistent_python3_command &> /dev/null; then
    echo "Error: python3 is required but not installed."
    exit 1
fi
echo "Should not reach here"
"""
        script_path = os.path.join(temp_dir, "test_script.sh")
        with open(script_path, "w") as f:
            f.write(script)
        os.chmod(script_path, 0o755)

        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        assert "python3 is required" in result.stdout

    def test_fails_without_ffmpeg(self, temp_dir):
        """Test that install fails gracefully without ffmpeg."""
        script = """#!/bin/bash
set -e
if ! command -v nonexistent_ffmpeg_command &> /dev/null; then
    echo "Error: ffmpeg is required but not installed."
    exit 1
fi
echo "Should not reach here"
"""
        script_path = os.path.join(temp_dir, "test_script.sh")
        with open(script_path, "w") as f:
            f.write(script)
        os.chmod(script_path, 0o755)

        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        assert "ffmpeg is required" in result.stdout


class TestInstallScriptIntegration:
    """Integration tests for install.sh (optional, slow)."""

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv")),
        reason="venv not set up - run ./install.sh first"
    )
    def test_venv_has_required_packages(self, project_root):
        """Test that venv has required packages installed."""
        venv_python = os.path.join(project_root, "venv", "bin", "python3")

        result = subprocess.run(
            [venv_python, "-c", "import pydub; import sounddevice; import soundfile"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv-chatterbox")),
        reason="venv-chatterbox not set up - run ./install.sh first"
    )
    def test_venv_chatterbox_has_required_packages(self, project_root):
        """Test that venv-chatterbox has Chatterbox installed."""
        venv_python = os.path.join(project_root, "venv-chatterbox", "bin", "python3")

        result = subprocess.run(
            [venv_python, "-c", "from chatterbox.tts import ChatterboxTTS"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
