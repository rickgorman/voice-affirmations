# Voice Affirmations

Clone your voice and generate personalized audio affirmations that play as an immersive stereo soundscape. Uses [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) for zero-shot voice cloning.

## Scripts

### `./install.sh`
Sets up Python virtual environments and downloads the Chatterbox model.

```bash
./install.sh
```

Run this once after cloning. Requires `python3` and `ffmpeg`.

---

### `./record.py`
Records your voice reading randomized paragraphs. Creates samples in `voice_samples/`.

```bash
./record.py
```

Press Enter to start, Ctrl+C to stop. Record 15-30 seconds of natural speech for best results.

---

### `./prepare.py`
Combines your recordings into a single voice reference file.

```bash
./prepare.py
```

Run after recording. Creates `voice_reference.wav` used by the TTS model.

---

### `./speak.py`
Generates a single audio clip in your cloned voice. Good for testing or one-off messages.

```bash
./speak.py "Your text here"
./speak.py "Hello world" -o custom_output.wav
./speak.py "Excited message" -e 0.8
./speak.py "Just generate, don't play" --no-play
```

| Flag | Description |
|------|-------------|
| `-o, --output FILE` | Output path (default: timestamped file in `spoken_affirmations/`) |
| `-e, --exaggeration 0-1` | Emotion intensity (default: 0.5) |
| `--no-play` | Skip auto-playback after generation |

---

### `./generate_positive_audio_clips.py`
Batch-generates affirmation clips in your cloned voice. The main production script.

```bash
./generate_positive_audio_clips.py                    # Use positive_messages.txt, sample 6
./generate_positive_audio_clips.py -n 10              # Sample 10 messages
./generate_positive_audio_clips.py -n -1              # Generate ALL messages
./generate_positive_audio_clips.py "Hi" "Bye"         # Custom strings (bypasses file)
./generate_positive_audio_clips.py -e 0.7             # More emotional delivery
echo "Custom message" | ./generate_positive_audio_clips.py   # Read from stdin
```

| Flag | Description |
|------|-------------|
| `-n, --count N` | Number of messages to sample (default: 6, use -1 for all) |
| `-o, --output-dir DIR` | Output directory (default: `spoken_affirmations/`) |
| `-e, --exaggeration 0-1` | Emotion intensity (default: 0.5) |

---

### `./weave.py`
Weaves clips into an immersive stereo soundscape with spatial panning and audio differentiation.

```bash
./weave.py                      # Use all clips
./weave.py -t 300               # Target ~5 minute output
./weave.py -s 42                # Reproducible random seed
```

| Flag | Description |
|------|-------------|
| `-t, --target-duration SEC` | Target output length in seconds |
| `-s, --seed N` | Random seed for reproducible ordering |

Output: `spoken_messages_001.wav` (auto-increments). Use headphones for the stereo effect.

---

## Workflows

### Stock Affirmations (Quick Start)

Use the built-in affirmations to get started immediately:

```bash
# 1. Install dependencies
./install.sh

# 2. Record your voice (15-30 seconds)
./record.py

# 3. Create voice reference
./prepare.py

# 4. Generate clips from stock affirmations (creates positive_messages.txt if missing)
./generate_positive_audio_clips.py -n 10

# 5. Weave into stereo soundscape
./weave.py -t 180

# 6. Listen (use headphones!)
afplay spoken_messages_001.wav
```

---

### Custom Affirmations via Stdin

Pipe your own affirmations for personalized content:

```bash
# From a custom file
cat my_affirmations.txt | ./generate_positive_audio_clips.py -n -1

# From a here-doc
./generate_positive_audio_clips.py << 'EOF'
I am capable of achieving great things.
My work makes a meaningful difference.
I trust my creative instincts.
EOF

# From another command
grep "success" ~/notes/mantras.txt | ./generate_positive_audio_clips.py

# Then weave
./weave.py
```

---

### Editing the Default Affirmations

The first run of `generate_positive_audio_clips.py` creates `positive_messages.txt`. Edit this file directly:

```bash
# Edit the file
vim positive_messages.txt

# Regenerate all clips
./generate_positive_audio_clips.py -n -1

# Create new weave
./weave.py -t 600
```

Lines starting with `#` are ignored. One affirmation per line.
