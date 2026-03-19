"""
pdf_quality_handler.py
======================
Camada de detecção de qualidade e extração resiliente para PDFs problemáticos.

Problemas tratados:
  1. PDF escaneado (imagem pura)  → OCR via Tesseract (fallback)
  2. OCR ruim embutido            → detecção por heurística + re-OCR seletivo
  3. Layout complexo              → extração de tabelas via pdfplumber +
                                    reordenação de colunas

Dependências extras:
    pip install pdfplumber pytesseract Pillow

O Tesseract engine também precisa estar instalado no sistema:
    Ubuntu/Debian : sudo apt install tesseract-ocr tesseract-ocr-por
    macOS         : brew install tesseract
    Windows       : https://github.com/UB-Mannheim/tesseract/wiki
"""

from __future__ import annotations

import io
import logging
import os
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

import fitz  # PyMuPDF

# Imports opcionais com fallback gracioso
try:
    import pdfplumber
    PDFPLUMBER_OK = True
except ImportError:
    PDFPLUMBER_OK = False
    logging.warning("pdfplumber não encontrado. Extração de tabelas desativada.")

try:
    from PIL import Image
    import pytesseract
    TESSERACT_OK = True
except ImportError:
    TESSERACT_OK = False
    logging.warning("pytesseract/Pillow não encontrados. OCR de fallback desativado.")


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

# Idiomas do Tesseract (ajuste conforme sua base)
TESSERACT_LANG = "por+eng"
# DPI para rasterização de páginas escaneadas
RASTER_DPI = 300
# Limiar de chars por página para considerar texto suficiente
MIN_CHARS_VALIDO = 50
# Limiar de "lixo": ratio de caracteres não-alfanuméricos para sinalizar OCR ruim
MAX_RATIO_LIXO = 0.35


# ---------------------------------------------------------------------------
# Enumeração de qualidade
# ---------------------------------------------------------------------------

class QualidadePagina(Enum):
    OK = auto()           # texto digital nativo, bom
    OCR_RUIM = auto()     # tem texto mas parece corrompido/lixo
    ESCANEADA = auto()    # sem texto extraível (imagem pura)
    COMPLEXA = auto()     # colunas/tabelas detectadas


# ---------------------------------------------------------------------------
# Diagnóstico de qualidade
# ---------------------------------------------------------------------------

@dataclass
class DiagnosticoPagina:
    numero: int
    qualidade: QualidadePagina
    texto_extraido: str = ""
    tem_tabelas: bool = False
    tem_colunas: bool = False
    metodo_usado: str = "pymupdf_nativo"
    avisos: list[str] = field(default_factory=list)


def _ratio_lixo(texto: str) -> float:
    """Calcula proporção de chars que não são letra, número ou pontuação comum."""
    if not texto:
        return 1.0
    lixo = sum(
        1 for c in texto
        if not (c.isalnum() or c in " \n\t.,;:!?()[]{}\"'-–—/\\@#%&*+=<>°ºª")
        and unicodedata.category(c) not in ("Ll", "Lu", "Lt", "Nd", "Zs")
    )
    return lixo / len(texto)


def _detectar_colunas(page: fitz.Page) -> bool:
    """
    Heurística simples: se há blocos de texto cuja coordenada X inicial
    varia muito (> 30% da largura), provavelmente há colunas.
    """
    blocos = page.get_text("dict").get("blocks", [])
    xs = [b["bbox"][0] for b in blocos if b.get("type") == 0]
    if len(xs) < 4:
        return False
    largura = page.rect.width
    spread = max(xs) - min(xs)
    return spread > largura * 0.30


