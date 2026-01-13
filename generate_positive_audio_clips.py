#!/bin/bash
''''exec "$(dirname "$0")/venv-chatterbox/bin/python3" "$0" "$@" # '''
"""
Generate a series of audio files from text strings using your cloned voice.

Usage:
    ./generate_positive_audio_clips.py              # Read from positive_messages.txt
    ./generate_positive_audio_clips.py -n 5         # Sample 5 messages from the file
    ./generate_positive_audio_clips.py "Hi" "Bye"   # Custom strings (bypass file)
    cat messages.txt | ./generate_positive_audio_clips.py   # Read from stdin
"""

import sys
import os
import argparse
import random

# Suppress warnings before importing torch
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# Fix perth watermarker issue
import perth
if perth.PerthImplicitWatermarker is None:
    perth.PerthImplicitWatermarker = perth.DummyWatermarker

import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS


REFERENCE_FILE = "voice_reference.wav"
DEFAULT_OUTPUT_DIR = "spoken_affirmations"
MESSAGES_FILE = "positive_messages.txt"

# Stock positive affirmations (used to generate default file)
STOCK_MESSAGES = [
    "I am worthy of love and respect, exactly as I am.",
    "My voice matters, and what I have to say is important.",
    "I trust myself to handle whatever comes my way.",
    "I am growing stronger and more confident every single day.",
    "I deserve happiness, success, and all the good things life has to offer.",
    "I am enough, just as I am right now.",
    "My mistakes do not define me; they help me grow.",
    "I choose to focus on what I can control and let go of the rest.",
    "I am proud of how far I have come.",
    "I give myself permission to rest and recharge.",
    "My feelings are valid, and I honor them.",
    "I am capable of achieving my goals.",
    "I attract positive energy and positive people.",
    "I am resilient and can overcome any challenge.",
    "I forgive myself for past mistakes and embrace my future.",
    "I am deserving of all the love I give to others.",
    "My potential is limitless.",
    "I am in charge of my own happiness.",
    "I celebrate my unique qualities and strengths.",
    "I am becoming the best version of myself.",
    "I release all doubt and welcome confidence.",
    "I am surrounded by abundance and opportunity.",
    "My contributions make a difference in the world.",
    "I choose peace over worry.",
    "I am brave enough to go after what I want.",
    "I treat myself with kindness and compassion.",
    "I am worthy of my own time and attention.",
    "I trust the timing of my life.",
    "I am grateful for this moment and all it brings.",
    "I let go of comparisons and embrace my own journey.",
    "I am open to new possibilities and experiences.",
    "I speak to myself with encouragement and love.",
    "I am creating a life that feels good on the inside.",
    "I honor my boundaries and respect myself.",
    "I am exactly where I need to be right now.",
]

DEFAULT_SAMPLE_COUNT = 6


def get_device():
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def sanitize_filename(text, max_len=40):
    """Convert text to a safe filename."""
    safe = "".join(c if c.isalnum() or c in " -_" else "" for c in text)
    safe = safe.strip().replace(" ", "_").lower()
    return safe[:max_len] if len(safe) > max_len else safe


def load_messages_from_file(filepath):
    """Load messages from a text file, one per line."""
    messages = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                messages.append(line)
    return messages


def generate_messages_file(filepath):
    """Generate the messages file from stock messages."""
    with open(filepath, 'w') as f:
        f.write("# Positive messages - one per line\n")
        f.write("# Lines starting with # are ignored\n")
        f.write("# Edit this file to customize your affirmations\n\n")
        for msg in STOCK_MESSAGES:
            f.write(msg + "\n")
    print(f"Created {filepath} with {len(STOCK_MESSAGES)} messages.")


def read_from_stdin():
    """Read messages from stdin, one per line."""
    messages = []
    for line in sys.stdin:
        line = line.strip()
        if line and not line.startswith('#'):
            messages.append(line)
    return messages


def get_messages(args):
    """Get messages from stdin, args, file, or prompt to create file."""
    if not sys.stdin.isatty():
        messages = read_from_stdin()
        if messages:
            print(f"Read {len(messages)} messages from stdin")
            return messages

    if args.messages:
        return args.messages

    if os.path.exists(MESSAGES_FILE):
        messages = load_messages_from_file(MESSAGES_FILE)
        if not messages:
            print(f"Error: {MESSAGES_FILE} exists but contains no messages.")
            sys.exit(1)
        print(f"Loaded {len(messages)} messages from {MESSAGES_FILE}")
        return messages

    print(f"{MESSAGES_FILE} not found.")
    response = input("Generate from stock messages? [Y/n] ").strip().lower()

    if response in ('', 'y', 'yes'):
        generate_messages_file(MESSAGES_FILE)
        return load_messages_from_file(MESSAGES_FILE)

    print("No messages to process. Exiting.")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Generate audio files from text strings")
    parser.add_argument("messages", nargs="*", help="Text strings to speak (overrides file)")
    parser.add_argument("-n", "--count", type=int, default=DEFAULT_SAMPLE_COUNT,
                        help=f"Number of messages to sample (default: {DEFAULT_SAMPLE_COUNT}, use -1 for all)")
    parser.add_argument("-o", "--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("-e", "--exaggeration", type=float, default=0.5,
                        help="Emotion exaggeration (0-1, default 0.5)")
    args = parser.parse_args()

    messages = get_messages(args)

    if args.count != -1:
        total = len(messages)
        sample_count = min(args.count, total)
        messages = random.sample(messages, sample_count)
        print(f"Sampled {sample_count} of {total} messages")

    # Check reference file
    if not os.path.exists(REFERENCE_FILE):
        print(f"Error: {REFERENCE_FILE} not found.")
        print("Run ./prepare.py first to create your voice reference.")
        sys.exit(1)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    device = get_device()
    print(f"Device: {device}")
    print(f"Loading model...")

    model = ChatterboxTTS.from_pretrained(device=device)

    print(f"\nGenerating {len(messages)} audio files...\n")

    generated_files = []
    for i, text in enumerate(messages, 1):
        filename = f"{i:02d}_{sanitize_filename(text)}.wav"
        output_path = os.path.join(args.output_dir, filename)

        print(f"[{i}/{len(messages)}] \"{text[:50]}{'...' if len(text) > 50 else ''}\"")

        wav = model.generate(
            text,
            audio_prompt_path=REFERENCE_FILE,
            exaggeration=args.exaggeration,
        )

        ta.save(output_path, wav, model.sr)
        duration = wav.shape[1] / model.sr
        print(f"         -> {filename} ({duration:.1f}s)")
        generated_files.append(output_path)

    print(f"\nDone! Generated {len(generated_files)} files in {args.output_dir}/")


if __name__ == "__main__":
    main()
