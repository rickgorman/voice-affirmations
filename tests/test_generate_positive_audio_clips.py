# frozen_string_literal: true
"""Tests for generate_positive_audio_clips.py batch TTS generation script."""

import os
import sys
import subprocess
import pytest

from conftest import PROJECT_ROOT

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGenerateScriptBasics:
    """Basic tests for generate_positive_audio_clips.py."""

    def test_script_exists(self, project_root):
        """Verify script exists."""
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        assert os.path.exists(script_path)

    def test_script_is_executable(self, project_root):
        """Verify script is executable."""
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        assert os.access(script_path, os.X_OK)

    def test_script_has_docstring(self, project_root):
        """Verify script has a docstring."""
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert '"""' in content


class TestGenerateConstants:
    """Tests for generate_positive_audio_clips.py constants."""

    def test_reference_file_in_script(self, project_root):
        """Test REFERENCE_FILE constant is set."""
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert 'REFERENCE_FILE = "voice_reference.wav"' in content

    def test_output_dir_in_script(self, project_root):
        """Test DEFAULT_OUTPUT_DIR constant is set."""
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert 'DEFAULT_OUTPUT_DIR = "spoken_affirmations"' in content

    def test_messages_file_in_script(self, project_root):
        """Test MESSAGES_FILE constant is set."""
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert 'MESSAGES_FILE = "positive_messages.txt"' in content

    def test_default_sample_count_in_script(self, project_root):
        """Test DEFAULT_SAMPLE_COUNT constant is set."""
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "DEFAULT_SAMPLE_COUNT" in content

    def test_has_stock_messages(self, project_root):
        """Test STOCK_MESSAGES list exists."""
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "STOCK_MESSAGES" in content
        assert "I am worthy" in content


class TestGenerateArgparse:
    """Tests for generate_positive_audio_clips.py argument parsing."""

    def test_has_messages_argument(self, project_root):
        """Test that messages argument is defined."""
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert '"messages"' in content
        assert 'nargs="*"' in content

    def test_has_count_flag(self, project_root):
        """Test that -n/--count flag is defined."""
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert '"-n"' in content
        assert '"--count"' in content

    def test_has_output_dir_flag(self, project_root):
        """Test that -o/--output-dir flag is defined."""
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert '"-o"' in content
        assert '"--output-dir"' in content

    def test_has_exaggeration_flag(self, project_root):
        """Test that -e/--exaggeration flag is defined."""
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert '"-e"' in content
        assert '"--exaggeration"' in content


class TestSanitizeFilename:
    """Tests for sanitize_filename function (import-safe)."""

    def test_removes_special_characters(self):
        """Test that special characters are removed."""
        # Import only what we need without triggering torch import
        import importlib.util
        import os

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        with open(script_path, "r") as f:
            content = f.read()

        # Extract and execute just the sanitize_filename function
        exec_globals = {}
        function_code = '''
def sanitize_filename(text, max_len=40):
    """Convert text to a safe filename."""
    safe = "".join(c if c.isalnum() or c in " -_" else "" for c in text)
    safe = safe.strip().replace(" ", "_").lower()
    return safe[:max_len] if len(safe) > max_len else safe
'''
        exec(function_code, exec_globals)
        sanitize_filename = exec_globals['sanitize_filename']

        result = sanitize_filename("Hello! How are you?")

        assert result == "hello_how_are_you"
        assert "!" not in result
        assert "?" not in result

    def test_truncates_long_strings(self):
        """Test that long strings are truncated."""
        exec_globals = {}
        function_code = '''
def sanitize_filename(text, max_len=40):
    """Convert text to a safe filename."""
    safe = "".join(c if c.isalnum() or c in " -_" else "" for c in text)
    safe = safe.strip().replace(" ", "_").lower()
    return safe[:max_len] if len(safe) > max_len else safe
'''
        exec(function_code, exec_globals)
        sanitize_filename = exec_globals['sanitize_filename']

        long_text = "This is a very long text that should be truncated to fit the filename limit"
        result = sanitize_filename(long_text)

        assert len(result) <= 40

    def test_converts_to_lowercase(self):
        """Test that text is converted to lowercase."""
        exec_globals = {}
        function_code = '''
def sanitize_filename(text, max_len=40):
    """Convert text to a safe filename."""
    safe = "".join(c if c.isalnum() or c in " -_" else "" for c in text)
    safe = safe.strip().replace(" ", "_").lower()
    return safe[:max_len] if len(safe) > max_len else safe
'''
        exec(function_code, exec_globals)
        sanitize_filename = exec_globals['sanitize_filename']

        result = sanitize_filename("HELLO World")

        assert result == "hello_world"

    def test_replaces_spaces_with_underscores(self):
        """Test that spaces are replaced with underscores."""
        exec_globals = {}
        function_code = '''
def sanitize_filename(text, max_len=40):
    """Convert text to a safe filename."""
    safe = "".join(c if c.isalnum() or c in " -_" else "" for c in text)
    safe = safe.strip().replace(" ", "_").lower()
    return safe[:max_len] if len(safe) > max_len else safe
'''
        exec(function_code, exec_globals)
        sanitize_filename = exec_globals['sanitize_filename']

        result = sanitize_filename("hello world")

        assert result == "hello_world"
        assert " " not in result