def diagnosticar_pagina(
    page: fitz.Page,
    plumber_page=None,  # pdfplumber page, opcional
) -> DiagnosticoPagina:
    """
    Analisa uma página e retorna seu diagnóstico de qualidade.
    """
    num = page.number + 1
    texto_bruto = page.get_text("text").strip()
    avisos: list[str] = []

    # --- Sem texto: escaneada ---
    if len(texto_bruto) < MIN_CHARS_VALIDO:
        return DiagnosticoPagina(
            numero=num,
            qualidade=QualidadePagina.ESCANEADA,
            texto_extraido="",
            metodo_usado="—",
            avisos=["Página sem texto extraível (possível scan)"],
        )

    # --- Texto com muito lixo: OCR ruim embutido ---
    ratio = _ratio_lixo(texto_bruto)
    if ratio > MAX_RATIO_LIXO:
        avisos.append(f"OCR ruim detectado (ratio_lixo={ratio:.2f})")
        return DiagnosticoPagina(
            numero=num,
            qualidade=QualidadePagina.OCR_RUIM,
            texto_extraido=texto_bruto,
            metodo_usado="pymupdf_nativo",
            avisos=avisos,
        )

    # --- Detecção de tabelas ---
    tem_tabelas = False
    if plumber_page is not None and PDFPLUMBER_OK:
        try:
            tabelas = plumber_page.extract_tables()
            tem_tabelas = bool(tabelas)
        except Exception as e:
            avisos.append(f"pdfplumber falhou na detecção de tabelas: {e}")

    # --- Detecção de colunas ---
    tem_colunas = _detectar_colunas(page)

    if tem_tabelas or tem_colunas:
        return DiagnosticoPagina(
            numero=num,
            qualidade=QualidadePagina.COMPLEXA,
            texto_extraido=texto_bruto,
            tem_tabelas=tem_tabelas,
            tem_colunas=tem_colunas,
            metodo_usado="pymupdf_nativo",
            avisos=avisos,
        )

    # --- OK ---
    return DiagnosticoPagina(
        numero=num,
        qualidade=QualidadePagina.OK,
        texto_extraido=texto_bruto,
        metodo_usado="pymupdf_nativo",
        avisos=avisos,
    )


# ---------------------------------------------------------------------------
# Estratégias de extração por qualidade
# ---------------------------------------------------------------------------

def _ocr_pagina(page: fitz.Page, dpi: int = RASTER_DPI) -> str:
    """
    Rasteriza a página e aplica Tesseract OCR.
    Requer pytesseract + Pillow instalados.
    """
    if not TESSERACT_OK:
        logger.error("pytesseract não disponível. Instale: pip install pytesseract Pillow")
        return ""

    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    texto = pytesseract.image_to_string(img, lang=TESSERACT_LANG)
    return texto.strip()


def _extrair_tabelas_plumber(plumber_page) -> str:
    """
    Extrai tabelas via pdfplumber e as serializa em Markdown
    (formato amigável para LLMs de RAG).
    """
    if not PDFPLUMBER_OK or plumber_page is None:
        return ""

    partes: list[str] = []
    try:
        tabelas = plumber_page.extract_tables()
        for tabela in tabelas:
            if not tabela:
                continue
            linhas_md: list[str] = []
            for i, linha in enumerate(tabela):
                # Substitui None por vazio
                celulas = [str(c or "").replace("\n", " ").strip() for c in linha]
                linhas_md.append("| " + " | ".join(celulas) + " |")
                if i == 0:
                    # Linha separadora do header Markdown
                    linhas_md.append("|" + "|".join(["---"] * len(celulas)) + "|")
            partes.append("\n".join(linhas_md))
    except Exception as e:
        logger.warning(f"Erro ao extrair tabelas com pdfplumber: {e}")

    return "\n\n".join(partes)


