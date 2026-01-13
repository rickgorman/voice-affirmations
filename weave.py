#!/bin/bash
''''exec "$(dirname "$0")/venv/bin/python3" "$0" "$@" # '''
"""
Audio weaving script - sequences clips on left and right channels
with independent random ordering and a 1-second offset.
"""

import random
import glob
import os
import re
import math
import sys
import argparse
from pydub import AudioSegment


OUTPUT_PREFIX = "spoken_messages_"
OUTPUT_PATTERN = re.compile(rf"^{OUTPUT_PREFIX}(\d{{3}})\.wav$")

OVERLAP_MS = 1500  # 1.5 second overlap between clips on each channel
RIGHT_CHANNEL_DELAY_MS = 3000  # Right channel starts 3 seconds after left
CROSSFEED = 0.30  # 30% bleed to opposite channel for "inner" positions

# Spatial positions (left_volume, right_volume)
POS_HARD_LEFT = (1.0, 0.0)
POS_SOFT_LEFT = (1.0, CROSSFEED)  # left + 30% right
POS_SOFT_RIGHT = (CROSSFEED, 1.0)  # right + 30% left
POS_HARD_RIGHT = (0.0, 1.0)

DURATION_TOLERANCE_MS = 4000  # Accept results within 4 seconds of target

# Intro sequence timing
INTRO_PAUSE_MS = 1000         # Pause after solo clips
INTRO_FINAL_PAUSE_MS = 1000   # Pause after paired intro clips
WEAVE_INITIAL_DELAY_MS = 2000 # Delay between left/right for first 2 weave clips
WEAVE_NORMAL_DELAY_MS = 1000  # Delay between left/right after first 2 clips
WEAVE_INITIAL_CLIPS = 2       # Number of clips to use initial delay for
MIN_CLIPS_FOR_INTRO = 3       # Need at least 3 clips per side for full intro
NO_OVERLAP_DURATION_MS = 30000  # No overlap on same channel for first 30 seconds

# Fade curves for smooth transitions
FADE_IN_MS = 100    # Quick fade in at clip start
FADE_OUT_MS = 500   # Longer fade out for smooth overlap transitions

# Audio differentiation profiles (alternated within each stream)
# Profile A: warm + slower
PROFILE_A = {
    'lowpass_hz': 3500,
    'highpass_hz': None,
    'tempo': 0.97,
}
# Profile B: bright + faster
PROFILE_B = {
    'lowpass_hz': None,
    'highpass_hz': 180,
    'tempo': 1.02,
}


def estimate_duration(clips, overlap_ms, delay_ms):
    """Estimate final output duration for a list of clips."""
    if not clips:
        return delay_ms

    total_clip_ms = sum(len(clip) for _, clip in clips)
    overlap_reduction = (len(clips) - 1) * overlap_ms
    stream_duration = total_clip_ms - overlap_reduction

    return stream_duration + delay_ms


def select_clips_for_duration(clips, target_ms, overlap_ms, delay_ms):
    """
    Select a subset of clips to approximately match target duration.
    Uses iterative refinement algorithm, O(n²) worst case.
    """
    if not clips:
        return []

    available = clips.copy()
    random.shuffle(available)
    selected = []

    # Greedy initial selection: add clips until we reach/exceed target
    for clip in available:
        selected.append(clip)
        if estimate_duration(selected, overlap_ms, delay_ms) >= target_ms:
            break

    # Iterative refinement
    max_iterations = len(clips) ** 2
    unselected = [c for c in available if c not in selected]

    for _ in range(max_iterations):
        current_duration = estimate_duration(selected, overlap_ms, delay_ms)
        diff = current_duration - target_ms

        if abs(diff) <= DURATION_TOLERANCE_MS:
            break

        if diff < 0 and unselected:
            # Too short: add the clip that gets us closest to target
            best_clip = None
            best_diff = float('inf')

            for clip in unselected:
                test_selected = selected + [clip]
                new_duration = estimate_duration(test_selected, overlap_ms, delay_ms)
                new_diff = abs(new_duration - target_ms)

                if new_diff < best_diff:
                    best_diff = new_diff
                    best_clip = clip

            if best_clip:
                selected.append(best_clip)
                unselected.remove(best_clip)

        elif diff > 0 and len(selected) > 1:
            # Too long: remove the clip that gets us closest to target
            best_idx = None
            best_diff = float('inf')

            for i in range(len(selected)):
                test_selected = selected[:i] + selected[i+1:]
                new_duration = estimate_duration(test_selected, overlap_ms, delay_ms)
                new_diff = abs(new_duration - target_ms)

                if new_diff < best_diff:
                    best_diff = new_diff
                    best_idx = i

            if best_idx is not None:
                removed = selected.pop(best_idx)
                unselected.append(removed)

        else:
            break

    return selected


