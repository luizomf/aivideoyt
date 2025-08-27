import re
from pathlib import Path
from typing import Literal, TypeAlias

whisper_model_size = "large-v2"

transcribe = {
    "language": "pt",
    "temperature": 0,
    "beam_size": 1,
    "word_timestamps": True,
    # "clip_timestamps": [0, 60],
}

GeminiModels: TypeAlias = Literal[
    # Família Gemini 1.5
    # 1.5-flash-8b
    # * Descrição: Versão mais leve (8 bilhões de parâmetros) do Gemini 1.5 Flash.
    #   Projetado para ser extremamente eficiente em custo e rápido, à custa de
    #   uma capacidade de raciocínio ou complexidade um pouco menor.
    # * Custo: Muito baixo. Geralmente o mais barato por token.
    # * Velocidade: Muito rápido.
    # * Casos de Uso: Tarefas que exigem o mínimo de custo e máxima velocidade,
    #   mas que não dependem de raciocínio complexo ou precisão super alta.
    #   Você notou que não funcionou muito bem para o seu caso, o que é esperado
    #   para tarefas que exigem um pouco mais de "inteligência".
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash-8b-001",  # Versão específica numerada
    "gemini-1.5-flash-8b-latest",  # Ponteiro para a versão mais recente e estável do 8B
    # 1.5-pro
    # * Descrição: O modelo "Pro" da geração 1.5. Robusto e versátil.
    #   Oferece raciocínio complexo e capacidade multimodal (texto, imagem, áudio,
    #   vídeo).
    # * Custo: Mais caro que o Flash, mas mais barato que o 2.5 Pro.
    # * Velocidade: Boa, mas não tão otimizado para velocidade quanto o Flash.
    # * Casos de Uso: Ideal para tarefas que exigem raciocínio aprofundado, geração
    #   de conteúdo criativo, análise de dados complexos, e quando a janela de
    #   contexto de 1M de tokens é necessária.
    "gemini-1.5-pro",
    "gemini-1.5-pro-002",  # Versão específica numerada
    "gemini-1.5-pro-latest",  # Ponteiro para a versão mais recente e estável do 1.5 Pro
    # 1.5-flash
    # * Descrição: O modelo "Flash" da geração 1.5. Excelente equilíbrio entre
    #   custo, velocidade e capacidade razoável. Possui a janela de contexto de
    #   1M de tokens.
    # * Custo: Muito baixo (ligeiramente mais caro que o 8B, mas ainda sim
    #   muito competitivo).
    # * Velocidade: Muito rápido.
    # * Casos de Uso: Seu "cavalo de batalha" para grande volume, resumos, traduções,
    #   e geração de texto onde a qualidade "aceitável/boa" é suficiente.
    #   Um dos melhores custo-benefício para muitas aplicações.
    "gemini-1.5-flash",
    "gemini-1.5-flash-002",  # Versão específica numerada
    "gemini-1.5-flash-latest",  # Ponteiro para a versão mais recente e estável
    # Família Gemini 2.0 (Nova Geração, com Melhorias Fundamentais)
    # * Oferecem raciocínio aprimorado, melhor compreensão de nuances e multimodalidade.
    # * Podem ser o "sweet spot" de custo-benefício para muitos, entregando
    #   mais "inteligência"
    #   que o 1.5 Flash por um custo ainda razoável.
    # 2.0-flash
    # * Descrição: O modelo "Flash" da geração 2.0. Baseado em uma arquitetura
    #   mais recente.
    #   Oferece melhor raciocínio e compreensão que o 1.5 Flash, mantendo
    #   boa velocidade.
    # * Custo: Baixo (ligeiramente mais caro que o 1.5 Flash, mas geralmente
    #   justificado pela melhoria de qualidade).
    # * Velocidade: Rápido.
    # * Casos de Uso: Para quando o 1.5 Flash não é "top" o suficiente, e você precisa
    #   de um modelo mais inteligente sem o custo do Pro. Parece ser seu "sweet spot"
    #   de custo-benefício para muitas tarefas.
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",  # Versão específica numerada
    # 2.0-flash-lite
    # * Descrição: Versão "Lite" do Gemini 2.0 Flash. Otimizado para ser ainda mais
    #   leve e econômico. Pode ter algumas capacidades reduzidas para atingir a
    #   eficiência máxima.
    # * Custo: Muito baixo para entrada (input), mas o custo por token de saída (output)
    #   pode ser surprisingly alto para certos SKUs, como você viu no extrato.
    # * Velocidade: Muito rápido.
    # * Casos de Uso: Tarefas onde o custo é extremamente crítico e a complexidade
    #   da saída é baixa, ou o volume de saída é pequeno.
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",  # Versão específica numerada
    # Família Gemini 2.5 (As Itensões Mais Recentes da Geração 2.x)
    # * Representam os desenvolvimentos mais recentes em Flash e Pro, potencialmente
    #   com otimizações ou novas funcionalidades. Muitas vezes em "preview"
    #   inicialmente.
    # 2.5-flash
    # * Descrição: Uma iteração mais recente e aprimorada do Gemini Flash.
    #   Pode oferecer melhorias sutis em qualidade ou eficiência sobre o 2.0 Flash.
    # * Custo: Mais caro que o 2.0 Flash, especialmente para output.
    # * Velocidade: Rápido.
    # * Casos de Uso: Se o 2.0 Flash não estiver entregando exatamente a qualidade
    #   desejada e você precisar de um "boost" no modelo Flash, e estiver disposto
    #   a pagar um pouco mais.
    "gemini-2.5-flash",
    # 2.5-pro
    # * Descrição: Uma iteração mais recente e aprimorada do Gemini Pro. Representa
    #   o cutting edge em raciocínio, complexidade e multimodalidade.
    # * Custo: O mais caro por token entre os modelos listados para uso geral.
    # * Velocidade: Boa, mas prioriza a capacidade sobre a velocidade bruta.
    # * Casos de Uso: Para as tarefas mais exigentes e críticas, onde o custo
    #   é secundário à qualidade e à capacidade de raciocínio complexo.
    #   Se o 2.5 Flash não for suficiente para tarefas de SEO ou geração criativa
    #   altamente complexa.
    "gemini-2.5-pro",
]

DEFAULT_GEMINI_MODEL: GeminiModels = "gemini-1.5-flash-latest"
PROMPT_MAX_CHARS = 6000

OUTPUT_DIR_NAME = "transcriptions"

OUTPUT_DIR_PATH = Path(OUTPUT_DIR_NAME).resolve()
ORIGINAL_SRT_FILE_PATH = OUTPUT_DIR_PATH / "original_transcription.srt"

SRT_FIXED_FILENAME = "new_transcription_fixed.srt"
SRT_FIXED_ENGLISH_FILENAME = "transcription_fixed_english.srt"

SUMMARY_FILE_PATH = OUTPUT_DIR_PATH / "summary.md"
SEO_YT_FILE_PATH = OUTPUT_DIR_PATH / "seo_yt.md"
CHAPTERS_YT_FILE_PATH = OUTPUT_DIR_PATH / "chapters_yt.md"
ARTICLE_FILE_PATH = OUTPUT_DIR_PATH / "article.md"

ONE_LINE_RE = re.compile(r"(?:\r?\n)")
DOUBLE_LINE_RE = re.compile(r"(?:\r?\n){2}")

ANY_SPACE_RE = re.compile(r"\s+")
ENDING_DOT_RE = re.compile(r"([.!?])(?=\s|$)")
