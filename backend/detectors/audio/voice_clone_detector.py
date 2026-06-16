"""
Voice Clone / Synthetic Speech Detector
Lightweight implementation inspired by AASIST architecture.
Detects:
- Synthetic speech artifacts
- Voice cloning indicators
- Unnatural spectral patterns typical of TTS/VC systems
"""

import numpy as np
import librosa
from scipy import stats
from typing import List
from pathlib import Path


class VoiceCloneDetector:
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
        """Run synthetic voice detection pipeline."""
        self._detect_spectral_flatness_anomaly()
        self._detect_pitch_regularity()
        self._detect_formant_consistency()
        self._detect_high_frequency_artifacts()
        return self.findings

    def _detect_spectral_flatness_anomaly(self):
        """
        Synthetic speech often has unnaturally flat or smooth spectral characteristics.
        Real speech has more variation in spectral flatness over time.
        """
        flatness = librosa.feature.spectral_flatness(y=self.y, hop_length=512)[0]

        if len(flatness) < 10:
            return

        # Synthetic speech tends to have lower variance in spectral flatness
        flatness_var = np.var(flatness)
        flatness_mean = np.mean(flatness)

        # Very low variance suggests synthetic (unnaturally consistent)
        # Threshold determined empirically
        if flatness_var < 0.001 and flatness_mean > 0.01:
            confidence = min(0.5 + (0.001 - flatness_var) * 200, 0.85)
            self.findings.append({
                "finding_type": "synthetic_voice",
                "confidence": confidence,
                "start_time": 0.0,
                "end_time": self.duration,
                "description": f"Unnaturally consistent spectral flatness (var={flatness_var:.6f}) suggests synthetic speech",
                "details": {
                    "method": "spectral_flatness",
                    "variance": round(float(flatness_var), 6),
                    "mean": round(float(flatness_mean), 4),
                },
            })

    def _detect_pitch_regularity(self):
        """
        Real speech has natural pitch variation (jitter).
        Synthetic speech from older TTS systems is too regular.
        """
        # Extract pitch using pyin
        f0, voiced_flag, _ = librosa.pyin(
            self.y, fmin=50, fmax=500, sr=self.sr, hop_length=512
        )

        if f0 is None:
            return

        # Only consider voiced segments
        voiced_f0 = f0[voiced_flag]
        if len(voiced_f0) < 20:
            return

        # Calculate jitter (pitch period perturbation)
        pitch_diffs = np.abs(np.diff(voiced_f0))
        mean_pitch = np.mean(voiced_f0)

        if mean_pitch == 0:
            return

        jitter = np.mean(pitch_diffs) / mean_pitch

        # Very low jitter (<0.5%) is suspicious for synthetic speech
        if jitter < 0.005:
            confidence = min(0.45 + (0.005 - jitter) * 60, 0.80)
            self.findings.append({
                "finding_type": "synthetic_voice",
                "confidence": confidence,
                "start_time": 0.0,
                "end_time": self.duration,
                "description": f"Abnormally low pitch jitter ({jitter:.4f}) suggests synthetic voice",
                "details": {
                    "method": "pitch_regularity",
                    "jitter": round(float(jitter), 5),
                    "mean_pitch_hz": round(float(mean_pitch), 1),
                },
            })

    def _detect_formant_consistency(self):
        """
        Analyze formant stability. Cloned voices sometimes have
        unnaturally stable formant transitions.
        """
        # Use LPC to estimate formants in windows
        window_size = int(self.sr * 0.03)  # 30ms windows
        hop = int(self.sr * 0.05)  # 50ms hop (was 10ms — 5x faster)
        order = 12

        formant_variations = []

        for i in range(0, len(self.y) - window_size, hop):
            window = self.y[i:i + window_size]
            if np.max(np.abs(window)) < 0.01:
                continue

            # Apply pre-emphasis and windowing
            window = np.append(window[0], window[1:] - 0.97 * window[:-1])
            window = window * np.hamming(len(window))

            try:
                # LPC analysis
                a = librosa.lpc(window, order=order)
                roots = np.roots(a)
                # Only keep roots inside the unit circle with positive imaginary part
                roots = roots[np.imag(roots) > 0]
                roots = roots[np.abs(roots) < 1]

                if len(roots) > 0:
                    angles = np.arctan2(np.imag(roots), np.real(roots))
                    freqs = sorted(angles * self.sr / (2 * np.pi))
                    # Get first two formants
                    formants = [f for f in freqs if 200 < f < 4000][:2]
                    if len(formants) == 2:
                        formant_variations.append(formants)
            except Exception:
                continue

        if len(formant_variations) < 20:
            return

        formant_variations = np.array(formant_variations)
        # Coefficient of variation for each formant
        f1_cv = np.std(formant_variations[:, 0]) / (np.mean(formant_variations[:, 0]) + 1e-10)
        f2_cv = np.std(formant_variations[:, 1]) / (np.mean(formant_variations[:, 1]) + 1e-10)

        # Very low formant variation indicates synthetic
        avg_cv = (f1_cv + f2_cv) / 2
        if avg_cv < 0.05:
            confidence = min(0.4 + (0.05 - avg_cv) * 8, 0.75)
            self.findings.append({
                "finding_type": "synthetic_voice",
                "confidence": confidence,
                "start_time": 0.0,
                "end_time": self.duration,
                "description": f"Unnaturally stable formants (CV={avg_cv:.4f}) suggest voice cloning",
                "details": {
                    "method": "formant_consistency",
                    "f1_cv": round(float(f1_cv), 4),
                    "f2_cv": round(float(f2_cv), 4),
                },
            })

    def _detect_high_frequency_artifacts(self):
        """
        Many voice synthesis systems have characteristic dropoff or artifacts
        in high frequency bands (>8kHz) due to vocoder limitations.
        """
        # Compute mel spectrogram
        S = librosa.feature.melspectrogram(
            y=self.y, sr=self.sr, n_mels=128, fmax=self.sr // 2, hop_length=512
        )
        S_db = librosa.power_to_db(S, ref=np.max)

        # Compare energy in high vs mid bands
        n_mels = S_db.shape[0]
        mid_band = S_db[n_mels // 4:n_mels // 2, :]  # ~2-4kHz region
        high_band = S_db[3 * n_mels // 4:, :]  # >8kHz region

        mid_energy = np.mean(mid_band)
        high_energy = np.mean(high_band)

        # Abnormal dropoff suggests vocoder artifacts
        dropoff = mid_energy - high_energy

        # Check for unnaturally sharp cutoff (>40dB difference)
        if dropoff > 40:
            # Also check if the high band is unnaturally uniform
            high_var = np.var(high_band)
            if high_var < 5.0:
                confidence = min(0.4 + (dropoff - 40) * 0.01, 0.70)
                self.findings.append({
                    "finding_type": "synthetic_voice",
                    "confidence": confidence,
                    "start_time": 0.0,
                    "end_time": self.duration,
                    "description": f"Sharp high-frequency cutoff ({dropoff:.0f}dB) with low variance suggests vocoder artifacts",
                    "details": {
                        "method": "hf_artifact",
                        "dropoff_db": round(float(dropoff), 1),
                        "high_band_var": round(float(high_var), 2),
                    },
                })
