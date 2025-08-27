# pyright: basic


from rich import print as rprint

from aivideocut.configs import (
    OUTPUT_DIR_PATH,
    SEO_YT_FILE_PATH,
    SUMMARY_FILE_PATH,
)
from aivideocut.gem_prompts import create_youtube_seo_prompt
from aivideocut.gem_utils import ask_gemini
from aivideocut.utils import (
    create_file_path,
    read_file_path,
    write_str_to_file,
)


def gem_yt_seo() -> None:
    file = create_file_path(
        full_filename=SUMMARY_FILE_PATH.name,
        parent=OUTPUT_DIR_PATH,
        unique_filename=False,
        today_parent=False,
        separator="",
    )
    summary = read_file_path(file)

    prompt = create_youtube_seo_prompt(
        summary,
        ("Vídeo educacional mostrando exemplos de uso avançado de f-string no Python."),
    )

    gemini_response = ask_gemini(prompt)
    gemini_response_text = gemini_response.text

    if not gemini_response_text:
        print("DEU RUIM")
        return

    response_text = gemini_response_text.strip()

    rprint("\n\n")
    rprint(response_text)

    if response_text:
        file = create_file_path(
            full_filename=SEO_YT_FILE_PATH.name,
            parent=OUTPUT_DIR_PATH,
            unique_filename=False,
            today_parent=False,
            separator="",
        )

        write_str_to_file(response_text, path=file, create_parents=True)

        rprint(f"\n✅ Saved to: {file.name} (model = {gemini_response.model_version})")
    else:
        rprint("\n🔴 Gemini did not return the text")


if __name__ == "__main__":
    gem_yt_seo()