def _extrair_colunas_ordenadas(page: fitz.Page) -> str:
    """
    Extrai texto de página com colunas respeitando a ordem de leitura
    (esquerda→direita, depois cima→baixo dentro de cada coluna).
    """
    blocos = page.get_text("dict").get("blocks", [])
    largura = page.rect.width
    meio = largura / 2

    coluna_esq: list[tuple[float, str]] = []
    coluna_dir: list[tuple[float, str]] = []

    for bloco in blocos:
        if bloco.get("type") != 0:
            continue
        x0 = bloco["bbox"][0]
        y0 = bloco["bbox"][1]
        txt = " ".join(
            span["text"]
            for linha in bloco.get("lines", [])
            for span in linha.get("spans", [])
        ).strip()
        if not txt:
            continue
        if x0 < meio:
            coluna_esq.append((y0, txt))
        else:
            coluna_dir.append((y0, txt))

    texto_esq = "\n".join(t for _, t in sorted(coluna_esq))
    texto_dir = "\n".join(t for _, t in sorted(coluna_dir))

    if texto_dir:
        return texto_esq + "\n\n" + texto_dir
    return texto_esq


# ---------------------------------------------------------------------------
# Interface pública: extração resiliente por página
# ---------------------------------------------------------------------------

@dataclass
class ResultadoPagina:
    numero: int
    texto: str
    qualidade: QualidadePagina
    metodo_usado: str
    tem_tabelas: bool = False
    avisos: list[str] = field(default_factory=list)


def extrair_pagina_resiliente(
    page: fitz.Page,
    plumber_page=None,
) -> ResultadoPagina:
    """
    Extrai o texto de uma página usando a estratégia mais adequada
    conforme a qualidade detectada automaticamente.

    Fluxo de decisão:
        ESCANEADA  → OCR via Tesseract
        OCR_RUIM   → re-OCR via Tesseract (substitui o texto corrompido)
        COMPLEXA   → colunas ordenadas + tabelas em Markdown
        OK         → texto nativo do PyMuPDF
    """
    diag = diagnosticar_pagina(page, plumber_page)
    num = diag.numero
    avisos = diag.avisos[:]

    if diag.qualidade == QualidadePagina.ESCANEADA:
        logger.info(f"  Pág. {num}: escaneada → aplicando OCR")
        texto = _ocr_pagina(page)
        metodo = "tesseract_ocr"
        if not texto:
            avisos.append("OCR não produziu texto. Página ignorada.")

    elif diag.qualidade == QualidadePagina.OCR_RUIM:
        logger.info(f"  Pág. {num}: OCR ruim detectado → re-OCR")
        texto_ocr = _ocr_pagina(page)
        # Usa o OCR novo só se for melhor que o texto já embutido
        if texto_ocr and _ratio_lixo(texto_ocr) < _ratio_lixo(diag.texto_extraido):
            texto = texto_ocr
            metodo = "tesseract_reocr"
            avisos.append("Texto substituído por re-OCR (qualidade superior)")
        else:
            texto = diag.texto_extraido
            metodo = "pymupdf_nativo_ocr_ruim"
            avisos.append("Re-OCR não melhorou qualidade; mantido texto original")

    elif diag.qualidade == QualidadePagina.COMPLEXA:
        logger.info(f"  Pág. {num}: layout complexo → extração especializada")
        partes: list[str] = []

        if diag.tem_colunas:
            partes.append(_extrair_colunas_ordenadas(page))
            avisos.append("Colunas reordenadas para leitura linear")

        if diag.tem_tabelas and plumber_page is not None:
            tabelas_md = _extrair_tabelas_plumber(plumber_page)
            if tabelas_md:
                partes.append("<!-- TABELA -->\n" + tabelas_md)
                avisos.append("Tabela(s) extraída(s) em Markdown")

        texto = "\n\n".join(p for p in partes if p) or diag.texto_extraido
        metodo = "layout_complexo"

    else:  # OK
        texto = diag.texto_extraido
        metodo = "pymupdf_nativo"

    return ResultadoPagina(
        numero=num,
        texto=texto.strip(),
        qualidade=diag.qualidade,
        metodo_usado=metodo,
        tem_tabelas=diag.tem_tabelas,
        avisos=avisos,
    )


# ---------------------------------------------------------------------------
# Função de alto nível: processa doc inteiro com relatório de qualidade
# ---------------------------------------------------------------------------

