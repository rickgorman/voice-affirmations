#!/bin/bash
''''exec "$(dirname "$0")/venv-chatterbox/bin/python3" "$0" "$@" # '''
"""
Generate speech in your cloned voice using Chatterbox.

Usage:
    ./speak.py "Text to speak"
    ./speak.py "Text to speak" -o output.wav
"""

import sys
import os
import argparse
import datetime
import subprocess

# Suppress warnings before importing torch
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# Fix perth watermarker issue (use dummy if real one unavailable)
import perth
if perth.PerthImplicitWatermarker is None:
    perth.PerthImplicitWatermarker = perth.DummyWatermarker

import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS


REFERENCE_FILE = "voice_reference.wav"
OUTPUT_DIR = "spoken_affirmations"


def get_device():
    """Get best available device."""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main():
    parser = argparse.ArgumentParser(description="Generate speech in your cloned voice")
    parser.add_argument("text", help="Text to speak")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-e", "--exaggeration", type=float, default=0.5,
                        help="Emotion exaggeration (0-1, default 0.5)")
    parser.add_argument("--no-play", action="store_true", help="Don't play audio after generating")
    args = parser.parse_args()

    # Check reference file exists
    if not os.path.exists(REFERENCE_FILE):
        print(f"Error: {REFERENCE_FILE} not found.")
        print("Run ./prepare.py first to create your voice reference.")
        sys.exit(1)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f"speech_{timestamp}.wav")

    device = get_device()
    print(f"Device: {device}")
    print(f"Loading model...")

    model = ChatterboxTTS.from_pretrained(device=device)

    print(f"Generating speech...")
    print(f"  Text: \"{args.text}\"")
    print(f"  Reference: {REFERENCE_FILE}")
    print(f"  Exaggeration: {args.exaggeration}")

    wav = model.generate(
        args.text,
        audio_prompt_path=REFERENCE_FILE,
        exaggeration=args.exaggeration,
    )

    # Save
    ta.save(output_path, wav, model.sr)
    duration = wav.shape[1] / model.sr
    print(f"\nSaved: {output_path} ({duration:.1f}s)")

    # Play
    if not args.no_play:
        print("Playing...")
        subprocess.run(["afplay", output_path])


if __name__ == "__main__":
    main()
