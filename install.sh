#!/bin/bash
#
# Install script for voice-affirmations
# Sets up Python virtual environments and downloads models
#

set -e

echo "========================================"
echo "Voice Affirmations - Installation"
echo "========================================"
echo ""

# Check dependencies
echo "Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not installed."
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is required but not installed."
    echo "Install with: brew install ffmpeg"
    exit 1
fi

# Check for uv (preferred) or fall back to pip
USE_UV=false
if command -v uv &> /dev/null; then
    USE_UV=true
    echo "Found uv - using for faster installation"
else
    echo "uv not found - using pip (install uv for faster setup: brew install uv)"
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create directories
echo ""
echo "Creating directories..."
mkdir -p voice_samples spoken_affirmations

# Setup venv for recording/weaving (pydub, sounddevice)
echo ""
echo "Setting up recording environment (venv)..."
if [ "$USE_UV" = true ]; then
    uv venv venv --python 3.11 --quiet
    source venv/bin/activate
    uv pip install pydub sounddevice soundfile numpy --quiet
else
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip --quiet
    pip install pydub sounddevice soundfile numpy --quiet
fi
deactivate
echo "  Done: venv/"

# Setup venv for chatterbox (voice cloning)
echo ""
echo "Setting up Chatterbox environment (venv-chatterbox)..."
if [ "$USE_UV" = true ]; then
    uv venv venv-chatterbox --python 3.11 --quiet
    source venv-chatterbox/bin/activate
    uv pip install chatterbox-tts --quiet
else
    python3 -m venv venv-chatterbox
    source venv-chatterbox/bin/activate
    pip install --upgrade pip --quiet
    pip install chatterbox-tts --quiet
fi

# Download the model
echo ""
echo "Downloading Chatterbox model (this may take a while)..."
python3 -c "
import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
import perth
if perth.PerthImplicitWatermarker is None:
    perth.PerthImplicitWatermarker = perth.DummyWatermarker
from chatterbox.tts import ChatterboxTTS
print('  Loading model...')
model = ChatterboxTTS.from_pretrained(device='cpu')
print('  Model downloaded and cached.')
"
deactivate
echo "  Done: venv-chatterbox/"

echo ""
echo "========================================"
echo "Installation complete!"
echo "========================================"
echo ""
echo "Quick start:"
echo "  1. Record your voice:  ./record.py"
echo "  2. Create reference:   ./prepare.py"
echo "  3. Generate clips:     ./generate_positive_messages.py"
echo "  4. Weave together:     ./weave.py"
echo "  5. Play result:        afplay combined_output.wav"
echo ""