@dataclass
class RelatorioQualidade:
    pdf: str
    total_paginas: int
    paginas_ok: int = 0
    paginas_escaneadas: int = 0
    paginas_ocr_ruim: int = 0
    paginas_complexas: int = 0
    paginas_vazias: int = 0
    avisos_por_pagina: dict[int, list[str]] = field(default_factory=dict)

    def resumo(self) -> str:
        return (
            f"{self.pdf} | {self.total_paginas} pág. | "
            f"OK={self.paginas_ok} | "
            f"Scan={self.paginas_escaneadas} | "
            f"OCR_ruim={self.paginas_ocr_ruim} | "
            f"Complexas={self.paginas_complexas} | "
            f"Vazias={self.paginas_vazias}"
        )


def extrair_documento_resiliente(
    pdf_path: str,
) -> tuple[list[ResultadoPagina], RelatorioQualidade]:
    """
    Processa todas as páginas de um PDF com extração resiliente.

    Returns:
        (lista de ResultadoPagina, RelatorioQualidade)
    """
    doc = fitz.open(pdf_path)
    pdf_nome = os.path.basename(pdf_path)
    total = len(doc)

    rel = RelatorioQualidade(pdf=pdf_nome, total_paginas=total)
    resultados: list[ResultadoPagina] = []

    # Abre pdfplumber em paralelo se disponível
    plumber_doc = None
    if PDFPLUMBER_OK:
        try:
            plumber_doc = pdfplumber.open(pdf_path)
        except Exception as e:
            logger.warning(f"pdfplumber não conseguiu abrir {pdf_nome}: {e}")

    try:
        for i, page in enumerate(doc):
            plumber_page = plumber_doc.pages[i] if plumber_doc else None
            resultado = extrair_pagina_resiliente(page, plumber_page)

            if not resultado.texto:
                rel.paginas_vazias += 1
                continue

            resultados.append(resultado)

            if resultado.avisos:
                rel.avisos_por_pagina[resultado.numero] = resultado.avisos

            match resultado.qualidade:
                case QualidadePagina.OK:
                    rel.paginas_ok += 1
                case QualidadePagina.ESCANEADA:
                    rel.paginas_escaneadas += 1
                case QualidadePagina.OCR_RUIM:
                    rel.paginas_ocr_ruim += 1
                case QualidadePagina.COMPLEXA:
                    rel.paginas_complexas += 1
    finally:
        if plumber_doc:
            plumber_doc.close()

    return resultados, rel


# ---------------------------------------------------------------------------
# Integração com pdf_chunker_rag.py
# ---------------------------------------------------------------------------
# Para usar no pipeline principal, substitua a chamada de extração no
# pdf_chunker_rag.py:
#
#   # ANTES (somente PyMuPDF):
#   paginas = _extrair_paginas(doc, ruido)
#
#   # DEPOIS (com handler resiliente):
#   from pdf_quality_handler import extrair_documento_resiliente
#
#   resultados, relatorio = extrair_documento_resiliente(pdf_path)
#   print(f"  {relatorio.resumo()}")
#
#   # Converte ResultadoPagina → _PaginaInfo para o chunker
#   paginas = [
#       _PaginaInfo(
#           numero=r.numero,
#           texto_limpo=r.texto,   # já resiliente, sem ruído de OCR
#           headings=[],           # headings são re-detectados pelo chunker
#       )
#       for r in resultados
#   ]
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if len(sys.argv) < 2:
        print("Uso: python pdf_quality_handler.py <caminho_do_pdf>")
        sys.exit(1)

    path = sys.argv[1]
    print(f"\nAnalisando: {path}\n{'─' * 50}")
    resultados, relatorio = extrair_documento_resiliente(path)

    print(relatorio.resumo())
    if relatorio.avisos_por_pagina:
        print("\nAvisos por página:")
        for pag, avisos in sorted(relatorio.avisos_por_pagina.items()):
            for aviso in avisos:
                print(f"  pág. {pag}: {aviso}")

    print(f"\nTotal de páginas com conteúdo: {len(resultados)}")