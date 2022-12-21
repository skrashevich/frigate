"""Handles inserting and maintaining ffmpeg presets."""

from enum import Enum
from typing import Any

from frigate.version import VERSION

_user_agent_args = [
    "-user_agent",
    f"FFmpeg Frigate/{VERSION}",
]


class HwAccelTypeEnum(str, Enum):
    decode = "decode"
    encode = "encode"


PRESETS_HW_ACCEL_DECODE = {
    "preset-rpi-32-h264": ["-c:v", "h264_v4l2m2m"],
    "preset-rpi-64-h264": ["-c:v", "h264_v4l2m2m"],
    "preset-intel-vaapi": [
        "-hwaccel",
        "vaapi",
        "-hwaccel_device",
        "/dev/dri/renderD128",
        "-hwaccel_output_format",
        "yuv420p",
    ],
    "preset-intel-qsv-h264": ["-c:v", "h264_qsv"],
    "preset-intel-qsv-h265": ["-c:v", "hevc_qsv"],
    "preset-amd-vaapi": [
        "-hwaccel",
        "vaapi",
        "-hwaccel_device",
        "/dev/dri/renderD128",
        "-hwaccel_output_format",
        "yuv420p",
    ],
    "preset-nvidia-h264": ["-c:v", "h264_cuvid"],
    "preset-nvidia-h265": ["-c:v", "hevc_cuvid"],
    "preset-nvidia-mjpeg": ["-c:v", "mjpeg_cuvid"],
}

PRESET_DEFAULT_ENCODE = [
    "-c:v",
    "libx264",
    "-g",
    "50",
    "-profile:v",
    "high",
    "-level:v",
    "4.1",
    "-preset:v",
    "superfast",
    "-tune:v",
    "zerolatency",
]

PRESETS_HW_ACCEL_ENCODE = {
    "preset-rpi-64-h264": ["-c:v", "h264_v4l2m2m", "-g", "50", "-bf", "0"],
    "preset-intel-vaapi": [
        "-c:v",
        "h264_vaapi",
        "-g",
        "50",
        "-bf",
        "0",
        "-level:v",
        "4.1",
    ],
    "preset-intel-qsv-h264": ["-c:v", "h264_qsv"],
    "preset-intel-qsv-h265": ["-c:v", "hevc_qsv"],
    "preset-amd-vaapi": [
        "-c:v",
        "h264_vaapi",
    ],
    "preset-nvidia-h264": [
        "-c:v",
        "h264_nvenc",
        "-g",
        "50",
        "-profile:v",
        "high",
        "-level:v",
        "auto",
        "-preset:v",
        "p2",
        "-tune:v",
        "ll",
    ],
    "preset-nvidia-h265": [
        "-c:v",
        "hevc_nvenc",
        "-g",
        "50",
        "-profile:v",
        "high",
        "-level:v",
        "auto",
    ],
}


def parse_preset_hardware_acceleration(
    arg: Any, type: HwAccelTypeEnum = HwAccelTypeEnum.decode
) -> list[str]:
    """Return the correct preset if in preset format otherwise return None."""
    if not isinstance(arg, str):
        if type is HwAccelTypeEnum.encode:
            return PRESET_DEFAULT_ENCODE

        return None

    if type is HwAccelTypeEnum.encode:
        return PRESETS_HW_ACCEL_ENCODE.get(arg, PRESET_DEFAULT_ENCODE)

    return PRESETS_HW_ACCEL_DECODE.get(arg, None)


