"""
Video Forensics - GOP Analysis Detector
Detects:
- GOP structure breaks (re-encoding indicators)
- Unusual I-frame placement
- GOP size inconsistencies
"""

import json
from pathlib import Path
from typing import List, Optional
import numpy as np


class GOPDetector:
    def __init__(self, gop_data: List[dict], fps: float = 25.0):
        """
        Args:
            gop_data: List of frame dicts from FFprobe with pict_type, pts_time, key_frame
            fps: Video frame rate
        """
        self.frames = gop_data
        self.fps = fps
        self.findings: List[dict] = []

    def analyze(self) -> List[dict]:
        """Run GOP analysis."""
        if not self.frames or len(self.frames) < 10:
            return []

        self._detect_gop_breaks()
        self._detect_irregular_iframes()
        return self.findings

    def _detect_gop_breaks(self):
        """Detect breaks in GOP pattern that suggest re-encoding at specific points."""
        # Find I-frame positions
        iframe_indices = []
        for i, frame in enumerate(self.frames):
            if frame.get("key_frame") == 1 or frame.get("pict_type") == "I":
                iframe_indices.append(i)

        if len(iframe_indices) < 3:
            return

        # Calculate GOP sizes (distance between I-frames)
        gop_sizes = np.diff(iframe_indices)

        if len(gop_sizes) < 3 or gop_sizes.std() == 0:
            return

        # Find the most common GOP size (mode)
        from scipy import stats
        mode_result = stats.mode(gop_sizes, keepdims=True)
        expected_gop = int(mode_result.mode[0])

        if expected_gop == 0:
            return

        # Find GOP breaks - where size deviates significantly from expected
        for i, size in enumerate(gop_sizes):
            if size != expected_gop:
                deviation = abs(size - expected_gop) / expected_gop

                if deviation > 0.3:  # >30% deviation from expected GOP
                    iframe_idx = iframe_indices[i + 1]
                    time = float(self.frames[iframe_idx].get("pts_time", 0) or 0)

                    confidence = min(0.4 + deviation * 0.3, 0.88)

                    self.findings.append({
                        "finding_type": "gop_break",
                        "confidence": confidence,
                        "start_time": round(time - 0.5, 3),
                        "end_time": round(time + 0.5, 3),
                        "description": f"GOP break at {time:.2f}s (size={size} vs expected={expected_gop}). May indicate re-encoding at this point.",
                        "details": {
                            "method": "gop_analysis",
                            "gop_size": int(size),
                            "expected_gop": expected_gop,
                            "deviation": round(deviation, 3),
                            "frame_index": iframe_idx,
                        },
                    })

    def _detect_irregular_iframes(self):
        """Detect I-frames at positions that don't align with scene changes."""
        # Get I-frame timestamps
        iframe_times = []
        for frame in self.frames:
            if frame.get("key_frame") == 1 or frame.get("pict_type") == "I":
                time = float(frame.get("pts_time", 0) or 0)
                iframe_times.append(time)

        if len(iframe_times) < 4:
            return

        # Calculate intervals
        intervals = np.diff(iframe_times)
        if len(intervals) < 3 or np.std(intervals) == 0:
            return

        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)

        # Find clusters of short intervals (suggests forced I-frames from editing)
        short_threshold = mean_interval - 2 * std_interval
        if short_threshold <= 0:
            return

        for i, interval in enumerate(intervals):
            if interval < short_threshold and interval < mean_interval * 0.3:
                time = iframe_times[i + 1]
                confidence = min(0.35 + (1 - interval / mean_interval) * 0.3, 0.75)

                self.findings.append({
                    "finding_type": "irregular_iframe",
                    "confidence": confidence,
                    "start_time": round(time - 0.2, 3),
                    "end_time": round(time + 0.2, 3),
                    "description": f"Irregular I-frame at {time:.2f}s (interval={interval:.3f}s vs avg={mean_interval:.3f}s)",
                    "details": {
                        "method": "iframe_regularity",
                        "interval": round(interval, 4),
                        "mean_interval": round(mean_interval, 4),
                    },
                })