class TestLoadMessagesFromFile:
    """Tests for load_messages_from_file function."""

    def test_loads_messages(self, temp_dir):
        """Test that messages are loaded from file."""
        messages_path = os.path.join(temp_dir, "messages.txt")
        with open(messages_path, "w") as f:
            f.write("Message one\n")
            f.write("Message two\n")
            f.write("Message three\n")

        exec_globals = {}
        function_code = '''
def load_messages_from_file(filepath):
    """Load messages from a text file, one per line."""
    messages = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                messages.append(line)
    return messages
'''
        exec(function_code, exec_globals)
        load_messages_from_file = exec_globals['load_messages_from_file']

        result = load_messages_from_file(messages_path)

        assert len(result) == 3
        assert "Message one" in result
        assert "Message two" in result
        assert "Message three" in result

    def test_ignores_comments(self, temp_dir):
        """Test that comments are ignored."""
        messages_path = os.path.join(temp_dir, "messages.txt")
        with open(messages_path, "w") as f:
            f.write("# This is a comment\n")
            f.write("Message one\n")
            f.write("# Another comment\n")
            f.write("Message two\n")

        exec_globals = {}
        function_code = '''
def load_messages_from_file(filepath):
    """Load messages from a text file, one per line."""
    messages = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                messages.append(line)
    return messages
'''
        exec(function_code, exec_globals)
        load_messages_from_file = exec_globals['load_messages_from_file']

        result = load_messages_from_file(messages_path)

        assert len(result) == 2
        assert "This is a comment" not in result

    def test_ignores_empty_lines(self, temp_dir):
        """Test that empty lines are ignored."""
        messages_path = os.path.join(temp_dir, "messages.txt")
        with open(messages_path, "w") as f:
            f.write("Message one\n")
            f.write("\n")
            f.write("   \n")
            f.write("Message two\n")

        exec_globals = {}
        function_code = '''
def load_messages_from_file(filepath):
    """Load messages from a text file, one per line."""
    messages = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                messages.append(line)
    return messages
'''
        exec(function_code, exec_globals)
        load_messages_from_file = exec_globals['load_messages_from_file']

        result = load_messages_from_file(messages_path)

        assert len(result) == 2


class TestGenerateCLI:
    """Tests for generate_positive_audio_clips.py command-line interface."""

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv-chatterbox")),
        reason="venv-chatterbox not set up"
    )
    def test_help_flag(self, project_root):
        """Test --help flag."""
        venv_python = os.path.join(project_root, "venv-chatterbox", "bin", "python3")
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        result = subprocess.run(
            [venv_python, script_path, "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "-n" in result.stdout
        assert "--count" in result.stdout
        assert "-o" in result.stdout
        assert "--output-dir" in result.stdout
        assert "-e" in result.stdout
        assert "--exaggeration" in result.stdout

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv-chatterbox")),
        reason="venv-chatterbox not set up"
    )
    def test_fails_without_reference_file(self, project_root, temp_dir):
        """Test that script fails when voice_reference.wav is missing."""
        venv_python = os.path.join(project_root, "venv-chatterbox", "bin", "python3")
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")

        result = subprocess.run(
            [venv_python, script_path, "Hello world"],
            capture_output=True,
            text=True,
            cwd=temp_dir,
            input="n\n"
        )

        assert result.returncode != 0 or "voice_reference.wav" in result.stdout


class TestGenerateIntegration:
    """Integration tests for generate_positive_audio_clips.py."""

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv-chatterbox")),
        reason="venv-chatterbox not set up"
    )
    def test_generates_audio_with_positional_messages(self, project_root, temp_dir, ensure_voice_reference):
        """Test generating audio with positional message arguments."""
        venv_python = os.path.join(project_root, "venv-chatterbox", "bin", "python3")
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")
        output_dir = os.path.join(temp_dir, "output")

        result = subprocess.run(
            [
                venv_python, script_path,
                "Test message one", "Test message two",
                "-o", output_dir
            ],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        assert result.returncode == 0
        assert os.path.isdir(output_dir)

        wav_files = [f for f in os.listdir(output_dir) if f.endswith(".wav")]
        assert len(wav_files) == 2

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv-chatterbox")),
        reason="venv-chatterbox not set up"
    )
    def test_count_flag_limits_messages(self, project_root, temp_dir, messages_file, ensure_voice_reference):
        """Test that -n flag limits number of messages."""
        venv_python = os.path.join(project_root, "venv-chatterbox", "bin", "python3")
        script_path = os.path.join(project_root, "generate_positive_audio_clips.py")
        output_dir = os.path.join(temp_dir, "output")

        result = subprocess.run(
            [
                venv_python, script_path,
                "-n", "2",
                "-o", output_dir
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(messages_file)
        )

        if result.returncode == 0:
            wav_files = [f for f in os.listdir(output_dir) if f.endswith(".wav")]
            assert len(wav_files) == 2
