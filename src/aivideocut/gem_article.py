# pyright: basic

from rich import print as rprint

from aivideocut.configs import (
    ARTICLE_FILE_PATH,
    OUTPUT_DIR_PATH,
    PROMPT_MAX_CHARS,
    SRT_FIXED_FILENAME,
)
from aivideocut.gem_prompts import create_technical_explanation_prompt
from aivideocut.gem_utils import ask_gemini
from aivideocut.utils import (
    create_file_path,
    extract_text_from_srt,
    read_file_path,
    smart_text_split,
    write_str_to_file,
)


def gem_create_article(*, dry_run: bool = False) -> None:
    fixed_srt_path = create_file_path(
        full_filename=SRT_FIXED_FILENAME,
        parent=OUTPUT_DIR_PATH,
        unique_filename=False,
        today_parent=False,
        separator="",
    )
    srt_content = read_file_path(fixed_srt_path)
    extracted_srt_text = extract_text_from_srt(srt_content)

    text_chunks = smart_text_split(
        extracted_srt_text, approx_max_chars=PROMPT_MAX_CHARS
    )

    response_text = ""
    for text in text_chunks:
        prompt = create_technical_explanation_prompt(
            text,
            (
                "Vídeo educacional mostrando exemplos de uso avançado de "
                "f-string no Python."
            ),
        )

        if dry_run:
            rprint(prompt, "\n\n---\n\n")
            continue

        gemini_response = ask_gemini(prompt)
        gemini_response_text = gemini_response.text

        if gemini_response_text:
            response_text += gemini_response_text.strip()
            response_text += "\n\n"

        rprint(response_text)

    if dry_run:
        return

    if not response_text:
        rprint("\n🔴 Gemini did not return the text")
        return

    rprint("\n\n")
    rprint(response_text)

    file = create_file_path(
        full_filename=ARTICLE_FILE_PATH.name,
        parent=OUTPUT_DIR_PATH,
        unique_filename=False,
        today_parent=False,
        separator="_",
    )
    write_str_to_file(response_text, path=file, create_parents=True)

    rprint(f"\n✅ Saved to: {file.name} (model = {gemini_response.model_version})")


if __name__ == "__main__":
    gem_create_article()