def make_mono(clip):
    """Ensure clip is mono."""
    if clip.channels > 1:
        clip = clip.set_channels(1)
    return clip


def change_tempo(clip, tempo_factor):
    """
    Change tempo by adjusting frame rate and resampling.
    tempo_factor > 1.0 = faster, < 1.0 = slower
    """
    if tempo_factor == 1.0:
        return clip

    original_rate = clip.frame_rate
    new_rate = int(original_rate * tempo_factor)
    modified = clip._spawn(clip.raw_data, overrides={'frame_rate': new_rate})
    return modified.set_frame_rate(original_rate)


def apply_profile(clip, profile, apply_tempo=True):
    """Apply EQ and tempo profile to a clip."""
    if profile['lowpass_hz']:
        clip = clip.low_pass_filter(profile['lowpass_hz'])
    if profile['highpass_hz']:
        clip = clip.high_pass_filter(profile['highpass_hz'])
    if apply_tempo and profile['tempo'] != 1.0:
        clip = change_tempo(clip, profile['tempo'])
    return clip


def apply_fades(clip):
    """Apply fade in/out curves for smooth transitions."""
    return clip.fade_in(FADE_IN_MS).fade_out(FADE_OUT_MS)


def pan_to_stereo(mono_clip, position):
    """
    Pan a mono clip to a stereo position.
    position is (left_vol, right_vol) where 1.0 = full volume, 0.0 = silent.
    """
    mono_clip = make_mono(mono_clip)
    left_vol, right_vol = position

    def vol_to_db(vol):
        if vol <= 0:
            return -120  # essentially silent
        return 20 * math.log10(vol)

    left_db = vol_to_db(left_vol)
    right_db = vol_to_db(right_vol)

    left_channel = mono_clip.apply_gain(left_db)
    right_channel = mono_clip.apply_gain(right_db)

    return AudioSegment.from_mono_audiosegments(left_channel, right_channel)


def sequence_clips_with_overlap_and_positions(clips, positions, overlap_ms, no_overlap_until_ms=0):
    """
    Sequence clips with overlap, alternating between spatial positions
    and audio profiles (EQ + tempo) for differentiation.

    For the first no_overlap_until_ms, clips play back-to-back without overlap
    and without tempo changes. After that threshold, clips overlap by overlap_ms
    and tempo differentiation kicks in.

    Returns a stereo AudioSegment.
    """
    if not clips:
        return AudioSegment.silent(duration=0, frame_rate=44100).set_channels(2)

    profiles = [PROFILE_A, PROFILE_B]

    # Start with first clip at first position and profile (no tempo yet)
    processed_clip = apply_profile(clips[0], profiles[0], apply_tempo=False)
    processed_clip = apply_fades(processed_clip)
    result = pan_to_stereo(processed_clip, positions[0])
    current_end = len(result)

    for i, clip in enumerate(clips[1:], 1):
        pos = positions[i % len(positions)]
        profile = profiles[i % len(profiles)]

        # Only apply tempo changes after we've passed the no-overlap threshold
        use_tempo = current_end > no_overlap_until_ms
        processed_clip = apply_profile(clip, profile, apply_tempo=use_tempo)
        processed_clip = apply_fades(processed_clip)
        stereo_clip = pan_to_stereo(processed_clip, pos)

        # Only overlap after we've passed the no-overlap threshold
        if current_end > no_overlap_until_ms:
            effective_overlap = overlap_ms
        else:
            effective_overlap = 0

        # Position where this clip starts
        start_pos = max(0, current_end - effective_overlap)

        # Extend result if needed
        end_pos = start_pos + len(stereo_clip)
        if end_pos > len(result):
            result += AudioSegment.silent(duration=end_pos - len(result)).set_channels(2)

        result = result.overlay(stereo_clip, position=start_pos)
        current_end = end_pos

    return result


