# frozen_string_literal: true
"""Shared pytest fixtures for audio-recordings tests."""

import os
import shutil
import tempfile
import pytest
import numpy as np
import soundfile as sf


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
TONE_528HZ_PATH = os.path.join(FIXTURES_DIR, "tone_528hz.wav")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session", autouse=True)
def ensure_voice_reference():
    """Ensure voice_reference.wav exists for integration tests using the test tone."""
    voice_ref_path = os.path.join(PROJECT_ROOT, "voice_reference.wav")
    if not os.path.exists(voice_ref_path):
        shutil.copy(TONE_528HZ_PATH, voice_ref_path)
    yield


@pytest.fixture
def tone_528hz_path():
    """Return path to the 528Hz test tone file."""
    return TONE_528HZ_PATH


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def temp_dir():
    """Create a temporary directory that is cleaned up after the test."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_working_dir(temp_dir):
    """Create a temporary working directory with the expected structure."""
    voice_samples_dir = os.path.join(temp_dir, "voice_samples")
    spoken_affirmations_dir = os.path.join(temp_dir, "spoken_affirmations")
    os.makedirs(voice_samples_dir)
    os.makedirs(spoken_affirmations_dir)

    return {
        "root": temp_dir,
        "voice_samples": voice_samples_dir,
        "spoken_affirmations": spoken_affirmations_dir,
    }


@pytest.fixture
def sample_recording(temp_working_dir):
    """Create a sample recording file in voice_samples/."""
    recording_path = os.path.join(
        temp_working_dir["voice_samples"],
        "recording_20240101_120000.wav"
    )
    shutil.copy(TONE_528HZ_PATH, recording_path)
    return recording_path


@pytest.fixture
def multiple_recordings(temp_working_dir):
    """Create multiple recording files in voice_samples/."""
    paths = []
    for i in range(3):
        recording_path = os.path.join(
            temp_working_dir["voice_samples"],
            f"recording_2024010{i+1}_120000.wav"
        )
        shutil.copy(TONE_528HZ_PATH, recording_path)
        paths.append(recording_path)
    return paths


@pytest.fixture
def voice_reference(temp_working_dir):
    """Create a voice reference file in the temp directory."""
    ref_path = os.path.join(temp_working_dir["root"], "voice_reference.wav")
    shutil.copy(TONE_528HZ_PATH, ref_path)
    return ref_path


@pytest.fixture
def sample_affirmation_clips(temp_working_dir):
    """Create sample affirmation clips in spoken_affirmations/."""
    paths = []
    for i in range(5):
        clip_path = os.path.join(
            temp_working_dir["spoken_affirmations"],
            f"{i+1:02d}_test_affirmation_{i+1}.wav"
        )
        shutil.copy(TONE_528HZ_PATH, clip_path)
        paths.append(clip_path)
    return paths


@pytest.fixture
def messages_file(temp_working_dir):
    """Create a positive_messages.txt file."""
    messages_path = os.path.join(temp_working_dir["root"], "positive_messages.txt")
    messages = [
        "# Test messages file",
        "I am worthy of love.",
        "I am strong and capable.",
        "I deserve happiness.",
    ]
    with open(messages_path, "w") as f:
        f.write("\n".join(messages))
    return messages_path


def generate_tone(frequency, duration, sample_rate=44100):
    """Generate a sine wave tone."""
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    tone = np.sin(2 * np.pi * frequency * t)

    fade_samples = int(0.01 * sample_rate)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    tone[:fade_samples] *= fade_in
    tone[-fade_samples:] *= fade_out

    return tone.astype(np.float32)


@pytest.fixture
def generate_test_wav(temp_dir):
    """Factory fixture to generate test WAV files."""
    def _generate(filename, duration=1.0, frequency=440):
        path = os.path.join(temp_dir, filename)
        tone = generate_tone(frequency, duration)
        sf.write(path, tone, 44100)
        return path
    return _generate