PRESETS_INPUT = {
    "preset-http-jpeg-generic": _user_agent_args
    + [
        "-r",
        "{}",
        "-stream_loop",
        "-1",
        "-f",
        "image2",
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "nobuffer",
        "-flags",
        "low_delay",
        "-strict",
        "experimental",
        "-fflags",
        "+genpts+discardcorrupt",
        "-use_wallclock_as_timestamps",
        "1",
    ],
    "preset-http-mjpeg-generic": _user_agent_args
    + [
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "nobuffer",
        "-flags",
        "low_delay",
        "-strict",
        "experimental",
        "-fflags",
        "+genpts+discardcorrupt",
        "-use_wallclock_as_timestamps",
        "1",
    ],
    "preset-http-reolink": _user_agent_args
    + [
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "+genpts+discardcorrupt",
        "-flags",
        "low_delay",
        "-strict",
        "experimental",
        "-analyzeduration",
        "1000M",
        "-probesize",
        "1000M",
        "-rw_timeout",
        "5000000",
    ],
    "preset-rtmp-generic": [
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "nobuffer",
        "-flags",
        "low_delay",
        "-strict",
        "experimental",
        "-fflags",
        "+genpts+discardcorrupt",
        "-rw_timeout",
        "5000000",
        "-use_wallclock_as_timestamps",
        "1",
        "-f",
        "live_flv",
    ],
    "preset-rtsp-generic": _user_agent_args
    + [
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "+genpts+discardcorrupt",
        "-rtsp_transport",
        "tcp",
        "-timeout",
        "5000000",
        "-use_wallclock_as_timestamps",
        "1",
    ],
    "preset-rtsp-udp": _user_agent_args
    + [
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "+genpts+discardcorrupt",
        "-rtsp_transport",
        "udp",
        "-timeout",
        "5000000",
        "-use_wallclock_as_timestamps",
        "1",
    ],
    "preset-rtsp-blue-iris": _user_agent_args
    + [
        "-user_agent",
        f"FFmpeg Frigate/{VERSION}",
        "-avoid_negative_ts",
        "make_zero",
        "-flags",
        "low_delay",
        "-strict",
        "experimental",
        "-fflags",
        "+genpts+discardcorrupt",
        "-rtsp_transport",
        "tcp",
        "-timeout",
        "5000000",
        "-use_wallclock_as_timestamps",
        "1",
    ],
}


def parse_preset_input(arg: Any, detect_fps: int) -> list[str]:
    """Return the correct preset if in preset format otherwise return None."""
    if not isinstance(arg, str):
        return None

    if arg == "preset-jpeg-generic":
        return PRESETS_INPUT[arg].format(f"{detect_fps}")

    return PRESETS_INPUT.get(arg, None)


PRESETS_RECORD_OUTPUT = {
    "preset-record-generic": [
        "-f",
        "segment",
        "-segment_time",
        "10",
        "-segment_format",
        "mp4",
        "-reset_timestamps",
        "1",
        "-strftime",
        "1",
        "-c",
        "copy",
        "-an",
    ],
    "preset-record-generic-audio": [
        "-f",
        "segment",
        "-segment_time",
        "10",
        "-segment_format",
        "mp4",
        "-reset_timestamps",
        "1",
        "-strftime",
        "1",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
    ],
    "preset-record-mjpeg": [
        "-f",
        "segment",
        "-segment_time",
        "10",
        "-segment_format",
        "mp4",
        "-reset_timestamps",
        "1",
        "-strftime",
        "1",
        "-c:v",
        "libx264",
        "-an",
    ],
    "preset-record-jpeg": [
        "-f",
        "segment",
        "-segment_time",
        "10",
        "-segment_format",
        "mp4",
        "-reset_timestamps",
        "1",
        "-strftime",
        "1",
        "-c:v",
        "libx264",
        "-an",
    ],
    "preset-record-ubiquiti": [
        "-f",
        "segment",
        "-segment_time",
        "10",
        "-segment_format",
        "mp4",
        "-reset_timestamps",
        "1",
        "-strftime",
        "1",
        "-c:v",
        "copy",
        "-ar",
        "44100",
        "-c:a",
        "aac",
    ],
}


def parse_preset_output_record(arg: Any) -> list[str]:
    """Return the correct preset if in preset format otherwise return None."""
    if not isinstance(arg, str):
        return None

    return PRESETS_RECORD_OUTPUT.get(arg, None)


PRESETS_RTMP_OUTPUT = {
    "preset-rtmp-generic": ["-c", "copy", "-f", "flv"],
    "preset-rtmp-mjpeg": ["-c:v", "libx264", "-an", "-f", "flv"],
    "preset-rtmp-jpeg": ["-c:v", "libx264", "-an", "-f", "flv"],
    "preset-rtmp-ubiquiti": [
        "-c:v",
        "copy",
        "-f",
        "flv",
        "-ar",
        "44100",
        "-c:a",
        "aac",
    ],
}


def parse_preset_output_rtmp(arg: Any) -> list[str]:
    """Return the correct preset if in preset format otherwise return None."""
    if not isinstance(arg, str):
        return None

    return PRESETS_RTMP_OUTPUT.get(arg, None)
