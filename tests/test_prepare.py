# frozen_string_literal: true
"""Tests for prepare.py voice reference creation script."""

import os
import sys
import subprocess
import shutil
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTrainScriptImports:
    """Test that prepare.py can be imported and has expected components."""

    def test_script_exists(self, project_root):
        """Verify prepare.py exists."""
        script_path = os.path.join(project_root, "prepare.py")

        assert os.path.exists(script_path)

    def test_script_is_executable(self, project_root):
        """Verify prepare.py is executable."""
        script_path = os.path.join(project_root, "prepare.py")

        assert os.access(script_path, os.X_OK)


class TestGetRecordings:
    """Tests for the get_recordings function."""

    def test_finds_recording_files(self, temp_working_dir, sample_recording):
        """Test that get_recordings finds recording files."""
        from prepare import get_recordings

        original_dir = os.getcwd()
        os.chdir(temp_working_dir["root"])

        try:
            recordings = get_recordings()

            assert len(recordings) == 1
            assert "recording_" in recordings[0]
        finally:
            os.chdir(original_dir)

    def test_finds_multiple_recordings(self, temp_working_dir, multiple_recordings):
        """Test that get_recordings finds multiple recording files."""
        from prepare import get_recordings

        original_dir = os.getcwd()
        os.chdir(temp_working_dir["root"])

        try:
            recordings = get_recordings()

            assert len(recordings) == 3
        finally:
            os.chdir(original_dir)

    def test_returns_sorted_list(self, temp_working_dir, multiple_recordings):
        """Test that recordings are returned in sorted order."""
        from prepare import get_recordings

        original_dir = os.getcwd()
        os.chdir(temp_working_dir["root"])

        try:
            recordings = get_recordings()

            assert recordings == sorted(recordings)
        finally:
            os.chdir(original_dir)

    def test_ignores_non_recording_files(self, temp_working_dir, tone_528hz_path):
        """Test that non-recording wav files are ignored."""
        from prepare import get_recordings

        other_wav = os.path.join(temp_working_dir["voice_samples"], "other_file.wav")
        shutil.copy(tone_528hz_path, other_wav)

        original_dir = os.getcwd()
        os.chdir(temp_working_dir["root"])

        try:
            recordings = get_recordings()

            assert len(recordings) == 0
        finally:
            os.chdir(original_dir)

    def test_returns_empty_when_no_recordings(self, temp_working_dir):
        """Test that empty list is returned when no recordings exist."""
        from prepare import get_recordings

        original_dir = os.getcwd()
        os.chdir(temp_working_dir["root"])

        try:
            recordings = get_recordings()

            assert recordings == []
        finally:
            os.chdir(original_dir)


class TestTrainConstants:
    """Tests for prepare.py constants."""

    def test_clips_dir_constant(self):
        """Test CLIPS_DIR constant is set correctly."""
        from prepare import CLIPS_DIR

        assert CLIPS_DIR == "voice_samples"

    def test_reference_file_constant(self):
        """Test REFERENCE_FILE constant is set correctly."""
        from prepare import REFERENCE_FILE

        assert REFERENCE_FILE == "voice_reference.wav"

    def test_min_duration_constant(self):
        """Test MIN_DURATION_SEC constant is reasonable."""
        from prepare import MIN_DURATION_SEC

        assert MIN_DURATION_SEC > 0
        assert MIN_DURATION_SEC <= 30

    def test_max_duration_constant(self):
        """Test MAX_DURATION_SEC constant is reasonable."""
        from prepare import MAX_DURATION_SEC

        assert MAX_DURATION_SEC >= 10
        assert MAX_DURATION_SEC <= 60


class TestTrainIntegration:
    """Integration tests for prepare.py."""

    def test_creates_voice_reference(self, temp_working_dir, sample_recording):
        """Test that prepare.py creates a voice_reference.wav file."""
        from prepare import main, REFERENCE_FILE

        original_dir = os.getcwd()
        os.chdir(temp_working_dir["root"])

        try:
            main()

            ref_path = os.path.join(temp_working_dir["root"], REFERENCE_FILE)
            assert os.path.exists(ref_path)
        finally:
            os.chdir(original_dir)

    def test_combines_multiple_recordings(self, temp_working_dir, multiple_recordings):
        """Test that multiple recordings are combined."""
        from prepare import main, REFERENCE_FILE
        from pydub import AudioSegment

        original_dir = os.getcwd()
        os.chdir(temp_working_dir["root"])

        try:
            main()

            ref_path = os.path.join(temp_working_dir["root"], REFERENCE_FILE)
            combined = AudioSegment.from_file(ref_path)

            single_clip = AudioSegment.from_file(multiple_recordings[0])
            assert len(combined) > len(single_clip)
        finally:
            os.chdir(original_dir)

    def test_exits_when_no_recordings(self, temp_working_dir, capsys):
        """Test that prepare.py exits with error when no recordings exist."""
        from prepare import main

        original_dir = os.getcwd()
        os.chdir(temp_working_dir["root"])

        try:
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
        finally:
            os.chdir(original_dir)


class TestTrainCLI:
    """Tests for prepare.py command-line interface."""

    def test_no_argparse_in_script(self, project_root):
        """Test that prepare.py doesn't use argparse."""
        script_path = os.path.join(project_root, "prepare.py")

        with open(script_path, "r") as f:
            content = f.read()

        assert "argparse" not in content