def build_intro(left_clips, right_clips, left_positions, right_positions):
    """
    Build gradual intro sequence:
    1. First clip on left alone
    2. 2s pause
    3. First clip on right alone
    4. 2s pause
    5. Second clip on left, with second clip on right starting halfway through
    6. Wait for both to finish, 1s pause

    Returns (intro_audio, remaining_left_clips, remaining_right_clips)
    """
    profiles = [PROFILE_A, PROFILE_B]
    result = AudioSegment.silent(duration=0, frame_rate=44100).set_channels(2)

    # 1. First message on left alone (profile A, hard-left, no tempo change)
    clip1_left = apply_profile(left_clips[0], profiles[0], apply_tempo=False)
    clip1_left = apply_fades(clip1_left)
    clip1_left_stereo = pan_to_stereo(clip1_left, left_positions[0])
    result += clip1_left_stereo

    # 2. 1 second pause
    result += AudioSegment.silent(duration=INTRO_PAUSE_MS).set_channels(2)

    # 3. First message on right alone (profile A, hard-right, no tempo change)
    clip1_right = apply_profile(right_clips[0], profiles[0], apply_tempo=False)
    clip1_right = apply_fades(clip1_right)
    clip1_right_stereo = pan_to_stereo(clip1_right, right_positions[0])
    result += clip1_right_stereo

    # 4. 1 second pause
    result += AudioSegment.silent(duration=INTRO_PAUSE_MS).set_channels(2)

    # 5. Second message on left (profile B, soft-left, no tempo change)
    clip2_left = apply_profile(left_clips[1], profiles[1], apply_tempo=False)
    clip2_left = apply_fades(clip2_left)
    clip2_left_stereo = pan_to_stereo(clip2_left, left_positions[1])

    # 6. Halfway through left, second message on right starts (profile B, soft-right, no tempo change)
    clip2_right = apply_profile(right_clips[1], profiles[1], apply_tempo=False)
    clip2_right = apply_fades(clip2_right)
    clip2_right_stereo = pan_to_stereo(clip2_right, right_positions[1])

    halfway = len(clip2_left_stereo) // 2

    # Combine the paired clips
    combined_len = max(len(clip2_left_stereo), halfway + len(clip2_right_stereo))
    combined = clip2_left_stereo
    if combined_len > len(combined):
        combined += AudioSegment.silent(duration=combined_len - len(combined)).set_channels(2)
    combined = combined.overlay(clip2_right_stereo, position=halfway)

    result += combined

    # 7. 1 second pause
    result += AudioSegment.silent(duration=INTRO_FINAL_PAUSE_MS).set_channels(2)

    return result, left_clips[2:], right_clips[2:]


