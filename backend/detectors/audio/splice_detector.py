"""
Audio Forensics - Splice Detection
Detects:
- Audio splice boundaries via spectral discontinuity
- Noise floor inconsistencies
- MFCC pattern breaks
- Spectral flux anomalies
"""

import numpy as np
import librosa
from scipy import signal
from typing import List
from pathlib import Path


class AudioSpliceDetector:
    def __init__(self, audio_path: str, sr: int = 22050, y: np.ndarray = None):
        self.audio_path = Path(audio_path)
        self.sr = sr
        if y is not None:
            self.y = y
        else:
            self.y, _ = librosa.load(str(self.audio_path), sr=self.sr)
        self.duration = len(self.y) / self.sr
        self.findings: List[dict] = []

    def analyze(self) -> List[dict]:
        """Run all audio splice detection techniques."""
        self._detect_spectral_flux_anomalies()
        self._detect_noise_floor_changes()
        self._detect_mfcc_discontinuities()
        self._detect_silence_gaps()
        return self.findings

    def _detect_spectral_flux_anomalies(self):
        """Detect sudden spectral changes that indicate splicing."""
        # Compute spectrogram
        S = np.abs(librosa.stft(self.y, n_fft=2048, hop_length=512))

        # Spectral flux: frame-to-frame difference
        flux = np.sqrt(np.sum(np.diff(S, axis=1) ** 2, axis=0))

        # Normalize
        if flux.std() == 0:
            return
        flux_norm = (flux - flux.mean()) / flux.std()

        # Find peaks that are significant outliers (>3 std deviations)
        threshold = 3.0
        anomaly_frames = np.where(flux_norm > threshold)[0]

        if len(anomaly_frames) == 0:
            return

        # Cluster nearby frames into events
        events = self._cluster_frames(anomaly_frames, min_gap=10)

        for start_frame, end_frame in events:
            start_time = librosa.frames_to_time(start_frame, sr=self.sr, hop_length=512)
            end_time = librosa.frames_to_time(end_frame, sr=self.sr, hop_length=512)
            peak_score = float(flux_norm[start_frame:end_frame + 1].max())

            confidence = min(0.4 + (peak_score - threshold) * 0.15, 0.95)

            self.findings.append({
                "finding_type": "audio_splice",
                "confidence": confidence,
                "start_time": round(start_time, 3),
                "end_time": round(end_time, 3),
                "description": f"Spectral flux anomaly (z-score: {peak_score:.1f}) suggests possible splice point",
                "details": {"method": "spectral_flux", "z_score": round(peak_score, 2)},
            })

    def _detect_noise_floor_changes(self):
        """Detect changes in background noise level that indicate splicing."""
        # Split audio into short windows
        window_size = int(self.sr * 0.5)  # 500ms windows
        hop = int(self.sr * 0.25)  # 250ms hop

        noise_floors = []
        for i in range(0, len(self.y) - window_size, hop):
            window = self.y[i:i + window_size]
            # RMS energy in quiet portions (bottom 20th percentile)
            sorted_abs = np.sort(np.abs(window))
            noise_floor = np.mean(sorted_abs[:len(sorted_abs) // 5])
            noise_floors.append(noise_floor)

        noise_floors = np.array(noise_floors)
        if len(noise_floors) < 4 or noise_floors.std() == 0:
            return

        # Detect sudden jumps in noise floor
        diff = np.abs(np.diff(noise_floors))
        diff_norm = (diff - diff.mean()) / (diff.std() + 1e-10)

        threshold = 2.5
        anomaly_indices = np.where(diff_norm > threshold)[0]

        events = self._cluster_frames(anomaly_indices, min_gap=4)

        for start_idx, end_idx in events:
            start_time = start_idx * 0.25  # hop is 250ms
            end_time = (end_idx + 1) * 0.25
            peak_score = float(diff_norm[start_idx:end_idx + 1].max())
            confidence = min(0.35 + (peak_score - threshold) * 0.12, 0.90)

            self.findings.append({
                "finding_type": "noise_floor_change",
                "confidence": confidence,
                "start_time": round(start_time, 3),
                "end_time": round(end_time, 3),
                "description": f"Abrupt noise floor change (z-score: {peak_score:.1f}) may indicate splicing",
                "details": {"method": "noise_floor", "z_score": round(peak_score, 2)},
            })

    def _detect_mfcc_discontinuities(self):
        """Detect breaks in MFCC patterns indicating audio from different sources."""
        mfccs = librosa.feature.mfcc(y=self.y, sr=self.sr, n_mfcc=13, hop_length=512)

        # Compute frame-to-frame MFCC distance
        mfcc_diff = np.sqrt(np.sum(np.diff(mfccs, axis=1) ** 2, axis=0))

        if mfcc_diff.std() == 0:
            return
        mfcc_diff_norm = (mfcc_diff - mfcc_diff.mean()) / mfcc_diff.std()

        # Look for extreme discontinuities
        threshold = 3.5
        anomaly_frames = np.where(mfcc_diff_norm > threshold)[0]

        if len(anomaly_frames) == 0:
            return

        events = self._cluster_frames(anomaly_frames, min_gap=10)

        for start_frame, end_frame in events:
            start_time = librosa.frames_to_time(start_frame, sr=self.sr, hop_length=512)
            end_time = librosa.frames_to_time(end_frame, sr=self.sr, hop_length=512)
            peak_score = float(mfcc_diff_norm[start_frame:end_frame + 1].max())
            confidence = min(0.35 + (peak_score - threshold) * 0.1, 0.85)

            self.findings.append({
                "finding_type": "mfcc_discontinuity",
                "confidence": confidence,
                "start_time": round(start_time, 3),
                "end_time": round(end_time, 3),
                "description": f"MFCC discontinuity (z-score: {peak_score:.1f}) indicates possible audio insertion",
                "details": {"method": "mfcc", "z_score": round(peak_score, 2)},
            })

    def _detect_silence_gaps(self):
        """Detect unnatural silence gaps that may indicate audio removal."""
        # Find silent regions
        intervals = librosa.effects.split(self.y, top_db=40, hop_length=512)

        if len(intervals) < 2:
            return

        # Check gaps between voiced segments
        for i in range(len(intervals) - 1):
            gap_start = intervals[i][1]
            gap_end = intervals[i + 1][0]
            gap_duration = (gap_end - gap_start) / self.sr

            # Very short gaps (20-100ms) at non-natural positions can indicate removal
            if 0.02 < gap_duration < 0.15:
                start_time = gap_start / self.sr
                end_time = gap_end / self.sr

                # Check if the transition is unusually abrupt
                pre_rms = np.sqrt(np.mean(self.y[max(0, gap_start - 512):gap_start] ** 2))
                post_rms = np.sqrt(np.mean(self.y[gap_end:min(len(self.y), gap_end + 512)] ** 2))

                if pre_rms > 0.01 and post_rms > 0.01:
                    ratio = max(pre_rms, post_rms) / (min(pre_rms, post_rms) + 1e-10)
                    if ratio > 3.0:
                        confidence = min(0.4 + (ratio - 3.0) * 0.05, 0.75)
                        self.findings.append({
                            "finding_type": "suspicious_silence",
                            "confidence": confidence,
                            "start_time": round(start_time, 3),
                            "end_time": round(end_time, 3),
                            "description": f"Unnatural silence gap ({gap_duration * 1000:.0f}ms) with energy asymmetry (ratio: {ratio:.1f})",
                            "details": {"method": "silence_gap", "gap_ms": round(gap_duration * 1000, 1), "energy_ratio": round(ratio, 2)},
                        })

    def _cluster_frames(self, frames: np.ndarray, min_gap: int = 5) -> List[tuple]:
        """Cluster nearby frame indices into events."""
        if len(frames) == 0:
            return []

        events = []
        start = frames[0]
        prev = frames[0]

        for f in frames[1:]:
            if f - prev > min_gap:
                events.append((int(start), int(prev)))
                start = f
            prev = f
        events.append((int(start), int(prev)))

        return events
