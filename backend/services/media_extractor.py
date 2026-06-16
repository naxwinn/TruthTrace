"""
Media Extraction Service
Decomposes uploaded media files into analyzable components:
- Video frames (as images)
- Audio track (WAV)
- Metadata (JSON via FFprobe)
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional
from config import settings


def _get_ffmpeg_path():
    """Find ffmpeg in system PATH."""
    # Refresh PATH to include newly installed tools
    system_path = os.environ.get("Path", "") or os.environ.get("PATH", "")
    machine_path = ""
    user_path = ""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
            machine_path = winreg.QueryValueEx(key, "Path")[0]
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
            user_path = winreg.QueryValueEx(key, "Path")[0]
    except Exception:
        pass

    combined = f"{system_path};{machine_path};{user_path}"
    os.environ["PATH"] = combined
    return combined


# Ensure ffmpeg is findable
_get_ffmpeg_path()


class MediaExtractor:
    def __init__(self, media_path: str, job_id: str):
        self.media_path = Path(media_path)
        self.job_id = job_id
        self.output_dir = settings.storage_dir / "extractions" / job_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def frames_dir(self) -> Path:
        d = self.output_dir / "frames"
        d.mkdir(exist_ok=True)
        return d

    @property
    def audio_path(self) -> Path:
        return self.output_dir / "audio.wav"

    @property
    def metadata_path(self) -> Path:
        return self.output_dir / "metadata.json"

    def extract_all(self) -> dict:
        """Run full extraction pipeline."""
        results = {
            "metadata": self.extract_metadata(),
            "audio": self.extract_audio(),
            "frames": self.extract_frames(),
        }
        return results

    def extract_metadata(self) -> dict:
        """Extract metadata using FFprobe."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(self.media_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return {"error": result.stderr}

        metadata = json.loads(result.stdout)

        # Save to file
        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return {
            "path": str(self.metadata_path),
            "format": metadata.get("format", {}).get("format_name"),
            "duration": float(metadata.get("format", {}).get("duration", 0)),
            "streams": len(metadata.get("streams", [])),
        }

    def extract_audio(self) -> dict:
        """Extract audio track as WAV."""
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(self.media_path),
            "-vn",              # No video
            "-acodec", "pcm_s16le",
            "-ar", "22050",     # 22.05kHz sample rate for analysis
            "-ac", "1",         # Mono
            str(self.audio_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            # File might be video-only
            if "does not contain any stream" in result.stderr:
                return {"path": None, "error": "no_audio_stream"}
            return {"path": None, "error": result.stderr[:500]}

        return {
            "path": str(self.audio_path),
            "size": self.audio_path.stat().st_size,
        }

    def extract_frames(self, fps: float = 2.0) -> dict:
        """Extract video frames at specified FPS."""
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(self.media_path),
            "-vf", f"fps={fps}",
            "-q:v", "2",
            str(self.frames_dir / "frame_%05d.jpg"),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            if "does not contain any stream" in result.stderr:
                return {"path": None, "count": 0, "error": "no_video_stream"}
            return {"path": None, "count": 0, "error": result.stderr[:500]}

        frame_count = len(list(self.frames_dir.glob("frame_*.jpg")))
        return {
            "path": str(self.frames_dir),
            "count": frame_count,
            "fps": fps,
        }

    def get_gop_structure(self) -> Optional[list]:
        """Extract GOP (Group of Pictures) structure for video forensics.
        Uses -skip_frame nokey to only parse keyframes for speed on large files.
        """
        # First try fast keyframe-only extraction
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-select_streams", "v:0",
            "-skip_frame", "nokey",
            "-show_frames",
            "-show_entries", "frame=pict_type,pts_time,key_frame",
            "-print_format", "json",
            str(self.media_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        frames = data.get("frames", [])

        # If we got keyframes, also do a lightweight packet-level scan for full GOP structure
        if frames:
            packet_cmd = [
                "ffprobe",
                "-v", "quiet",
                "-select_streams", "v:0",
                "-show_packets",
                "-show_entries", "packet=flags,pts_time",
                "-print_format", "json",
                str(self.media_path),
            ]
            packet_result = subprocess.run(packet_cmd, capture_output=True, text=True, timeout=300)
            if packet_result.returncode == 0:
                packet_data = json.loads(packet_result.stdout)
                packets = packet_data.get("packets", [])
                # Convert packets to frame-like structure for GOP analysis
                frame_list = []
                for pkt in packets:
                    is_key = 1 if "K" in pkt.get("flags", "") else 0
                    frame_list.append({
                        "key_frame": is_key,
                        "pict_type": "I" if is_key else "P",
                        "pts_time": pkt.get("pts_time", "0"),
                    })
                frames = frame_list

        gop_path = self.output_dir / "gop_structure.json"
        with open(gop_path, "w") as f:
            json.dump(frames, f, indent=2)

        return frames

    def get_compression_info(self) -> Optional[dict]:
        """Extract compression/encoding details."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries",
            "stream=codec_name,profile,level,bit_rate,r_frame_rate,avg_frame_rate",
            "-print_format", "json",
            str(self.media_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        return streams[0] if streams else None
