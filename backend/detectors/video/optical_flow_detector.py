"""
Video Forensics - Optical Flow Detector
Detects:
- Frame deletion (sudden motion jumps)
- Frame insertion (motion stalls)
- Motion discontinuity at splice points
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List


class OpticalFlowDetector:
    MAX_FRAMES = 150  # Cap frames to bound runtime
    ANALYSIS_HEIGHT = 360  # Downsample to 360p for speed

    def __init__(self, frames_dir: str, fps: float = 2.0):
        self.frames_dir = Path(frames_dir)
        self.fps = fps
        self.findings: List[dict] = []
        all_paths = sorted(self.frames_dir.glob("frame_*.jpg"))
        # Sample frames if too many — evenly spaced to preserve temporal coverage
        if len(all_paths) > self.MAX_FRAMES:
            indices = np.linspace(0, len(all_paths) - 1, self.MAX_FRAMES, dtype=int)
            self.frame_paths = [all_paths[i] for i in indices]
            self.effective_fps = fps * (len(all_paths) / self.MAX_FRAMES)
        else:
            self.frame_paths = all_paths
            self.effective_fps = fps

    def _load_gray_resized(self, path) -> np.ndarray:
        """Load frame as grayscale and resize to analysis resolution."""
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        h, w = img.shape
        if h > self.ANALYSIS_HEIGHT:
            scale = self.ANALYSIS_HEIGHT / h
            img = cv2.resize(img, (int(w * scale), self.ANALYSIS_HEIGHT), interpolation=cv2.INTER_AREA)
        return img

    def analyze(self) -> List[dict]:
        """Run optical flow analysis to detect motion discontinuities."""
        if len(self.frame_paths) < 3:
            return []

        self._detect_motion_discontinuity()
        self._detect_static_frames()
        return self.findings

    def _detect_motion_discontinuity(self):
        """Use Farneback optical flow to detect sudden motion changes."""
        flow_magnitudes = []

        prev_gray = self._load_gray_resized(self.frame_paths[0])
        if prev_gray is None:
            return

        for i in range(1, len(self.frame_paths)):
            curr_gray = self._load_gray_resized(self.frame_paths[i])
            if curr_gray is None:
                flow_magnitudes.append(0.0)
                continue

            # Ensure same dimensions (in case of resize edge cases)
            if prev_gray.shape != curr_gray.shape:
                curr_gray = cv2.resize(curr_gray, (prev_gray.shape[1], prev_gray.shape[0]))

            # Compute dense optical flow
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, curr_gray,
                None,
                pyr_scale=0.5,
                levels=3,
                winsize=15,
                iterations=3,
                poly_n=5,
                poly_sigma=1.2,
                flags=0,
            )

            # Magnitude of flow vectors
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            mean_mag = float(np.mean(mag))
            flow_magnitudes.append(mean_mag)

            prev_gray = curr_gray

        if not flow_magnitudes or np.std(flow_magnitudes) == 0:
            return

        flow_arr = np.array(flow_magnitudes)
        flow_norm = (flow_arr - flow_arr.mean()) / (flow_arr.std() + 1e-10)

        # Detect sudden jumps (frame deletion creates motion discontinuity)
        threshold = 2.5
        anomaly_indices = np.where(np.abs(flow_norm) > threshold)[0]

        for idx in anomaly_indices:
            frame_time = (idx + 1) / self.effective_fps
            z_score = float(flow_norm[idx])

            if z_score > threshold:
                # Sudden high motion = possible frame deletion
                confidence = min(0.4 + (abs(z_score) - threshold) * 0.15, 0.92)
                self.findings.append({
                    "finding_type": "frame_deletion",
                    "confidence": confidence,
                    "start_time": round(frame_time - 0.5 / self.effective_fps, 3),
                    "end_time": round(frame_time + 0.5 / self.effective_fps, 3),
                    "description": f"Motion discontinuity (z={z_score:.1f}) suggests frames may have been removed",
                    "details": {
                        "method": "optical_flow",
                        "z_score": round(z_score, 2),
                        "flow_magnitude": round(float(flow_arr[idx]), 4),
                        "frame_index": int(idx + 1),
                    },
                })
            elif z_score < -threshold:
                # Sudden low motion after high = possible frame insertion
                confidence = min(0.35 + (abs(z_score) - threshold) * 0.12, 0.85)
                self.findings.append({
                    "finding_type": "frame_insertion",
                    "confidence": confidence,
                    "start_time": round(frame_time - 0.5 / self.effective_fps, 3),
                    "end_time": round(frame_time + 0.5 / self.effective_fps, 3),
                    "description": f"Motion stall (z={z_score:.1f}) suggests frames may have been inserted",
                    "details": {
                        "method": "optical_flow",
                        "z_score": round(z_score, 2),
                        "flow_magnitude": round(float(flow_arr[idx]), 4),
                        "frame_index": int(idx + 1),
                    },
                })

    def _detect_static_frames(self):
        """Detect sequences of near-identical frames (freeze frame manipulation)."""
        if len(self.frame_paths) < 3:
            return

        static_run = 0
        static_start = 0
        threshold_ssim = 0.995  # Nearly identical

        prev_gray = self._load_gray_resized(self.frame_paths[0])
        if prev_gray is None:
            return

        for i in range(1, len(self.frame_paths)):
            curr_gray = self._load_gray_resized(self.frame_paths[i])
            if curr_gray is None:
                continue

            # Ensure same dimensions
            if prev_gray.shape != curr_gray.shape:
                curr_gray = cv2.resize(curr_gray, (prev_gray.shape[1], prev_gray.shape[0]))

            # Quick similarity check using normalized correlation
            correlation = cv2.matchTemplate(
                prev_gray, curr_gray, cv2.TM_CCORR_NORMED
            )[0][0]

            if correlation > threshold_ssim:
                if static_run == 0:
                    static_start = i - 1
                static_run += 1
            else:
                if static_run >= 3:  # At least 3 identical frames at 2fps = 1.5s freeze
                        start_time = static_start / self.effective_fps
                        end_time = (static_start + static_run) / self.effective_fps
                    duration = end_time - start_time
                    confidence = min(0.5 + duration * 0.1, 0.85)

                    self.findings.append({
                        "finding_type": "freeze_frame",
                        "confidence": confidence,
                        "start_time": round(start_time, 3),
                        "end_time": round(end_time, 3),
                        "description": f"Static frame sequence ({duration:.1f}s) may indicate freeze-frame manipulation",
                        "details": {
                            "method": "static_detection",
                            "duration_seconds": round(duration, 2),
                            "frame_count": static_run,
                        },
                    })
                static_run = 0

            prev_gray = curr_gray
