#!/usr/bin/env python3
"""Generate a 528Hz test tone file for use in tests."""

import numpy as np
import soundfile as sf
import os

SAMPLE_RATE = 44100
DURATION_SEC = 1.0
FREQUENCY_HZ = 528


def generate_tone(frequency, duration, sample_rate):
    """Generate a sine wave tone."""
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    # Apply fade in/out to avoid clicks
    tone = np.sin(2 * np.pi * frequency * t)

    # Apply 10ms fade in/out
    fade_samples = int(0.01 * sample_rate)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    tone[:fade_samples] *= fade_in
    tone[-fade_samples:] *= fade_out

    return tone.astype(np.float32)


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "tone_528hz.wav")

    tone = generate_tone(FREQUENCY_HZ, DURATION_SEC, SAMPLE_RATE)
    sf.write(output_path, tone, SAMPLE_RATE)
    print(f"Generated: {output_path} ({DURATION_SEC}s @ {FREQUENCY_HZ}Hz)")
