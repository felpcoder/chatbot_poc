"""
pdf_chunker_rag.py
==================
Pipeline de extração e chunking de PDFs para RAG (Retrieval-Augmented Generation).

Funcionalidades:
  1. Metadados ricos  – título do doc, seção atual, hierarquia de headings,
                        número de página e posição relativa no documento.
  2. Chunking semântico – respeitando parágrafos e quebras de seção em vez de
                          cortar por página.
  3. Limpeza de ruído  – remoção automática de cabeçalhos/rodapés repetitivos.
  4. Overlap entre chunks – janela deslizante configurável para preservar
                            continuidade de contexto.
  5. Extração resiliente – integração com pdf_quality_handler para PDFs
                           escaneados, OCR ruim e layouts complexos.
"""

import fitz  # PyMuPDF
import os
import json
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from typing import Optional

from pdf_quality_handler import (
    extrair_documento_resiliente,
    QualidadePagina,
    RelatorioQualidade,
)

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


OUTPUT_FOLDER = BASE_DIR / "base_conhecimento" / "silver"
INPUT_FOLDER = BASE_DIR / "base_conhecimento" / "raw"


RELATORIO_PATH = os.path.join(OUTPUT_FOLDER, "_relatorio_qualidade.json")

# Tamanho alvo de cada chunk (em caracteres)
CHUNK_SIZE = 1000
# Sobreposição entre chunks consecutivos (em caracteres)
CHUNK_OVERLAP = 200
# Frequência mínima para considerar uma linha como cabeçalho/rodapé repetitivo
HEADER_FOOTER_FREQ_THRESHOLD = 0.4  # presente em > 40 % das páginas → ruído


# ---------------------------------------------------------------------------
# Estrutura de dados
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    # Identificação
    chunk_id: str = ""           # "<pdf_stem>_p<pagina_inicio>_c<idx>"
    pdf: str = ""
    # Metadados de posição
    pagina_inicio: int = 0
    pagina_fim: int = 0
    posicao_relativa: float = 0.0  # 0.0 (início) → 1.0 (fim do doc)
    # Hierarquia semântica
    titulo_documento: str = ""
    secao: str = ""
    subsecao: str = ""
    hierarquia: list[str] = field(default_factory=list)
    # Qualidade da extração
    qualidade_extracao: str = ""   # "ok" | "ocr" | "reocr" | "complexo"
    metodo_extracao: str = ""      # método real usado pelo handler
    tem_tabelas: bool = False
    # Conteúdo
    texto: str = ""
    num_caracteres: int = 0
    # Contexto vizinho
    chunk_anterior_preview: str = ""
    chunk_proximo_preview: str = ""


# ---------------------------------------------------------------------------
# 1. Detecção de headings via heurística de fonte
# ---------------------------------------------------------------------------

_HEADING_PATTERNS = [
    re.compile(r"^(\d+\.){1,3}\s+\S"),
    re.compile(r"^(art(igo)?|cl[aá]usula|cap[íi]tulo|se[çc][aã]o|§)\s*\d+", re.I),
    re.compile(r"^[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ\s\d\-:]{5,80}$"),
]


def _detectar_headings_por_fonte(page: fitz.Page) -> list[tuple[float, int, str]]:
    """Retorna lista de (y_pos, nivel, texto) para cada bloco que parece heading."""
    blocos = page.get_text("dict")["blocks"]
    spans_com_fonte: list[tuple[float, float, str]] = []

    for bloco in blocos:
        if bloco.get("type") != 0:
            continue
        for linha in bloco.get("lines", []):
            for span in linha.get("spans", []):
                txt = span["text"].strip()
                if not txt:
                    continue
                spans_com_fonte.append((span["size"], bloco["bbox"][1], txt))

    if not spans_com_fonte:
        return []

    tamanhos = sorted({s[0] for s in spans_com_fonte}, reverse=True)
    mapa_nivel = {t: i + 1 for i, t in enumerate(tamanhos[:3])}

    return [
        (y, mapa_nivel[size], txt)
        for size, y, txt in spans_com_fonte
        if size in mapa_nivel and len(txt) <= 120
    ]


