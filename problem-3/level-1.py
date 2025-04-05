import librosa
import numpy as np
import argparse

def detect_beats(audio_path, sensitivity=1.0):
    """
    Detects beats in the audio file and returns timestamps (in seconds).

    Args:
        audio_path (str): Path to .mp3 or .wav file
        sensitivity (float): Controls beat detection sensitivity (lower is more sensitive)

    Returns:
        List of beat timestamps (in seconds)
    """
    try:
        y, sr = librosa.load(audio_path)
    except Exception as e:
        print(f"Failed to load audio: {e}")
        return []

    # Get beat frames using librosa's beat tracking
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units='frames')
    
    # Convert beat frames to timestamps
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    # Optionally filter beats by energy
    rms = librosa.feature.rms(y=y)[0]
    frame_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
    
    min_rms_threshold = sensitivity * np.mean(rms)

    # Keep beat only if corresponding energy is above threshold
    final_beats = []
    for t in beat_times:
        idx = np.searchsorted(frame_times, t)
        if idx < len(rms) and rms[idx] > min_rms_threshold:
            final_beats.append(round(t, 3))  # rounded for cleaner output

    return final_beats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🎵 AutoBeatCut - Beat Detector Level 1")
    parser.add_argument("file", help="Path to audio file (.mp3 or .wav)")
    parser.add_argument("--sensitivity", type=float, default=1.0,
                        help="Energy sensitivity (default=1.0, lower = more sensitive)")
    args = parser.parse_args()

    print(f"🔍 Detecting beats in: {args.file}")
    beats = detect_beats(args.file, sensitivity=args.sensitivity)

    if beats:
        print("\n🎯 Detected Beat Timestamps (in seconds):")
        for t in beats:
            print(f"{t:.3f}")
    else:
        print("⚠️ No beats detected or failed to process audio.")
