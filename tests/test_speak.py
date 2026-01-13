# frozen_string_literal: true
"""Tests for speak.py TTS generation script."""

import os
import sys
import subprocess
import pytest

from conftest import PROJECT_ROOT

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSpeakScriptBasics:
    """Basic tests for speak.py."""

    def test_script_exists(self, project_root):
        """Verify speak.py exists."""
        script_path = os.path.join(project_root, "speak.py")

        assert os.path.exists(script_path)

    def test_script_is_executable(self, project_root):
        """Verify speak.py is executable."""
        script_path = os.path.join(project_root, "speak.py")

        assert os.access(script_path, os.X_OK)

    def test_script_has_docstring(self, project_root):
        """Verify speak.py has a docstring."""
        script_path = os.path.join(project_root, "speak.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert '"""' in content


class TestSpeakConstants:
    """Tests for speak.py constants (without importing torch)."""

    def test_reference_file_in_script(self, project_root):
        """Test REFERENCE_FILE constant is set."""
        script_path = os.path.join(project_root, "speak.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert 'REFERENCE_FILE = "voice_reference.wav"' in content

    def test_output_dir_in_script(self, project_root):
        """Test OUTPUT_DIR constant is set."""
        script_path = os.path.join(project_root, "speak.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert 'OUTPUT_DIR = "spoken_affirmations"' in content


class TestSpeakArgparse:
    """Tests for speak.py argument parsing."""

    def test_has_text_argument(self, project_root):
        """Test that text argument is defined."""
        script_path = os.path.join(project_root, "speak.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert 'add_argument("text"' in content

    def test_has_output_flag(self, project_root):
        """Test that -o/--output flag is defined."""
        script_path = os.path.join(project_root, "speak.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert '"-o"' in content
        assert '"--output"' in content

    def test_has_exaggeration_flag(self, project_root):
        """Test that -e/--exaggeration flag is defined."""
        script_path = os.path.join(project_root, "speak.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert '"-e"' in content
        assert '"--exaggeration"' in content

    def test_has_no_play_flag(self, project_root):
        """Test that --no-play flag is defined."""
        script_path = os.path.join(project_root, "speak.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert '"--no-play"' in content

    def test_exaggeration_default(self, project_root):
        """Test that exaggeration defaults to 0.5."""
        script_path = os.path.join(project_root, "speak.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "default=0.5" in content


class TestSpeakCLI:
    """Tests for speak.py command-line interface."""

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv-chatterbox")),
        reason="venv-chatterbox not set up"
    )
    def test_help_flag(self, project_root):
        """Test --help flag."""
        venv_python = os.path.join(project_root, "venv-chatterbox", "bin", "python3")
        script_path = os.path.join(project_root, "speak.py")

        result = subprocess.run(
            [venv_python, script_path, "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "text" in result.stdout.lower()
        assert "-o" in result.stdout
        assert "--output" in result.stdout
        assert "-e" in result.stdout
        assert "--exaggeration" in result.stdout
        assert "--no-play" in result.stdout

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv-chatterbox")),
        reason="venv-chatterbox not set up"
    )
    def test_fails_without_reference_file(self, project_root, temp_dir):
        """Test that speak.py fails when voice_reference.wav is missing."""
        venv_python = os.path.join(project_root, "venv-chatterbox", "bin", "python3")
        script_path = os.path.join(project_root, "speak.py")

        result = subprocess.run(
            [venv_python, script_path, "Hello world", "--no-play"],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        assert result.returncode == 1
        assert "voice_reference.wav" in result.stdout or "not found" in result.stdout

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv-chatterbox")),
        reason="venv-chatterbox not set up"
    )
    def test_requires_text_argument(self, project_root):
        """Test that text argument is required."""
        venv_python = os.path.join(project_root, "venv-chatterbox", "bin", "python3")
        script_path = os.path.join(project_root, "speak.py")

        result = subprocess.run(
            [venv_python, script_path],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "required" in result.stderr.lower() or "text" in result.stderr.lower()


class TestSpeakIntegration:
    """Integration tests for speak.py (requires model download)."""

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv-chatterbox")),
        reason="venv-chatterbox not set up"
    )
    def test_generates_audio_file(self, project_root, temp_dir, ensure_voice_reference):
        """Test that speak.py generates an audio file."""
        venv_python = os.path.join(project_root, "venv-chatterbox", "bin", "python3")
        script_path = os.path.join(project_root, "speak.py")
        output_path = os.path.join(temp_dir, "output.wav")

        result = subprocess.run(
            [
                venv_python, script_path,
                "Hello, this is a test.",
                "-o", output_path,
                "--no-play"
            ],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        assert result.returncode == 0
        assert os.path.exists(output_path)

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv-chatterbox")),
        reason="venv-chatterbox not set up"
    )
    def test_respects_exaggeration_flag(self, project_root, temp_dir, ensure_voice_reference):
        """Test that exaggeration flag is accepted."""
        venv_python = os.path.join(project_root, "venv-chatterbox", "bin", "python3")
        script_path = os.path.join(project_root, "speak.py")
        output_path = os.path.join(temp_dir, "output.wav")

        result = subprocess.run(
            [
                venv_python, script_path,
                "Hello, this is a test.",
                "-o", output_path,
                "-e", "0.8",
                "--no-play"
            ],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        assert result.returncode == 0
        assert "0.8" in result.stdout
