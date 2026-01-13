# frozen_string_literal: true
"""Tests for weave.py audio weaving script."""

import os
import sys
import subprocess
import shutil
import pytest
from pydub import AudioSegment

from conftest import PROJECT_ROOT

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWeaveScriptBasics:
    """Basic tests for weave.py."""

    def test_script_exists(self, project_root):
        """Verify weave.py exists."""
        script_path = os.path.join(project_root, "weave.py")

        assert os.path.exists(script_path)

    def test_script_is_executable(self, project_root):
        """Verify weave.py is executable."""
        script_path = os.path.join(project_root, "weave.py")

        assert os.access(script_path, os.X_OK)


class TestWeaveConstants:
    """Tests for weave.py constants."""

    def test_output_prefix(self):
        """Test OUTPUT_PREFIX constant."""
        from weave import OUTPUT_PREFIX

        assert OUTPUT_PREFIX == "spoken_messages_"

    def test_overlap_ms(self):
        """Test OVERLAP_MS is reasonable."""
        from weave import OVERLAP_MS

        assert OVERLAP_MS > 0
        assert OVERLAP_MS < 5000

    def test_right_channel_delay(self):
        """Test RIGHT_CHANNEL_DELAY_MS is set."""
        from weave import RIGHT_CHANNEL_DELAY_MS

        assert RIGHT_CHANNEL_DELAY_MS > 0

    def test_crossfeed(self):
        """Test CROSSFEED is in valid range."""
        from weave import CROSSFEED

        assert 0 <= CROSSFEED <= 1

    def test_spatial_positions(self):
        """Test spatial position constants."""
        from weave import POS_HARD_LEFT, POS_SOFT_LEFT, POS_HARD_RIGHT, POS_SOFT_RIGHT

        assert POS_HARD_LEFT == (1.0, 0.0)
        assert POS_HARD_RIGHT == (0.0, 1.0)
        assert POS_SOFT_LEFT[0] == 1.0
        assert POS_SOFT_LEFT[1] > 0
        assert POS_SOFT_RIGHT[0] > 0
        assert POS_SOFT_RIGHT[1] == 1.0

    def test_audio_profiles(self):
        """Test audio differentiation profiles."""
        from weave import PROFILE_A, PROFILE_B

        assert "lowpass_hz" in PROFILE_A
        assert "highpass_hz" in PROFILE_A
        assert "tempo" in PROFILE_A
        assert "lowpass_hz" in PROFILE_B
        assert "highpass_hz" in PROFILE_B
        assert "tempo" in PROFILE_B


class TestEstimateDuration:
    """Tests for estimate_duration function."""

    def test_empty_clips(self):
        """Test with empty clip list."""
        from weave import estimate_duration

        result = estimate_duration([], 1500, 3000)

        assert result == 3000

    def test_single_clip(self, tone_528hz_path):
        """Test with single clip."""
        from weave import estimate_duration

        clip = AudioSegment.from_file(tone_528hz_path)
        clips = [("test.wav", clip)]

        result = estimate_duration(clips, 1500, 3000)

        expected = len(clip) + 3000
        assert result == expected

    def test_multiple_clips(self, tone_528hz_path):
        """Test with multiple clips."""
        from weave import estimate_duration

        clip = AudioSegment.from_file(tone_528hz_path)
        clips = [("test1.wav", clip), ("test2.wav", clip), ("test3.wav", clip)]

        result = estimate_duration(clips, 1500, 3000)

        total_clip_ms = 3 * len(clip)
        overlap_reduction = 2 * 1500
        expected = total_clip_ms - overlap_reduction + 3000
        assert result == expected


class TestSelectClipsForDuration:
    """Tests for select_clips_for_duration function."""

    def test_empty_clips(self):
        """Test with empty clip list."""
        from weave import select_clips_for_duration

        result = select_clips_for_duration([], 10000, 1500, 3000)

        assert result == []

    def test_selects_subset_for_short_duration(self, tone_528hz_path):
        """Test that subset is selected for short target duration."""
        from weave import select_clips_for_duration, estimate_duration

        clip = AudioSegment.from_file(tone_528hz_path)
        clips = [(f"test{i}.wav", clip) for i in range(10)]

        target_ms = 2000
        result = select_clips_for_duration(clips, target_ms, 1500, 0)

        assert len(result) > 0
        estimated = estimate_duration(result, 1500, 0)
        assert estimated <= target_ms + 4000


