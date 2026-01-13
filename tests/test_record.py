# frozen_string_literal: true
"""Tests for record.py voice recording script."""

import os
import sys
import subprocess
import pytest

from conftest import PROJECT_ROOT

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRecordScriptBasics:
    """Basic tests for record.py."""

    def test_script_exists(self, project_root):
        """Verify record.py exists."""
        script_path = os.path.join(project_root, "record.py")

        assert os.path.exists(script_path)

    def test_script_is_executable(self, project_root):
        """Verify record.py is executable."""
        script_path = os.path.join(project_root, "record.py")

        assert os.access(script_path, os.X_OK)

    def test_script_has_docstring(self, project_root):
        """Verify record.py has a docstring."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert '"""' in content


class TestRecordConstants:
    """Tests for record.py constants."""

    def test_sample_rate_in_script(self, project_root):
        """Test SAMPLE_RATE constant is set."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "SAMPLE_RATE = 44100" in content

    def test_channels_in_script(self, project_root):
        """Test CHANNELS constant is set."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "CHANNELS = 1" in content

    def test_paragraphs_list_exists(self, project_root):
        """Test PARAGRAPHS list exists with content."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "PARAGRAPHS = [" in content
        assert "lighthouse" in content.lower()


class TestRecordImports:
    """Tests for record.py imports."""

    def test_imports_sounddevice(self, project_root):
        """Test that sounddevice is imported."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "import sounddevice" in content

    def test_imports_soundfile(self, project_root):
        """Test that soundfile is imported."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "import soundfile" in content

    def test_imports_numpy(self, project_root):
        """Test that numpy is imported."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "import numpy" in content

    def test_imports_signal(self, project_root):
        """Test that signal is imported for Ctrl+C handling."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "import signal" in content


class TestRecordFunctions:
    """Tests for record.py function definitions."""

    def test_has_callback_function(self, project_root):
        """Test that callback function is defined."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "def callback(" in content

    def test_has_stop_recording_function(self, project_root):
        """Test that stop_recording function is defined."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "def stop_recording(" in content

    def test_has_main_function(self, project_root):
        """Test that main function is defined."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "def main():" in content


class TestRecordOutputPath:
    """Tests for record.py output file naming."""

    def test_output_to_voice_samples_dir(self, project_root):
        """Test that output goes to voice_samples/ directory."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "voice_samples/" in content

    def test_filename_includes_timestamp(self, project_root):
        """Test that filename includes timestamp."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "recording_" in content
        assert "strftime" in content


class TestRecordSignalHandling:
    """Tests for record.py signal handling."""

    def test_handles_sigint(self, project_root):
        """Test that SIGINT (Ctrl+C) is handled."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "signal.SIGINT" in content
        assert "stop_recording" in content


class TestRecordParagraphs:
    """Tests for the PARAGRAPHS content."""

    def test_paragraphs_have_variety(self, project_root):
        """Test that paragraphs cover diverse topics."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        topics = [
            "lighthouse",
            "scientist",
            "recipe",
            "technology",
            "forest",
            "speaking",
            "jazz",
            "climate",
            "book",
            "marathon"
        ]
        found_topics = sum(1 for topic in topics if topic.lower() in content.lower())

        assert found_topics >= 5

    def test_paragraphs_are_readable_length(self, project_root):
        """Test that paragraphs are reasonable length for reading."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "PARAGRAPHS = [" in content
        start = content.find("PARAGRAPHS = [")
        end = content.find("]", start)
        paragraphs_section = content[start:end]

        assert len(paragraphs_section) > 1000


class TestRecordCLI:
    """Tests for record.py command-line behavior."""

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv")),
        reason="venv not set up"
    )
    def test_no_help_flag(self, project_root):
        """Test that record.py doesn't use argparse (no --help)."""
        script_path = os.path.join(project_root, "record.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "argparse" not in content


class TestRecordIntegration:
    """Integration tests for record.py (limited due to interactive nature)."""

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv")),
        reason="venv not set up"
    )
    def test_can_import_script_dependencies(self, project_root):
        """Test that venv has required dependencies."""
        venv_python = os.path.join(project_root, "venv", "bin", "python3")

        result = subprocess.run(
            [venv_python, "-c", "import sounddevice; import soundfile; import numpy"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
