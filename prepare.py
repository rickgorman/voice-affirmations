#!/bin/bash
''''exec "$(dirname "$0")/venv/bin/python3" "$0" "$@" # '''
"""
Prepare voice reference from recordings in voice_samples/.
Chatterbox is zero-shot, so this just selects/combines the best clips.
"""

import os
import glob
import sys
from pydub import AudioSegment


CLIPS_DIR = "voice_samples"
REFERENCE_FILE = "voice_reference.wav"
MIN_DURATION_SEC = 10
MAX_DURATION_SEC = 200


def get_recordings():
    """Get all recording_*.wav files (not tone files), newest first."""
    pattern = os.path.join(CLIPS_DIR, "recording_*.wav")
    return sorted(glob.glob(pattern), reverse=True)


def main():
    recordings = get_recordings()

    if not recordings:
        print(f"No recordings found in {CLIPS_DIR}/")
        print("Run ./record.py to create some voice samples first.")
        sys.exit(1)

    print(f"Found {len(recordings)} recording(s):\n")

    # Load and show durations
    clips = []
    total_duration = 0
    for path in recordings:
        audio = AudioSegment.from_file(path)
        duration = len(audio) / 1000
        total_duration += duration
        clips.append((path, audio, duration))
        print(f"  {os.path.basename(path)}: {duration:.1f}s")

    print(f"\nTotal: {total_duration:.1f}s")

    # Combine clips if needed
    if total_duration < MIN_DURATION_SEC:
        print(f"\nWarning: Total duration ({total_duration:.1f}s) is short.")
        print(f"Recommend at least {MIN_DURATION_SEC}s for good voice cloning.")

    # Combine all clips with small gaps
    print(f"\nCombining into {REFERENCE_FILE}...")
    combined = AudioSegment.empty()
    gap = AudioSegment.silent(duration=500)  # 0.5s gap between clips

    for i, (path, audio, duration) in enumerate(clips):
        if i > 0:
            combined += gap
        combined += audio

    # Trim if too long
    if len(combined) > MAX_DURATION_SEC * 1000:
        print(f"Trimming to {MAX_DURATION_SEC}s (was {len(combined)/1000:.1f}s)")
        combined = combined[:MAX_DURATION_SEC * 1000]

    # Export
    combined.export(REFERENCE_FILE, format="wav")
    final_duration = len(combined) / 1000
    print(f"\nSaved: {REFERENCE_FILE} ({final_duration:.1f}s)")
    print("\nReady! Run: ./speak.py \"Your text here\"")


if __name__ == "__main__":
    main()