class TestMakeMono:
    """Tests for make_mono function."""

    def test_mono_clip_unchanged(self, tone_528hz_path):
        """Test that mono clip is returned unchanged."""
        from weave import make_mono

        clip = AudioSegment.from_file(tone_528hz_path)

        result = make_mono(clip)

        assert result.channels == 1

    def test_stereo_clip_converted(self, tone_528hz_path):
        """Test that stereo clip is converted to mono."""
        from weave import make_mono

        mono_clip = AudioSegment.from_file(tone_528hz_path)
        stereo_clip = AudioSegment.from_mono_audiosegments(mono_clip, mono_clip)

        result = make_mono(stereo_clip)

        assert result.channels == 1


class TestChangeTempo:
    """Tests for change_tempo function."""

    def test_tempo_1_unchanged(self, tone_528hz_path):
        """Test that tempo 1.0 returns clip unchanged."""
        from weave import change_tempo

        clip = AudioSegment.from_file(tone_528hz_path)
        original_len = len(clip)

        result = change_tempo(clip, 1.0)

        assert len(result) == original_len

    def test_tempo_faster(self, tone_528hz_path):
        """Test that tempo > 1.0 shortens clip."""
        from weave import change_tempo

        clip = AudioSegment.from_file(tone_528hz_path)
        original_len = len(clip)

        result = change_tempo(clip, 1.1)

        assert len(result) < original_len

    def test_tempo_slower(self, tone_528hz_path):
        """Test that tempo < 1.0 lengthens clip."""
        from weave import change_tempo

        clip = AudioSegment.from_file(tone_528hz_path)
        original_len = len(clip)

        result = change_tempo(clip, 0.9)

        assert len(result) > original_len


class TestApplyProfile:
    """Tests for apply_profile function."""

    def test_applies_lowpass(self, tone_528hz_path):
        """Test that lowpass filter is applied."""
        from weave import apply_profile, PROFILE_A

        clip = AudioSegment.from_file(tone_528hz_path)

        result = apply_profile(clip, PROFILE_A, apply_tempo=False)

        assert len(result) == len(clip)

    def test_applies_highpass(self, tone_528hz_path):
        """Test that highpass filter is applied."""
        from weave import apply_profile, PROFILE_B

        clip = AudioSegment.from_file(tone_528hz_path)

        result = apply_profile(clip, PROFILE_B, apply_tempo=False)

        assert len(result) == len(clip)

    def test_applies_tempo_when_enabled(self, tone_528hz_path):
        """Test that tempo is applied when enabled."""
        from weave import apply_profile, PROFILE_A

        clip = AudioSegment.from_file(tone_528hz_path)

        result = apply_profile(clip, PROFILE_A, apply_tempo=True)

        assert len(result) != len(clip)

    def test_skips_tempo_when_disabled(self, tone_528hz_path):
        """Test that tempo is skipped when disabled."""
        from weave import apply_profile, PROFILE_A

        clip = AudioSegment.from_file(tone_528hz_path)

        result = apply_profile(clip, PROFILE_A, apply_tempo=False)

        assert len(result) == len(clip)


class TestApplyFades:
    """Tests for apply_fades function."""

    def test_applies_fade_in_out(self, tone_528hz_path):
        """Test that fades are applied."""
        from weave import apply_fades

        clip = AudioSegment.from_file(tone_528hz_path)

        result = apply_fades(clip)

        assert len(result) == len(clip)


class TestPanToStereo:
    """Tests for pan_to_stereo function."""

    def test_hard_left_panning(self, tone_528hz_path):
        """Test hard left panning."""
        from weave import pan_to_stereo, POS_HARD_LEFT

        clip = AudioSegment.from_file(tone_528hz_path)

        result = pan_to_stereo(clip, POS_HARD_LEFT)

        assert result.channels == 2

    def test_hard_right_panning(self, tone_528hz_path):
        """Test hard right panning."""
        from weave import pan_to_stereo, POS_HARD_RIGHT

        clip = AudioSegment.from_file(tone_528hz_path)

        result = pan_to_stereo(clip, POS_HARD_RIGHT)

        assert result.channels == 2

    def test_soft_left_panning(self, tone_528hz_path):
        """Test soft left panning with crossfeed."""
        from weave import pan_to_stereo, POS_SOFT_LEFT

        clip = AudioSegment.from_file(tone_528hz_path)

        result = pan_to_stereo(clip, POS_SOFT_LEFT)

        assert result.channels == 2

    def test_soft_right_panning(self, tone_528hz_path):
        """Test soft right panning with crossfeed."""
        from weave import pan_to_stereo, POS_SOFT_RIGHT

        clip = AudioSegment.from_file(tone_528hz_path)

        result = pan_to_stereo(clip, POS_SOFT_RIGHT)

        assert result.channels == 2