def weave_stereo(
    clip_paths,
    output_path="combined_output.wav",
    seed=None,
    target_duration_s=None
):
    """
    Weave audio clips into stereo with spatial positioning.

    Intro sequence (gradual buildup):
    1. First clip plays on left alone
    2. 2s pause
    3. First clip plays on right alone
    4. 2s pause
    5. Second clip on left, with second clip on right starting halfway through
    6. 1s pause

    Main weave:
    - Left stream starts, right stream starts 2s later
    - Clips overlap within each stream
    - Alternates between hard and soft positions per side
    """
    if seed is not None:
        random.seed(seed)

    # Load all clips
    clips = []
    for path in clip_paths:
        clip = AudioSegment.from_file(path)
        clips.append((os.path.basename(path), clip))
        print(f"Loaded: {os.path.basename(path)} ({len(clip)/1000:.2f}s)")

    print(f"\nTotal clips available: {len(clips)}")

    # Select subset if target duration specified
    if target_duration_s is not None:
        target_ms = target_duration_s * 1000
        clips = select_clips_for_duration(
            clips, target_ms, OVERLAP_MS, RIGHT_CHANNEL_DELAY_MS
        )
        estimated = estimate_duration(clips, OVERLAP_MS, RIGHT_CHANNEL_DELAY_MS)
        print(f"Selected {len(clips)} clips for ~{estimated/1000:.1f}s target duration")

    # Create two independent random orderings
    left_order = clips.copy()
    right_order = clips.copy()
    random.shuffle(left_order)
    random.shuffle(right_order)

    # Positions for each side (alternating)
    left_positions = [POS_HARD_LEFT, POS_SOFT_LEFT]
    right_positions = [POS_HARD_RIGHT, POS_SOFT_RIGHT]

    print("\nLeft-side stream (hard-left ↔ soft-left):")
    for i, (name, _) in enumerate(left_order, 1):
        pos = "HARD-L" if (i - 1) % 2 == 0 else "SOFT-L"
        profile = "warm/slow" if (i - 1) % 2 == 0 else "bright/fast"
        print(f"  {i}. [{pos}] [{profile}] {name}")

    print("\nRight-side stream (hard-right ↔ soft-right):")
    for i, (name, _) in enumerate(right_order, 1):
        pos = "HARD-R" if (i - 1) % 2 == 0 else "SOFT-R"
        profile = "warm/slow" if (i - 1) % 2 == 0 else "bright/fast"
        print(f"  {i}. [{pos}] [{profile}] {name}")

    # Build audio with gradual intro
    print("\nBuilding audio (applying panning + EQ + tempo differentiation)...")

    left_clips = [clip for _, clip in left_order]
    right_clips = [clip for _, clip in right_order]

    if len(left_clips) >= MIN_CLIPS_FOR_INTRO and len(right_clips) >= MIN_CLIPS_FOR_INTRO:
        # Build intro with first 2 clips from each side
        print("  Building intro sequence...")
        intro, remaining_left, remaining_right = build_intro(
            left_clips, right_clips, left_positions, right_positions
        )

        if remaining_left and remaining_right:
            print("  Building main weave...")

            # Split into initial clips (2s delay) and rest (1s delay)
            initial_left = remaining_left[:WEAVE_INITIAL_CLIPS]
            initial_right = remaining_right[:WEAVE_INITIAL_CLIPS]
            rest_left = remaining_left[WEAVE_INITIAL_CLIPS:]
            rest_right = remaining_right[WEAVE_INITIAL_CLIPS:]

            # Build initial weave section (2s delay between left/right)
            initial_left_stream = sequence_clips_with_overlap_and_positions(
                initial_left, left_positions, OVERLAP_MS, NO_OVERLAP_DURATION_MS
            )
            initial_right_stream = sequence_clips_with_overlap_and_positions(
                initial_right, right_positions, OVERLAP_MS, NO_OVERLAP_DURATION_MS
            )

            # Add 2s delay to initial right stream
            initial_right_delay = AudioSegment.silent(duration=WEAVE_INITIAL_DELAY_MS).set_channels(2)
            initial_right_stream = initial_right_delay + initial_right_stream

            # Pad and overlay initial streams
            initial_max_len = max(len(initial_left_stream), len(initial_right_stream))
            if len(initial_left_stream) < initial_max_len:
                initial_left_stream += AudioSegment.silent(duration=initial_max_len - len(initial_left_stream)).set_channels(2)
            if len(initial_right_stream) < initial_max_len:
                initial_right_stream += AudioSegment.silent(duration=initial_max_len - len(initial_right_stream)).set_channels(2)

            initial_weave = initial_left_stream.overlay(initial_right_stream)

            # Build rest of weave (1s delay between left/right)
            if rest_left and rest_right:
                rest_left_stream = sequence_clips_with_overlap_and_positions(
                    rest_left, left_positions, OVERLAP_MS, NO_OVERLAP_DURATION_MS
                )
                rest_right_stream = sequence_clips_with_overlap_and_positions(
                    rest_right, right_positions, OVERLAP_MS, NO_OVERLAP_DURATION_MS
                )

                # Add 1s delay to rest right stream
                rest_right_delay = AudioSegment.silent(duration=WEAVE_NORMAL_DELAY_MS).set_channels(2)
                rest_right_stream = rest_right_delay + rest_right_stream

                # Pad and overlay rest streams
                rest_max_len = max(len(rest_left_stream), len(rest_right_stream))
                if len(rest_left_stream) < rest_max_len:
                    rest_left_stream += AudioSegment.silent(duration=rest_max_len - len(rest_left_stream)).set_channels(2)
                if len(rest_right_stream) < rest_max_len:
                    rest_right_stream += AudioSegment.silent(duration=rest_max_len - len(rest_right_stream)).set_channels(2)

                rest_weave = rest_left_stream.overlay(rest_right_stream)
                weave = initial_weave + rest_weave
            else:
                weave = initial_weave

            # Combine intro + weave
            combined = intro + weave
        else:
            # Only intro clips available
            combined = intro
    else:
        # Not enough clips for intro, fall back to simple weave with variable delay
        print("  Not enough clips for intro, using simple weave...")

        # Split into initial clips (2s delay) and rest (1s delay)
        initial_left = left_clips[:WEAVE_INITIAL_CLIPS]
        initial_right = right_clips[:WEAVE_INITIAL_CLIPS]
        rest_left = left_clips[WEAVE_INITIAL_CLIPS:]
        rest_right = right_clips[WEAVE_INITIAL_CLIPS:]

        # Build initial section with 2s delay
        initial_left_stream = sequence_clips_with_overlap_and_positions(
            initial_left, left_positions, OVERLAP_MS, NO_OVERLAP_DURATION_MS
        )
        initial_right_stream = sequence_clips_with_overlap_and_positions(
            initial_right, right_positions, OVERLAP_MS, NO_OVERLAP_DURATION_MS
        )

        initial_right_delay = AudioSegment.silent(duration=WEAVE_INITIAL_DELAY_MS).set_channels(2)
        initial_right_stream = initial_right_delay + initial_right_stream

        initial_max_len = max(len(initial_left_stream), len(initial_right_stream))
        if len(initial_left_stream) < initial_max_len:
            initial_left_stream += AudioSegment.silent(duration=initial_max_len - len(initial_left_stream)).set_channels(2)
        if len(initial_right_stream) < initial_max_len:
            initial_right_stream += AudioSegment.silent(duration=initial_max_len - len(initial_right_stream)).set_channels(2)

        combined = initial_left_stream.overlay(initial_right_stream)

        # Build rest with 1s delay
        if rest_left and rest_right:
            rest_left_stream = sequence_clips_with_overlap_and_positions(
                rest_left, left_positions, OVERLAP_MS, NO_OVERLAP_DURATION_MS
            )
            rest_right_stream = sequence_clips_with_overlap_and_positions(
                rest_right, right_positions, OVERLAP_MS, NO_OVERLAP_DURATION_MS
            )

            rest_right_delay = AudioSegment.silent(duration=WEAVE_NORMAL_DELAY_MS).set_channels(2)
            rest_right_stream = rest_right_delay + rest_right_stream

            rest_max_len = max(len(rest_left_stream), len(rest_right_stream))
            if len(rest_left_stream) < rest_max_len:
                rest_left_stream += AudioSegment.silent(duration=rest_max_len - len(rest_left_stream)).set_channels(2)
            if len(rest_right_stream) < rest_max_len:
                rest_right_stream += AudioSegment.silent(duration=rest_max_len - len(rest_right_stream)).set_channels(2)

            rest_weave = rest_left_stream.overlay(rest_right_stream)
            combined = combined + rest_weave

    print(f"\nTotal duration: {len(combined)/1000:.1f}s")

    # Export
    combined.export(output_path, format="wav")
    print(f"Exported: {output_path}")


