from rich import print as rprint

from aivideocut.configs import (
    CHAPTERS_YT_FILE_PATH,
    ORIGINAL_SRT_FILE_PATH,
    OUTPUT_DIR_PATH,
    PROMPT_MAX_CHARS,
)
from aivideocut.gem_prompts import create_youtube_chapters_prompt
from aivideocut.gem_utils import ask_gemini
from aivideocut.utils import (
    create_file_path,
    read_file_path,
    split_srt_blocks,
    write_str_to_file,
)


def gem_yt_chapters(*, dry_run: bool = False) -> None:
    srt_content = read_file_path(ORIGINAL_SRT_FILE_PATH)
    srt_blocks = split_srt_blocks(srt_content, max_chars=PROMPT_MAX_CHARS)

    response_text = ""
    response_model = ""
    for block in srt_blocks:
        current_block = "\n\n".join(block)
        prompt = create_youtube_chapters_prompt(
            current_block,
            (
                "Vídeo educacional mostrando exemplos de uso avançado de "
                "f-string no Python."
            ),
        )

        if dry_run:
            rprint(prompt, "\n\n")
            continue

        gemini_response = ask_gemini(prompt)
        gemini_response_text = gemini_response.text

        if gemini_response_text:
            response_text += gemini_response_text.strip()
            response_text += "\n"
            response_model = gemini_response.model_version

        rprint(response_text)

    if dry_run:
        return

    if not response_text:
        rprint("\n🔴 Gemini did not return the text")
        return

    rprint("\n\n")
    rprint(response_text)

    file = create_file_path(
        full_filename=CHAPTERS_YT_FILE_PATH.name,
        parent=OUTPUT_DIR_PATH,
        unique_filename=False,
        today_parent=False,
        separator="_",
    )
    write_str_to_file(response_text, path=file, create_parents=True)

    rprint(f"\n✅ Saved to: {file.name} (model = {response_model})")


if __name__ == "__main__":
    gem_yt_chapters(dry_run=False)
