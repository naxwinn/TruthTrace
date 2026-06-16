"""
Evaluation Dataset Generator
Creates 3 controlled test cases with known tampering for validation.

Test 1: Trim 2 seconds from video (simulates frame deletion)
Test 2: Remove segment from audio (simulates audio splice)
Test 3: Insert synthetic tone (simulates voice cloning/AI audio)
"""

import subprocess
import json
from pathlib import Path

TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)


def generate_all_test_cases():
    """Generate all evaluation test files."""
    print("=" * 60)
    print("TruthTrace Evaluation Dataset Generator")
    print("=" * 60)

    _generate_original()
    _generate_test1_trimmed()
    _generate_test2_audio_splice()
    _generate_test3_synthetic_voice()

    print("\n" + "=" * 60)
    print("All test cases generated successfully!")
    print("=" * 60)


def _generate_original():
    """Generate a 10-second original reference video."""
    print("\n[Original] Generating 10s reference video...")
    output = TEST_DATA_DIR / "original_10s.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=10:size=640x480:rate=25",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=10",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", str(output),
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)
    print(f"  -> {output} ({output.stat().st_size // 1024} KB)")


def _generate_test1_trimmed():
    """
    Test 1: Trim 2 seconds (4s-6s) from middle of video.
    Expected detection: Optical flow anomaly, GOP break at splice point.
    """
    print("\n[Test 1] Trimming 2 seconds from middle (4s-6s removed)...")
    original = TEST_DATA_DIR / "original_10s.mp4"
    part1 = TEST_DATA_DIR / "_part1.mp4"
    part2 = TEST_DATA_DIR / "_part2.mp4"
    output = TEST_DATA_DIR / "test1_trimmed.mp4"
    concat_file = TEST_DATA_DIR / "_concat.txt"

    # Extract 0-4s
    subprocess.run([
        "ffmpeg", "-y", "-i", str(original),
        "-t", "4", "-c", "copy", str(part1),
    ], capture_output=True, timeout=30)

    # Extract 6-10s
    subprocess.run([
        "ffmpeg", "-y", "-i", str(original),
        "-ss", "6", "-c", "copy", str(part2),
    ], capture_output=True, timeout=30)

    # Concatenate (re-encode to simulate real editing)
    concat_file.write_text(f"file '{part1.name}'\nfile '{part2.name}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        str(output),
    ], capture_output=True, timeout=60)

    # Cleanup temp files
    for f in [part1, part2, concat_file]:
        f.unlink(missing_ok=True)

    print(f"  -> {output} ({output.stat().st_size // 1024} KB)")
    print("  Expected: Optical flow anomaly at ~4s, GOP break, compression anomaly")


def _generate_test2_audio_splice():
    """
    Test 2: Remove 1 second of audio (3s-4s) and join remaining.
    Expected detection: Spectral discontinuity, noise floor change.
    """
    print("\n[Test 2] Splicing audio (removing 3s-4s segment)...")
    original = TEST_DATA_DIR / "original_10s.mp4"
    output = TEST_DATA_DIR / "test2_audio_splice.mp4"

    # Use complex filter to cut audio segment
    cmd = [
        "ffmpeg", "-y", "-i", str(original),
        "-filter_complex",
        "[0:a]atrim=0:3,asetpts=PTS-STARTPTS[a1];"
        "[0:a]atrim=4:10,asetpts=PTS-STARTPTS[a2];"
        "[a1][a2]concat=n=2:v=0:a=1[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", str(output),
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)

    print(f"  -> {output} ({output.stat().st_size // 1024} KB)")
    print("  Expected: Spectral flux anomaly at ~3s, MFCC discontinuity, noise floor change")


def _generate_test3_synthetic_voice():
    """
    Test 3: Replace section with synthetic tone (simulating AI-generated audio).
    Expected detection: Synthetic voice indicators, spectral anomaly.
    """
    print("\n[Test 3] Inserting synthetic audio segment (2s-4s replaced with 880Hz tone)...")
    original = TEST_DATA_DIR / "original_10s.mp4"
    output = TEST_DATA_DIR / "test3_synthetic_voice.mp4"

    # Replace audio from 2s-4s with a different frequency tone
    cmd = [
        "ffmpeg", "-y", "-i", str(original),
        "-f", "lavfi", "-i", "sine=frequency=880:duration=2",
        "-filter_complex",
        "[0:a]atrim=0:2,asetpts=PTS-STARTPTS[a1];"
        "[1:a]asetpts=PTS-STARTPTS[a2];"
        "[0:a]atrim=4:10,asetpts=PTS-STARTPTS[a3];"
        "[a1][a2][a3]concat=n=3:v=0:a=1[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", str(output),
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)

    print(f"  -> {output} ({output.stat().st_size // 1024} KB)")
    print("  Expected: AASIST trigger, spectral anomaly at 2s and 4s, MFCC discontinuity")


if __name__ == "__main__":
    generate_all_test_cases()
