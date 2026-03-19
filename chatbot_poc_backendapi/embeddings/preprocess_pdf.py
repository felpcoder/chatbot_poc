import fitz  # PyMuPDF
import os
import json
def extrair_texto(pdf_path):
    """
    Extrai texto de um PDF, retornando uma lista de dicionários com:
    - pdf: nome do arquivo
    - pagina: número da página
    - texto: conteúdo textual da página
    """
    doc = fitz.open(pdf_path)
    texto_completo = []
    for num_pagina, pagina in enumerate(doc, start=1):
        texto = pagina.get_text("text")
        if texto.strip():
            texto_completo.append({
                "pdf": os.path.basename(pdf_path),
                "pagina": num_pagina,
                "texto": texto.strip()
            })
    return texto_completo

name_file = "Machine learning-driven credit risk a systemic review"
# Caminho do PDF
pdf_path = f"base_conhecimento/raw/{name_file}.pdf"

# Extrair texto
chunks = extrair_texto(pdf_path)

# Salvar em JSON
output_path = f"base_conhecimento/silver/chunks_{name_file}.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)  # cria pasta se não existir

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

print(f"{len(chunks)} chunks salvos em {output_path}")
