import librosa
import numpy as np
import argparse
from datetime import timedelta


def seconds_to_timestamp(seconds: float) -> str:
    """Convert float seconds to HH:MM:SS.MS format."""
    return str(timedelta(seconds=seconds))[:-3]


def detect_cut_markers(audio_path, sensitivity=1.0, min_gap=0.4, energy_threshold=0.1):
    """
    Detects beat-based cut markers and returns timestamp strings.

    Args:
        audio_path (str): Path to audio file
        sensitivity (float): Controls beat detection sensitivity (lower = more sensitive)
        min_gap (float): Minimum gap in seconds between successive cuts
        energy_threshold (float): Min RMS energy (normalized) required to accept a beat

    Returns:
        List of formatted cut timestamps (HH:MM:SS.MS)
    """
    y, sr = librosa.load(audio_path)
    
    # Calculate RMS energy to ignore low-energy beats
    rms = librosa.feature.rms(y=y)[0]
    frame_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
    mean_rms = np.mean(rms)
    min_energy = energy_threshold * mean_rms

    # Detect beat times
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units='frames')
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # Filter based on energy
    filtered_beats = []
    last_accepted = -np.inf

    for t in beat_times:
        idx = np.searchsorted(frame_times, t)
        if idx < len(rms) and rms[idx] >= min_energy:
            if t - last_accepted >= min_gap:
                filtered_beats.append(seconds_to_timestamp(round(t, 3)))
                last_accepted = t

    return filtered_beats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🎬 AutoBeatCut - Cut Marker Generator (Level 2)")
    parser.add_argument("file", help="Path to audio file (.mp3 or .wav)")
    parser.add_argument("--sensitivity", type=float, default=1.0,
                        help="Beat detection sensitivity (lower = more sensitive, default=1.0)")
    parser.add_argument("--min_gap", type=float, default=0.4,
                        help="Minimum time gap between cuts (in seconds, default=0.4)")
    parser.add_argument("--energy_threshold", type=float, default=0.1,
                        help="Ignore beats with energy below this fraction of average (default=0.1)")
    parser.add_argument("--output", help="Optional file to save timestamps")

    args = parser.parse_args()

    print(f"\n🔍 Processing: {args.file}")
    print(f"🎛️ Sensitivity={args.sensitivity}, Min Gap={args.min_gap}s, Energy Threshold={args.energy_threshold}")

    markers = detect_cut_markers(
        audio_path=args.file,
        sensitivity=args.sensitivity,
        min_gap=args.min_gap,
        energy_threshold=args.energy_threshold
    )

    if markers:
        print(f"\n📌 Cut Markers ({len(markers)} total):")
        for ts in markers:
            print(ts)

        if args.output:
            with open(args.output, 'w') as f:
                for ts in markers:
                    f.write(ts + '\n')
            print(f"\n💾 Saved to {args.output}")
    else:
        print("⚠️ No cut markers found.")
