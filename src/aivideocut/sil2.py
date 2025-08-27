# pyright: basic
# ruff: noqa: S603,ERA001
import json
import re
import time
from collections import namedtuple
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from subprocess import run
from typing import Literal, ParamSpec, TypeVar

import av
from rich.console import Console
from silero_vad import get_speech_timestamps, load_silero_vad, read_audio
from smartcut.__main__ import Progress, parse_time_segments
from smartcut.cut_video import (
    MediaContainer,
    VideoExportMode,
    VideoExportQuality,
    VideoSettings,
    smart_cut,
)
from smartcut.misc_data import AudioExportInfo, AudioExportSettings

from aivideocut.utils import SpeechTimestamps, ajust_vad_speech_timestamps

console = Console(highlight=False, style="cyan")
rprint = console.print

ROOT_DIR = Path(__file__).parent.parent.parent
FFMPEG_LOG_LEVEL = Literal[
    "quiet",
    "panic",
    "fatal",
    "error",
    "warning",
    "info",
    "verbose",
    "debug",
    "trace",
]

FilePaths = namedtuple(
    "FilePaths",
    [
        "in_file",
        "in_dir",
        "in_name",
        "in_ext",
        "out_file",
        "out_dir",
        "out_name",
        "out_ext",
    ],
)


def join(args: list[str | Path]) -> str:
    return " ".join([f"{s}" for s in args])


def get_ffmpeg_cmd(log_level: FFMPEG_LOG_LEVEL = "warning") -> list[str]:
    return ["ffmpeg", "-hide_banner", "-loglevel", log_level, "-stats"]


def ffmpeg_fix_codecs(
    *, input_file: Path, output_file: Path, dry_run: bool = True
) -> Path:
    ffmpeg_cmd = get_ffmpeg_cmd(log_level="info")

    # fmt: off
    ffmpeg_cmd = [
        *ffmpeg_cmd,
        "-i", input_file,
        "-c:v", "libx264", "-crf", "13", "-preset", "fast",
        "-c:a", "aac", "-b:a", "512k",
        "-movflags", "+faststart", "-fflags", "+genpts",
        output_file
    ]
    # fmt: on

    rprint(
        "🎬 ffmpeg fix codecs:",
        f"[code]{join(ffmpeg_cmd)}[/code]",
        "\n\n",
    )

    if dry_run:
        return output_file

    run(ffmpeg_cmd)

    return output_file


def ffmpeg_audio_normalization(
    *,
    input_file: Path,
    output_file: Path,
    loudnorm_i: str = "-14",
    loudnorm_tp: str = "-2.0",
    loudnorm_lra: str = "11",
    dry_run: bool = False,
) -> Path:
    # fmt: off
    ffmpeg_cmd = get_ffmpeg_cmd(log_level="info")
    ffmpeg_audio_normalization = [
        *ffmpeg_cmd,
        "-i", input_file,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "512k",
        "-af",
        f"loudnorm=I={loudnorm_i}:TP={loudnorm_tp}:LRA={loudnorm_lra}:print_format=json",
        "-f", "null",
        "-",
    ]
    # fmt: on

    rprint(
        "🔉 Normalization first pass:",
        f"[code]{join(ffmpeg_audio_normalization)}[/code]\n\n",
    )

    ffmpeg_normalization_output = run(
        ffmpeg_audio_normalization,
        capture_output=True,
        text=True,
        check=False,
    )
    stderr_output = ffmpeg_normalization_output.stderr
    found_loud_norm_output = re.search(
        r"(?:\[Parsed_loudnorm.*?\].*)(\{.*?\})",
        stderr_output,
        re.DOTALL | re.MULTILINE,
    )

    if found_loud_norm_output:
        raw_loud_norm_json = found_loud_norm_output.group(1)
        parsed_loud_norm = json.loads(raw_loud_norm_json)

        measured_i = parsed_loud_norm["input_i"]
        measured_lra = parsed_loud_norm["input_lra"]
        measured_tp = parsed_loud_norm["input_tp"]
        measured_thresh = parsed_loud_norm["input_thresh"]
        target_offset = parsed_loud_norm["target_offset"]

        # fmt: off
        ffmpeg_audio_normalization = [
            *ffmpeg_cmd,
            "-i", input_file,
            "-c:v", "copy",
            "-af",
            (
                f"loudnorm=I={loudnorm_i}:TP={loudnorm_tp}:LRA={loudnorm_lra}:"
                f"measured_I={measured_i}:"
                f"measured_LRA={measured_lra}:measured_TP={measured_tp}:measured_thresh={measured_thresh}:"
                f"offset={target_offset}:linear=true:print_format=summary"
            ),
            "-c:a", "aac", "-b:a", "512k",
            output_file,
            "-y",
        ]
        # fmt: on
        #
        rprint("🔉 Normalization data:", parsed_loud_norm, "\n\n")
        rprint(
            "🔉 Normalization second pass:",
            f"[code]{join(ffmpeg_audio_normalization)}[/code]",
            "\n\n",
        )

        if dry_run:
            return output_file

        run(ffmpeg_audio_normalization)

        return output_file
    return output_file