def _e_heading_textual(linha: str) -> bool:
    linha = linha.strip()
    if not linha or len(linha) > 120:
        return False
    return any(p.match(linha) for p in _HEADING_PATTERNS)


# ---------------------------------------------------------------------------
# 2. Limpeza de ruído (cabeçalhos/rodapés repetitivos)
#    Nota: limpeza de OCR já é feita pelo pdf_quality_handler
# ---------------------------------------------------------------------------

def _coletar_linhas_repetitivas(textos: list[str]) -> set[str]:
    contagem: dict[str, int] = {}
    total = len(textos)
    for texto in textos:
        linhas_unicas = {l.strip() for l in texto.splitlines() if l.strip()}
        for linha in linhas_unicas:
            contagem[linha] = contagem.get(linha, 0) + 1

    limiar = max(2, int(total * HEADER_FOOTER_FREQ_THRESHOLD))
    return {l for l, c in contagem.items() if c >= limiar}


def _limpar_texto(texto: str, ruido: set[str]) -> str:
    linhas = []
    for linha in texto.splitlines():
        ls = linha.strip()
        if ls in ruido:
            continue
        if re.fullmatch(r"[-–—]?\s*\d+\s*[-–—]?|p[aá]gina\s*\d+", ls, re.I):
            continue
        linhas.append(linha)

    texto_limpo = "\n".join(linhas)
    texto_limpo = re.sub(r"\n{3,}", "\n\n", texto_limpo)
    texto_limpo = re.sub(r"[ \t]{2,}", " ", texto_limpo)
    return texto_limpo.strip()


# ---------------------------------------------------------------------------
# 3. Estrutura interna de página (pós-handler)
# ---------------------------------------------------------------------------

@dataclass
class _PaginaInfo:
    numero: int
    texto_limpo: str
    headings: list[tuple[float, int, str]]
    qualidade: QualidadePagina = QualidadePagina.OK
    metodo_extracao: str = "pymupdf_nativo"
    tem_tabelas: bool = False


def _titulo_documento(doc: fitz.Document, primeira_pagina_texto: str) -> str:
    meta = doc.metadata or {}
    titulo = meta.get("title", "").strip()
    if titulo and titulo.lower() not in ("untitled", ""):
        return titulo
    for linha in primeira_pagina_texto.splitlines():
        linha = linha.strip()
        if len(linha) > 5:
            return linha[:120]
    return ""


# ---------------------------------------------------------------------------
# 4. Chunking semântico com overlap
# ---------------------------------------------------------------------------

def _paragrafo_split(texto: str) -> list[str]:
    paragrafos: list[str] = []
    atual: list[str] = []

    for linha in texto.splitlines():
        if not linha.strip():
            if atual:
                paragrafos.append("\n".join(atual).strip())
                atual = []
        elif _e_heading_textual(linha) and atual:
            paragrafos.append("\n".join(atual).strip())
            atual = [linha]
        else:
            atual.append(linha)

    if atual:
        paragrafos.append("\n".join(atual).strip())

    return [p for p in paragrafos if p]


