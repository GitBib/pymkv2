from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pymkv import MKVTrack

type_files = {
    "video": {
        "V_MPEG1": "mpg",
        "V_MPEG2": "mpg",
        "V_MPEG4/ISO/AVC": "264",
        "MPEG-4p10": "h264",
        "HEVC": "h265",
        "V_MS/VFW/FOURCC": "avi",
        "V_REAL": "rm",
        "V_THEORA": "ogg",
        "V_VP8": "ivf",
        "V_VP9": "ivf",
        "AVC/H.264/MPEG-4p10": "mp4",
    },
    "audio": {
        "AAC": "aac",
        "AC3": "ac3",
        "AC-3": "ac3",
        "ALAC": "caf",
        "DTS": "dts",
        "FLAC": "flac",
        "MPEG/L2": "mp2",
        "MPEG/L3": "mp3",
        "OPUS": "ogg",
        "PCM": "wav",
        "REAL": "ra",
        "TRUEHD": "thd",
        "MLP": "mlp",
        "TTA1": "tta",
        "VORBIS": "ogg",
        "WAVPACK4": "wv",
        "V_MS/VFW/FOURCC, WVC1": "wvc",
        "VC-1": "wvc",
        "Vorbis": "ogg",
    },
    "subtitles": {
        "PGS": "sup",
        "ASS": "ass",
        "SSA": "ssa",
        "UTF8": "srt",
        "SubRip/SRT": "srt",
        "ASCII": "srt",
        "VOBSUB": "sub",
        "USF": "usf",
        "WEBVTT": "vtt",
    },
}


def get_track_extension(track: MKVTrack) -> str | None:
    """
    Get the file extension for a given MKVTrack.

    Parameters
    ----------
    track : MKVTrack
        The MKVTrack object from which to determine the file extension.

    Returns
    -------
    str | None
        The file extension corresponding to the track's type and codec, or None if not found.

    Notes
    -----
    This function uses the track's type and codec to look up the appropriate
    file extension in the `type_files` dictionary. If no matching extension
    is found, it returns None.
    """
    track_type = track.track_type
    track_codec = track.track_codec
    if track_type in type_files and track_codec in type_files[track_type]:
        return type_files[track_type][track_codec]
    return None