def auto_editor_cut_silences(
    *, input_file: Path, output_file: Path, dry_run: bool = False
) -> Path:
    # fmt: off
    auto_editor_bin = ROOT_DIR / ".." /  "autoeditorlatest"/".venv"/"bin"/"auto-editor"
    auto_editor_silence_cut  = [
        # "/Users/luizotavio/Desktop/tutoriais_e_cursos/autoeditorlatest/.venv/bin/auto-editor",
        str(auto_editor_bin),
        # "--edit", "audio:threshold=0.02,stream=all,mincut=30", # OLD
        "--edit", "audio:threshold=0.04,stream=all,mincut=30",
        "--margin", "0.2s,0.3s",
        input_file,
        "-o", output_file,
        "-c:v", "libx264", "-b:v", "16M", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "512k",
        "--progress", "modern", # choices: modern, classic, ascii, machine, none
        "--faststart",
        "--no-open",
        "-dn", "-sn",
        # "--debug",
        "--add-in", "0,2sec", # keep first 2 seconds
        "--add-in", "-2sec,end", # keep last 5 seconds
        # "--no-seek",
        # "--preview",
    ]
    # fmt: on
    rprint("🏁 auto editor:", f"[code]{join(auto_editor_silence_cut)}[/code]", "\n\n")

    if dry_run:
        return output_file

    run(auto_editor_silence_cut)
    rprint(join(auto_editor_silence_cut), "\n\n")

    return output_file


def silero_get_speech_pauses(
    *, input_file: Path, output_file: Path, dry_run: bool = False
) -> tuple[SpeechTimestamps, Path]:
    ffmpeg_input_to_wav = [
        *get_ffmpeg_cmd(),
        "-i",
        input_file,
        output_file,
        "-y",
    ]

    if dry_run:
        rprint(join(ffmpeg_input_to_wav), "\n\n")
        return [], output_file

    rprint(join(ffmpeg_input_to_wav), "\n\n")
    run(ffmpeg_input_to_wav)

    silero_model = load_silero_vad()
    audio_data = read_audio(str(output_file))
    silero_speech_timestamps = get_speech_timestamps(
        audio_data,
        silero_model,
        threshold=0.5,
        sampling_rate=16000,
        min_speech_duration_ms=100,  # old 150
        max_speech_duration_s=float("inf"),
        min_silence_duration_ms=50,  # old 100
        speech_pad_ms=30,
        return_seconds=True,
    )
    rprint("🤖 SILERO VAD Output:", silero_speech_timestamps, "\n\n")

    proccessed_silero_timestamps = ajust_vad_speech_timestamps(
        silero_speech_timestamps,
        # OLD
        # min_speech_length_secs=0.5,
        # pad_start_secs=0.03,
        # pad_end_secs=0.04,
        min_speech_length_secs=0.2,
        pad_start_secs=0.01,
        pad_end_secs=0.01,
    )
    rprint(
        "⏳ Processed timestamps with ajust_vad_speech_timestamps:",
        proccessed_silero_timestamps,
        "\n\n",
    )

    return proccessed_silero_timestamps, output_file


def smartcut_cut_by_second_timestamps(
    *,
    input_path: Path,
    output_path: Path,
    speech_timestamps: SpeechTimestamps,
    dry_run: bool = False,
) -> Path:
    smartcut_seconds_to_keep = ",".join(
        [f"{t['start']},{t['end']}" for t in speech_timestamps]
    )
    if dry_run:
        return output_path

    rprint("⏱️ Smartcut timestamps:", smartcut_seconds_to_keep, "\n\n")

    smartcut_media_source = MediaContainer(input_path)
    smartcut_segments = parse_time_segments(smartcut_seconds_to_keep)

    # Default audio settings: no mix, include all tracks with lossless passthru
    smartcut_audio_settings = [AudioExportSettings(codec="passthru")] * len(
        smartcut_media_source.audio_tracks
    )
    smartcut_export_info = AudioExportInfo(output_tracks=smartcut_audio_settings)  # pyright: ignore

    smartcut_video_settings = VideoSettings(
        VideoExportMode.SMARTCUT,
        VideoExportQuality.NEAR_LOSSLESS,
        None,  # pyright: ignore
    )

    smartcut_progress = Progress()

    smartcut_log_level = "info"
    av.logging.set_level(av.logging.INFO)  # pyright: ignore

    smartcut_exception_value = smart_cut(
        smartcut_media_source,
        smartcut_segments,
        str(output_path),
        audio_export_info=smartcut_export_info,
        video_settings=smartcut_video_settings,
        progress=smartcut_progress,
        log_level=smartcut_log_level,
    )

    smartcut_progress.tqdm.close()  # pyright: ignore

    if smartcut_exception_value is not None:
        raise smartcut_exception_value

    rprint(
        f"👏 Smart cut completed successfully. Output saved to {output_path}", "\n\n"
    )

    return output_path


P = ParamSpec("P")
T_Ret = TypeVar("T_Ret")