def get_next_output_path():
    """Find the next available sequence number for the output file."""
    existing = glob.glob(f"{OUTPUT_PREFIX}*.wav")
    max_seq = 0

    for filename in existing:
        basename = os.path.basename(filename)
        match = OUTPUT_PATTERN.match(basename)
        if match:
            seq = int(match.group(1))
            if seq > max_seq:
                max_seq = seq

    next_seq = max_seq + 1
    return f"{OUTPUT_PREFIX}{next_seq:03d}.wav"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weave audio clips into stereo soundscape")
    parser.add_argument("-t", "--target-duration", type=int, default=None,
                        help="Target output duration in seconds (uses all clips if not specified)")
    parser.add_argument("-s", "--seed", type=int, default=None,
                        help="Random seed for reproducible output")
    args = parser.parse_args()

    # Find all audio clips in the spoken_affirmations folder
    clip_files = sorted(glob.glob("spoken_affirmations/*.wav"))

    if not clip_files:
        print("No .wav files found in spoken_affirmations/ folder!")
        exit(1)

    print(f"Found {len(clip_files)} clips\n")

    output_path = get_next_output_path()

    weave_stereo(
        clip_paths=clip_files,
        output_path=output_path,
        seed=args.seed,
        target_duration_s=args.target_duration
    )

    print("\nTo play (use headphones for stereo effect):")
    if sys.platform == "darwin":
        print(f"afplay {output_path}")
    elif sys.platform == "linux":
        print(f"aplay {output_path}")
        print(f"paplay {output_path}")