def _montar_chunks(
    paginas: list[_PaginaInfo],
    titulo_doc: str,
    pdf_nome: str,
) -> list[Chunk]:
    hierarquia: dict[int, str] = {}
    unidades: list[tuple[int, str, dict, str, str, bool]] = []
    total_paginas = paginas[-1].numero if paginas else 1

    _QUALIDADE_STR = {
        QualidadePagina.OK:        "ok",
        QualidadePagina.ESCANEADA: "ocr",
        QualidadePagina.OCR_RUIM:  "reocr",
        QualidadePagina.COMPLEXA:  "complexo",
    }

    for pinfo in paginas:
        for _, nivel, htxt in sorted(pinfo.headings):
            hierarquia[nivel] = htxt
            for sub in list(hierarquia):
                if sub > nivel:
                    del hierarquia[sub]

        qualidade_str = _QUALIDADE_STR.get(pinfo.qualidade, "ok")

        for par in _paragrafo_split(pinfo.texto_limpo):
            unidades.append((
                pinfo.numero,
                par,
                dict(hierarquia),
                qualidade_str,
                pinfo.metodo_extracao,
                pinfo.tem_tabelas,
            ))

    chunks: list[Chunk] = []
    buffer_texto: list[str] = []
    buffer_chars = 0
    buffer_paginas: list[int] = []
    buffer_hier: dict = {}
    buffer_qualidade = "ok"
    buffer_metodo = "pymupdf_nativo"
    buffer_tabelas = False
    chunk_idx = 0

    def _fechar_chunk(overlap_texto: str = "") -> None:
        nonlocal chunk_idx, buffer_texto, buffer_chars
        nonlocal buffer_paginas, buffer_hier
        nonlocal buffer_qualidade, buffer_metodo, buffer_tabelas

        if not buffer_texto:
            return

        texto = "\n\n".join(buffer_texto)
        h = buffer_hier
        pdf_stem = os.path.splitext(pdf_nome)[0]
        p_inicio = buffer_paginas[0] if buffer_paginas else 0
        p_fim    = buffer_paginas[-1] if buffer_paginas else 0

        chunks.append(Chunk(
            chunk_id=f"{pdf_stem}_p{p_inicio}_c{chunk_idx:04d}",
            pdf=pdf_nome,
            pagina_inicio=p_inicio,
            pagina_fim=p_fim,
            posicao_relativa=round(p_fim / total_paginas, 4),
            titulo_documento=titulo_doc,
            secao=h.get(1, ""),
            subsecao=h.get(2, ""),
            hierarquia=[h[k] for k in sorted(h)],
            qualidade_extracao=buffer_qualidade,
            metodo_extracao=buffer_metodo,
            tem_tabelas=buffer_tabelas,
            texto=texto,
            num_caracteres=len(texto),
        ))
        chunk_idx += 1

        if overlap_texto:
            buffer_texto = [overlap_texto]
            buffer_chars = len(overlap_texto)
        else:
            buffer_texto = []
            buffer_chars = 0
        buffer_paginas = []
        buffer_hier = {}
        buffer_qualidade = "ok"
        buffer_metodo = "pymupdf_nativo"
        buffer_tabelas = False

    for pagina_num, par, hier, qualidade, metodo, tabelas in unidades:
        par_len = len(par)

        # Parágrafo muito grande: divide por sentenças
        if par_len > CHUNK_SIZE * 1.5:
            sentencas = re.split(r"(?<=[.!?;])\s+", par)
            for sent in sentencas:
                if buffer_chars + len(sent) > CHUNK_SIZE and buffer_texto:
                    overlap = buffer_texto[-1][-CHUNK_OVERLAP:] if buffer_texto else ""
                    _fechar_chunk(overlap)
                buffer_texto.append(sent)
                buffer_chars += len(sent)
                buffer_paginas.append(pagina_num)
                buffer_hier = dict(hier)
                buffer_qualidade = qualidade
                buffer_metodo = metodo
                buffer_tabelas = buffer_tabelas or tabelas
            continue

        # Chunk cheio: fecha e inicia com overlap
        if buffer_chars + par_len > CHUNK_SIZE and buffer_texto:
            if buffer_texto:
                overlap = buffer_texto[-1][-CHUNK_OVERLAP:]
                overlap = re.sub(r"^\S*\s", "", overlap) 
            else:
                overlap = ""

        buffer_texto.append(par)
        buffer_chars += par_len
        buffer_paginas.append(pagina_num)
        buffer_hier = dict(hier)
        buffer_qualidade = qualidade
        buffer_metodo = metodo
        buffer_tabelas = buffer_tabelas or tabelas

    _fechar_chunk()

    # Previews de contexto vizinho
    for i, chunk in enumerate(chunks):
        if i > 0:
            chunk.chunk_anterior_preview = (
                chunks[i - 1].texto[-80:].replace("\n", " ").strip()
            )
        if i < len(chunks) - 1:
            chunk.chunk_proximo_preview = (
                chunks[i + 1].texto[:80].replace("\n", " ").strip()
            )

    return chunks


