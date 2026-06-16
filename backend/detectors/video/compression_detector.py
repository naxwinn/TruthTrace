"""
Video Forensics - Compression Anomaly Detector
Detects:
- Double compression artifacts
- Quantization inconsistencies
- Block artifact grid analysis
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List


class CompressionDetector:
    MAX_FRAMES = 150  # Cap frames to bound runtime

    def __init__(self, frames_dir: str, fps: float = 2.0):
        self.frames_dir = Path(frames_dir)
        self.fps = fps
        self.findings: List[dict] = []
        all_paths = sorted(self.frames_dir.glob("frame_*.jpg"))
        # Sample frames if too many
        if len(all_paths) > self.MAX_FRAMES:
            indices = np.linspace(0, len(all_paths) - 1, self.MAX_FRAMES, dtype=int)
            self.frame_paths = [all_paths[i] for i in indices]
            self.effective_fps = fps * (len(all_paths) / self.MAX_FRAMES)
        else:
            self.frame_paths = all_paths
            self.effective_fps = fps
        self._cached_frames = None

    def _load_frames(self) -> List[np.ndarray]:
        """Load all frames once and cache them."""
        if self._cached_frames is not None:
            return self._cached_frames
        self._cached_frames = []
        for frame_path in self.frame_paths:
            img = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)
            self._cached_frames.append(img)
        return self._cached_frames

    def analyze(self) -> List[dict]:
        """Run compression anomaly detection."""
        if len(self.frame_paths) < 2:
            return []

        self._detect_quantization_inconsistency()
        self._detect_block_artifact_anomalies()
        self._cached_frames = None  # Free memory after analysis
        return self.findings

    def _detect_quantization_inconsistency(self):
        """
        Detect regions with different quantization levels.
        Double-compressed regions show different DCT coefficient distributions.
        """
        quality_scores = []
        frames = self._load_frames()

        for img in frames:
            if img is None:
                quality_scores.append(0)
                continue

            # Estimate JPEG quality via Laplacian variance (sharpness proxy)
            laplacian = cv2.Laplacian(img, cv2.CV_64F)
            quality_scores.append(float(np.var(laplacian)))

        if not quality_scores or np.std(quality_scores) == 0:
            return

        quality_arr = np.array(quality_scores)
        quality_norm = (quality_arr - quality_arr.mean()) / (quality_arr.std() + 1e-10)

        # Detect sudden quality changes (different compression levels)
        quality_diff = np.abs(np.diff(quality_norm))
        threshold = 2.0

        for i, diff in enumerate(quality_diff):
            if diff > threshold:
                time = (i + 1) / self.effective_fps
                confidence = min(0.35 + (diff - threshold) * 0.15, 0.82)

                self.findings.append({
                    "finding_type": "compression_anomaly",
                    "confidence": confidence,
                    "start_time": round(time - 0.5 / self.effective_fps, 3),
                    "end_time": round(time + 0.5 / self.effective_fps, 3),
                    "description": f"Quantization level change at {time:.2f}s (delta={diff:.2f}) suggests double compression",
                    "details": {
                        "method": "quantization_analysis",
                        "quality_delta": round(float(diff), 3),
                        "frame_index": i + 1,
                    },
                })

    def _detect_block_artifact_anomalies(self):
        """
        Analyze 8x8 block boundary artifacts.
        Re-compressed regions may show misaligned or stronger blocking.
        """
        block_scores = []
        frames = self._load_frames()

        for img in frames:
            if img is None:
                block_scores.append(0)
                continue

            score = self._measure_blockiness(img)
            block_scores.append(score)

        if not block_scores or np.std(block_scores) == 0:
            return

        block_arr = np.array(block_scores)
        block_norm = (block_arr - block_arr.mean()) / (block_arr.std() + 1e-10)

        # Detect frames with significantly different blockiness
        threshold = 2.0
        for i, score in enumerate(block_norm):
            if abs(score) > threshold:
                time = i / self.effective_fps
                confidence = min(0.3 + (abs(score) - threshold) * 0.12, 0.78)

                finding_type = "double_compression" if score > 0 else "compression_anomaly"
                desc = "Increased" if score > 0 else "Decreased"

                self.findings.append({
                    "finding_type": finding_type,
                    "confidence": confidence,
                    "start_time": round(time, 3),
                    "end_time": round(time + 1.0 / self.effective_fps, 3),
                    "description": f"{desc} block artifacts at {time:.2f}s (z={score:.1f}) indicates potential re-encoding",
                    "details": {
                        "method": "block_artifact",
                        "blockiness_zscore": round(float(score), 2),
                        "frame_index": i,
                    },
                })

    def _measure_blockiness(self, img: np.ndarray) -> float:
        """Measure 8x8 JPEG block boundary strength."""
        h, w = img.shape
        img_float = img.astype(np.float64)

        # Measure horizontal block boundaries (every 8 pixels)
        h_boundaries = 0.0
        h_count = 0
        for x in range(7, w - 1, 8):
            if x + 1 < w:
                diff = np.abs(img_float[:, x] - img_float[:, x + 1])
                h_boundaries += np.mean(diff)
                h_count += 1

        # Measure vertical block boundaries
        v_boundaries = 0.0
        v_count = 0
        for y in range(7, h - 1, 8):
            if y + 1 < h:
                diff = np.abs(img_float[y, :] - img_float[y + 1, :])
                v_boundaries += np.mean(diff)
                v_count += 1

        total_boundary = 0.0
        if h_count > 0:
            total_boundary += h_boundaries / h_count
        if v_count > 0:
            total_boundary += v_boundaries / v_count

        return total_boundary
