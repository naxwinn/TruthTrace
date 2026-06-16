"""
Metadata Forensics Detector
Detects:
- Encoder mismatches
- Timestamp anomalies
- Missing/stripped metadata
- Container inconsistencies
"""

import json
from pathlib import Path
from typing import List


class MetadataDetector:
    def __init__(self, metadata_path: str):
        self.metadata_path = Path(metadata_path)
        with open(self.metadata_path) as f:
            self.metadata = json.load(f)

        self.format_info = self.metadata.get("format", {})
        self.streams = self.metadata.get("streams", [])
        self.findings: List[dict] = []

    def analyze(self) -> List[dict]:
        """Run all metadata checks."""
        self._check_encoder_mismatch()
        self._check_timestamp_anomalies()
        self._check_missing_metadata()
        self._check_container_inconsistency()
        self._check_suspicious_tags()
        return self.findings

    def _check_encoder_mismatch(self):
        """Detect if video and audio were encoded by different tools."""
        video_streams = [s for s in self.streams if s.get("codec_type") == "video"]
        audio_streams = [s for s in self.streams if s.get("codec_type") == "audio"]

        if not video_streams or not audio_streams:
            return

        # Check for encoder tag differences
        format_tags = self.format_info.get("tags", {})
        encoder = format_tags.get("encoder", "").lower()
        creation_tool = format_tags.get("creation_time", "")

        # Look for stream-level encoding differences
        video_codec = video_streams[0].get("codec_name", "")
        audio_codec = audio_streams[0].get("codec_name", "")

        # Suspicious: H.264 video with PCM audio in MP4 (unusual for normal recording)
        if video_codec == "h264" and audio_codec in ("pcm_s16le", "pcm_s24le"):
            self.findings.append({
                "finding_type": "encoder_mismatch",
                "confidence": 0.65,
                "description": f"Unusual codec combination: {video_codec} video with {audio_codec} audio. May indicate post-processing.",
                "details": {"video_codec": video_codec, "audio_codec": audio_codec},
            })

        # Check for multiple encoder signatures
        stream_tags = []
        for s in self.streams:
            tags = s.get("tags", {})
            handler = tags.get("handler_name", "")
            if handler:
                stream_tags.append(handler)

        unique_handlers = set(stream_tags)
        if len(unique_handlers) > 1:
            # Different handlers might indicate multiplexing from different sources
            self.findings.append({
                "finding_type": "encoder_mismatch",
                "confidence": 0.55,
                "description": f"Multiple handler signatures detected: {unique_handlers}",
                "details": {"handlers": list(unique_handlers)},
            })

    def _check_timestamp_anomalies(self):
        """Detect timestamp inconsistencies."""
        format_tags = self.format_info.get("tags", {})
        creation_time = format_tags.get("creation_time", "")

        # Check stream durations vs format duration
        format_duration = float(self.format_info.get("duration", 0))

        for stream in self.streams:
            stream_duration = float(stream.get("duration", 0) or 0)
            if stream_duration > 0 and format_duration > 0:
                diff = abs(stream_duration - format_duration)
                if diff > 1.0:  # More than 1 second discrepancy
                    self.findings.append({
                        "finding_type": "timestamp_mismatch",
                        "confidence": min(0.5 + (diff / 10.0), 0.95),
                        "description": f"Stream duration ({stream_duration:.2f}s) differs from container duration ({format_duration:.2f}s) by {diff:.2f}s",
                        "details": {
                            "stream_duration": stream_duration,
                            "format_duration": format_duration,
                            "difference": diff,
                            "stream_index": stream.get("index"),
                        },
                    })

        # Check for start_time anomalies
        for stream in self.streams:
            start_time = float(stream.get("start_time", 0) or 0)
            if start_time > 0.5:  # Non-zero start time suggests editing
                self.findings.append({
                    "finding_type": "timestamp_anomaly",
                    "confidence": 0.60,
                    "description": f"Non-zero stream start time ({start_time:.3f}s) may indicate editing or trimming",
                    "details": {"start_time": start_time, "stream_index": stream.get("index")},
                })

    def _check_missing_metadata(self):
        """Detect suspiciously stripped metadata."""
        format_tags = self.format_info.get("tags", {})

        # Normal recordings usually have creation_time
        has_creation_time = "creation_time" in format_tags
        has_encoder = "encoder" in format_tags or "major_brand" in format_tags

        # Check total tag count
        total_tags = len(format_tags)
        for s in self.streams:
            total_tags += len(s.get("tags", {}))

        if total_tags == 0:
            self.findings.append({
                "finding_type": "missing_metadata",
                "confidence": 0.70,
                "description": "File has no metadata tags at all. Metadata may have been deliberately stripped.",
                "details": {"total_tags": 0},
            })
        elif not has_creation_time and not has_encoder:
            self.findings.append({
                "finding_type": "missing_metadata",
                "confidence": 0.50,
                "description": "No creation time or encoder information found.",
                "details": {"available_tags": list(format_tags.keys())},
            })

    def _check_container_inconsistency(self):
        """Check for container format vs codec mismatches."""
        format_name = self.format_info.get("format_name", "")

        for stream in self.streams:
            codec = stream.get("codec_name", "")
            codec_type = stream.get("codec_type", "")

            # AVI with H.265 is suspicious (unusual combination)
            if "avi" in format_name and codec == "hevc":
                self.findings.append({
                    "finding_type": "container_inconsistency",
                    "confidence": 0.75,
                    "description": "HEVC codec in AVI container is non-standard and may indicate re-muxing.",
                    "details": {"format": format_name, "codec": codec},
                })

            # MP4 with very old codecs
            if "mp4" in format_name and codec in ("mpeg1video", "mpeg2video"):
                self.findings.append({
                    "finding_type": "container_inconsistency",
                    "confidence": 0.60,
                    "description": f"Legacy codec ({codec}) in MP4 container suggests transcoding.",
                    "details": {"format": format_name, "codec": codec},
                })

    def _check_suspicious_tags(self):
        """Check for known editing software signatures."""
        format_tags = self.format_info.get("tags", {})
        encoder = format_tags.get("encoder", "").lower()

        editing_tools = ["ffmpeg", "handbrake", "premiere", "davinci", "avidemux", "virtualdub", "sox"]

        for tool in editing_tools:
            if tool in encoder:
                self.findings.append({
                    "finding_type": "editing_tool_detected",
                    "confidence": 0.40,
                    "description": f"Editing tool signature detected in metadata: '{encoder}'",
                    "details": {"encoder": encoder, "tool": tool},
                })
                break