# ---------------------------------------------------------------------------
# 5. Pipeline principal
# ---------------------------------------------------------------------------

def processar_pdf(pdf_path: str, output_folder: str) -> tuple[int, RelatorioQualidade]:
    """
    Extrai, limpa e chunka um PDF usando extração resiliente.

    Returns:
        (número de chunks gerados, RelatorioQualidade)
    """
    pdf_nome = os.path.basename(pdf_path)
    pdf_stem = os.path.splitext(pdf_nome)[0]

    # --- Extração resiliente (handler cuida de scan/OCR/colunas/tabelas) ---
    resultados, relatorio = extrair_documento_resiliente(pdf_path)

    if not resultados:
        return 0, relatorio

    # --- Limpeza de cabeçalhos/rodapés repetitivos ---
    textos_brutos = [r.texto for r in resultados]
    ruido = _coletar_linhas_repetitivas(textos_brutos)

    # --- Monta _PaginaInfo com headings re-detectados ---
    with fitz.open(pdf_path) as doc:
        paginas: list[_PaginaInfo] = []

        for resultado in resultados:
            texto_limpo = _limpar_texto(resultado.texto, ruido)
            if not texto_limpo:
                continue

            # Headings por fonte só funcionam em PDFs com texto nativo
            if resultado.qualidade == QualidadePagina.ESCANEADA:
                headings = []  # Tesseract não preserva informação de fonte
            else:
                try:
                    page = doc[resultado.numero - 1]
                    headings = _detectar_headings_por_fonte(page)
                except Exception:
                    headings = []

            paginas.append(_PaginaInfo(
                numero=resultado.numero,
                texto_limpo=texto_limpo,
                headings=headings,
                qualidade=resultado.qualidade,
                metodo_extracao=resultado.metodo_usado,
                tem_tabelas=resultado.tem_tabelas,
            ))

        if not paginas:
            return 0, relatorio

        titulo_doc = _titulo_documento(doc, paginas[0].texto_limpo)
        chunks = _montar_chunks(paginas, titulo_doc, pdf_nome)

        output_path = os.path.join(output_folder, f"chunks_{pdf_stem}.json")
        os.makedirs(output_folder, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in chunks], f, ensure_ascii=False, indent=2)

        return len(chunks), relatorio


def main() -> None:
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    arquivos = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".pdf")]

    if not arquivos:
        print(f"Nenhum PDF encontrado em {INPUT_FOLDER}")
        return

    print(f"{len(arquivos)} PDF(s) encontrado(s) em {INPUT_FOLDER}\n")

    total_chunks = 0
    relatorios: list[dict] = []

    for file_name in sorted(arquivos):
        pdf_path = os.path.join(INPUT_FOLDER, file_name)
        print(f"Processando: {file_name}")

        n, relatorio = processar_pdf(pdf_path, OUTPUT_FOLDER)
        total_chunks += n

        print(f"  {relatorio.resumo()}")
        print(f"  → {n} chunks salvos\n")

        relatorios.append({
            "pdf": relatorio.pdf,
            "total_paginas": relatorio.total_paginas,
            "chunks_gerados": n,
            "paginas_ok": relatorio.paginas_ok,
            "paginas_escaneadas": relatorio.paginas_escaneadas,
            "paginas_ocr_ruim": relatorio.paginas_ocr_ruim,
            "paginas_complexas": relatorio.paginas_complexas,
            "paginas_vazias": relatorio.paginas_vazias,
            "avisos": relatorio.avisos_por_pagina,
        })

    # Salva relatório consolidado de qualidade
    with open(RELATORIO_PATH, "w", encoding="utf-8") as f:
        json.dump(relatorios, f, ensure_ascii=False, indent=2)

    print(f"Extração concluída.")
    print(f"  Total de chunks : {total_chunks}")
    print(f"  Relatório salvo : {RELATORIO_PATH}")


if __name__ == "__main__":
    main()