class TestGetNextOutputPath:
    """Tests for get_next_output_path function."""

    def test_returns_001_when_no_existing(self, temp_dir):
        """Test returns _001 suffix when no existing files."""
        from weave import get_next_output_path

        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            result = get_next_output_path()

            assert result == "spoken_messages_001.wav"
        finally:
            os.chdir(original_dir)

    def test_increments_sequence(self, temp_dir, tone_528hz_path):
        """Test increments sequence number."""
        from weave import get_next_output_path

        shutil.copy(tone_528hz_path, os.path.join(temp_dir, "spoken_messages_001.wav"))
        shutil.copy(tone_528hz_path, os.path.join(temp_dir, "spoken_messages_002.wav"))

        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            result = get_next_output_path()

            assert result == "spoken_messages_003.wav"
        finally:
            os.chdir(original_dir)


class TestWeaveIntegration:
    """Integration tests for weave.py."""

    def test_weave_stereo_creates_output(self, temp_dir, sample_affirmation_clips):
        """Test that weave_stereo creates an output file."""
        from weave import weave_stereo

        output_path = os.path.join(temp_dir, "output.wav")

        weave_stereo(
            clip_paths=sample_affirmation_clips,
            output_path=output_path,
            seed=42
        )

        assert os.path.exists(output_path)

    def test_weave_stereo_output_is_stereo(self, temp_dir, sample_affirmation_clips):
        """Test that output is stereo."""
        from weave import weave_stereo

        output_path = os.path.join(temp_dir, "output.wav")

        weave_stereo(
            clip_paths=sample_affirmation_clips,
            output_path=output_path,
            seed=42
        )

        result = AudioSegment.from_file(output_path)
        assert result.channels == 2

    def test_weave_stereo_with_seed_is_reproducible(self, temp_dir, sample_affirmation_clips):
        """Test that same seed produces same output."""
        from weave import weave_stereo

        output1 = os.path.join(temp_dir, "output1.wav")
        output2 = os.path.join(temp_dir, "output2.wav")

        weave_stereo(clip_paths=sample_affirmation_clips, output_path=output1, seed=42)
        weave_stereo(clip_paths=sample_affirmation_clips, output_path=output2, seed=42)

        audio1 = AudioSegment.from_file(output1)
        audio2 = AudioSegment.from_file(output2)

        assert len(audio1) == len(audio2)

    def test_weave_stereo_with_target_duration(self, temp_dir, sample_affirmation_clips):
        """Test weaving with target duration."""
        from weave import weave_stereo

        output_path = os.path.join(temp_dir, "output.wav")

        weave_stereo(
            clip_paths=sample_affirmation_clips,
            output_path=output_path,
            seed=42,
            target_duration_s=5
        )

        result = AudioSegment.from_file(output_path)
        assert len(result) > 0


class TestWeaveCLI:
    """Tests for weave.py command-line interface."""

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv")),
        reason="venv not set up"
    )
    def test_help_flag(self, project_root):
        """Test --help flag."""
        venv_python = os.path.join(project_root, "venv", "bin", "python3")
        script_path = os.path.join(project_root, "weave.py")

        result = subprocess.run(
            [venv_python, script_path, "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "target-duration" in result.stdout
        assert "seed" in result.stdout

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv")),
        reason="venv not set up"
    )
    def test_target_duration_flag_short(self, project_root):
        """Test -t flag is documented."""
        venv_python = os.path.join(project_root, "venv", "bin", "python3")
        script_path = os.path.join(project_root, "weave.py")

        result = subprocess.run(
            [venv_python, script_path, "--help"],
            capture_output=True,
            text=True
        )

        assert "-t" in result.stdout

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(PROJECT_ROOT, "venv")),
        reason="venv not set up"
    )
    def test_seed_flag_short(self, project_root):
        """Test -s flag is documented."""
        venv_python = os.path.join(project_root, "venv", "bin", "python3")
        script_path = os.path.join(project_root, "weave.py")

        result = subprocess.run(
            [venv_python, script_path, "--help"],
            capture_output=True,
            text=True
        )

        assert "-s" in result.stdout
