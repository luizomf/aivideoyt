# pyright: basic

from rich import print as rprint

from aivideocut.configs import (
    OUTPUT_DIR_PATH,
    PROMPT_MAX_CHARS,
    SRT_FIXED_ENGLISH_FILENAME,
    SRT_FIXED_FILENAME,
)
from aivideocut.gem_prompts import (
    create_translate_srt_pt_to_en_prompt,
)
from aivideocut.gem_utils import ask_gemini
from aivideocut.utils import (
    create_file_path,
    read_file_path,
    split_srt_blocks,
    write_str_to_file,
)


def gem_translate_srt_to_pt_br() -> None:
    fixed_srt_path = create_file_path(
        full_filename=SRT_FIXED_FILENAME,
        parent=OUTPUT_DIR_PATH,
        unique_filename=False,
        today_parent=False,
        separator="",
    )
    srt_content = read_file_path(fixed_srt_path)
    srt_blocks = split_srt_blocks(srt_content, max_chars=PROMPT_MAX_CHARS)

    response_text = ""
    for block in srt_blocks:
        current_block = "\n\n".join(block)
        prompt = create_translate_srt_pt_to_en_prompt(
            current_block,
            (
                "Vídeo educacional mostrando exemplos de uso avançado de "
                "f-string no Python."
            ),
        )

        gemini_response = ask_gemini(prompt)
        gemini_response_text = gemini_response.text

        if gemini_response_text:
            response_text += gemini_response_text.strip()
            response_text += "\n\n"

        rprint(response_text)

    if not response_text:
        rprint("\n🔴 Gemini did not return the text")
        return

    rprint("\n\n")
    rprint(response_text)

    file = create_file_path(
        full_filename=SRT_FIXED_ENGLISH_FILENAME,
        parent=OUTPUT_DIR_PATH,
        unique_filename=False,
        today_parent=False,
        separator="",
    )
    write_str_to_file(response_text, path=file, create_parents=True)

    rprint(f"\n✅ Saved to: {file.name} (model = {gemini_response.model_version})")


if __name__ == "__main__":
    gem_translate_srt_to_pt_br()
