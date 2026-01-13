#!/bin/bash
''''exec "$(dirname "$0")/venv/bin/python3" "$0" "$@" # '''
"""
Record audio from default input until Ctrl+C.
"""

import signal
import sys
import datetime
import random
import sounddevice as sd
import soundfile as sf
import numpy as np

SAMPLE_RATE = 44100
CHANNELS = 1

recording = []
is_recording = True

# Paragraphs designed to capture varied phonemes, emotions, and speech patterns
PARAGRAPHS = [
    "The old lighthouse keeper walked along the rocky shore every morning, watching the waves crash against the jagged cliffs below. He had spent forty years in this place, through storms and sunshine, through joy and sorrow. The sea was his constant companion, never judging, always present.",

    "Scientists have discovered that the human brain processes music in a fundamentally different way than speech. When we hear a familiar melody, multiple regions light up simultaneously, creating a symphony of neural activity. This explains why certain songs can instantly transport us back to specific moments in our past.",

    "The recipe called for three cups of flour, two eggs, and a pinch of salt. She measured each ingredient carefully, remembering how her grandmother used to bake bread every Sunday morning. The kitchen filled with warmth as the oven preheated, and she smiled at the memories.",

    "Technology continues to reshape our daily lives in unexpected ways. From smartphones that recognize our faces to algorithms that predict our preferences, we're surrounded by invisible intelligence. The question isn't whether machines will change society, but how we'll adapt to these changes.",

    "The forest was quiet except for the rustling of leaves overhead. Shafts of golden sunlight pierced through the canopy, illuminating patches of moss and fern on the forest floor. A deer paused at the edge of a clearing, ears twitching, before bounding silently into the shadows.",

    "Public speaking terrifies most people more than death itself, according to surveys. Yet the ability to communicate clearly and confidently remains one of the most valuable skills anyone can develop. Practice, preparation, and genuine enthusiasm for your subject matter make all the difference.",

    "The jazz quartet played until well past midnight, their improvised melodies weaving through the smoky air of the club. Each musician listened intently to the others, responding and building upon phrases in a musical conversation that had no script. The audience sat transfixed.",

    "Climate researchers warn that the next decade will be critical for addressing environmental challenges. Rising temperatures affect everything from agriculture to wildlife migration patterns. Communities around the world are already implementing innovative solutions, from vertical farms to renewable energy grids.",

    "She opened the dusty book and began to read aloud, her voice filling the empty room. The words were old, written centuries ago by someone whose name had been forgotten. Yet the emotions they conveyed felt as fresh and relevant as if they had been penned yesterday.",

    "The marathon runner crossed the finish line with tears streaming down her face. Four years of training, countless early mornings, and moments of doubt had led to this single achievement. The crowd's cheers washed over her as she realized that the impossible had become possible.",
]


def callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}", file=sys.stderr)
    if is_recording:
        recording.append(indata.copy())


def stop_recording(signum, frame):
    global is_recording
    is_recording = False
    print("\nStopping...")


def main():
    global is_recording

    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"voice_samples/recording_{timestamp}.wav"

    # Pick random paragraphs to read
    paragraphs = random.sample(PARAGRAPHS, min(3, len(PARAGRAPHS)))

    print("=" * 70)
    print("VOICE RECORDING")
    print("=" * 70)
    print()
    print("Read the following paragraphs naturally:")
    print()
    for i, para in enumerate(paragraphs, 1):
        print(f"[{i}]")
        # Word wrap at ~65 chars
        words = para.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 > 65:
                print(f"    {line}")
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            print(f"    {line}")
        print()
    print()
    print("-" * 60)
    print(f"Output: {output_file}")
    print()
    print("Press ENTER to start recording, then Ctrl+C when done.")
    print("-" * 60)

    input()  # Wait for user to press Enter

    # Set up signal handler
    signal.signal(signal.SIGINT, stop_recording)

    # Start recording
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
        print("\n🎙️  RECORDING... (Ctrl+C to stop)\n")
        while is_recording:
            sd.sleep(100)

    # Combine all recorded chunks
    if recording:
        audio_data = np.concatenate(recording, axis=0)
        duration = len(audio_data) / SAMPLE_RATE

        # Write to file
        sf.write(output_file, audio_data, SAMPLE_RATE)
        print(f"\nSaved: {output_file}")
        print(f"Duration: {duration:.2f}s")
    else:
        print("No audio recorded.")


if __name__ == "__main__":
    main()