def get_time_elapsed(func: Callable[P, T_Ret]) -> Callable[P, T_Ret]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T_Ret:
        start_time = time.perf_counter()

        result = func(*args, **kwargs)

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        minutes, seconds = divmod(elapsed_time, 60)

        rprint(
            f"✅ Function {func.__name__} Total Time: {int(minutes)}min {seconds:.2f}s",
            "\n\n",
        )

        return result

    return wrapper


def create_in_out_paths(
    *, input_path: Path, suffix: str, sep: str = "_", new_file_ext: str | None = None
) -> FilePaths:
    in_file_path = input_path.resolve()
    parent_dir = in_file_path.parent
    in_file_name = in_file_path.stem
    in_file_ext = in_file_path.suffix
    out_file_ext = new_file_ext if new_file_ext is not None else in_file_ext
    out_file_name = f"{in_file_name}{sep}{suffix}{out_file_ext}"
    out_file_path = in_file_path.with_name(out_file_name)

    return FilePaths(
        in_file=in_file_path,
        in_dir=parent_dir,
        in_name=in_file_name,
        in_ext=in_file_ext,
        out_file=out_file_path,
        out_dir=parent_dir,
        out_ext=out_file_ext,
        out_name=out_file_name,
    )


@get_time_elapsed
def run_single_file(
    *,
    input_path: Path,
    dry_run: bool = False,
    normalize_audio: bool = True,
    cut_audio_silences: bool = True,
    cut_speech_silences: bool = True,
    fix_codecs: bool = True,
) -> list[Path]:
    files_processed = []
    in_path = input_path.resolve()

    if not in_path.is_file():
        raise FileNotFoundError(in_path)

    source_filename = in_path.name
    source_fileext = in_path.suffix
    source_filestem = in_path.stem
    source_dirname = in_path.parent
    output_dir = source_dirname / f"{source_filestem}_{source_fileext[1:]}"
    output_dir.mkdir(parents=True, exist_ok=True)

    current_input_path = in_path
    current_output_path = output_dir / source_filename

    if fix_codecs:
        current_output_path = current_output_path.with_stem("00_FIX_CODECS")

        ffmpeg_fix_codecs(
            input_file=current_input_path,
            output_file=current_output_path,
            dry_run=dry_run,
        )

        files_processed.append(current_output_path)
        current_input_path = current_output_path

    if normalize_audio:
        current_output_path = current_output_path.with_stem("01_NORMALIZED")

        ffmpeg_audio_normalization(
            input_file=current_input_path,
            output_file=current_output_path,
            dry_run=dry_run,
        )

        files_processed.append(current_output_path)
        current_input_path = current_output_path

    if cut_audio_silences:
        current_output_path = current_output_path.with_stem("02_AE_CUT")

        auto_editor_cut_silences(
            input_file=current_input_path,
            output_file=current_output_path,
            dry_run=dry_run,
        )

        files_processed.append(current_output_path)
        current_input_path = current_output_path

    if cut_speech_silences:
        current_output_path = current_output_path.with_stem("04_FINAL")

        speech_timestamps, _ = silero_get_speech_pauses(
            input_file=current_input_path,
            output_file=current_input_path.with_name("03_SILERO.wav"),
            dry_run=dry_run,
        )
        smartcut_cut_by_second_timestamps(
            input_path=current_input_path,
            output_path=current_output_path,
            speech_timestamps=speech_timestamps,
            dry_run=dry_run,
        )

        files_processed.append(current_output_path)
        current_input_path = current_output_path

    return files_processed


@get_time_elapsed
def run_many_files(
    *,
    input_path: Path,
    dry_run: bool = False,
    normalize_audio: bool = True,
    cut_audio_silences: bool = True,
    cut_speech_silences: bool = True,
    fix_codecs: bool = True,
) -> None:
    in_path = input_path.resolve()
    allowed_extensions = [".mp4", ".mov", ".mkv"]
    files_processed = []

    if not in_path.is_dir():
        raise NotADirectoryError(input_path)

    files = list(in_path.rglob("**/*.*"))
    for file in files:
        file_ext = file.suffix

        if file in files_processed:
            rprint("🙅 File skipped (PROCESSED):", file)
            continue

        if file_ext not in allowed_extensions:
            rprint("🤷‍♀️ File skipped:", file)
            continue

        rprint("📋 FILE", file)
        files_processed += run_single_file(
            input_path=file,
            fix_codecs=fix_codecs,
            normalize_audio=normalize_audio,
            cut_audio_silences=cut_audio_silences,
            cut_speech_silences=cut_speech_silences,
            dry_run=dry_run,
        )


if __name__ == "__main__":
    input_path = Path("/Users/luizotavio/Desktop/videos/")
    run_many_files(
        input_path=input_path,
        fix_codecs=False,
        normalize_audio=True,
        cut_audio_silences=True,
        cut_speech_silences=True,
        dry_run=False,
    )

    # input_path = Path("/users/luizotavio/desktop/videos/smaller.mp4")
    # out = run_single_file(
    #     input_path=input_path,
    #     fix_codecs=True,
    #     normalize_audio=True,
    #     cut_audio_silences=True,
    #     cut_speech_silences=True,
    #     dry_run=False
    # )
    # print()
    # print(out)
