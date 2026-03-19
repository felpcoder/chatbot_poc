import json
import os
import tiktoken
import numpy as np
import faiss
from openai import OpenAI

# ----------------------------
# Configurações
# ----------------------------

api_key = os.getenv("API_KEY")
client = OpenAI(api_key=api_key)

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FOLDER = BASE_DIR / "base_conhecimento" / "silver"
EMBEDDINGS_FOLDER = BASE_DIR / "base_conhecimento" / "gold" / "embeddings"
VECTOR_STORE = BASE_DIR / "base_conhecimento" / "gold" / "vector_store"

MAX_TOKENS_POR_CHUNK = 1300

enc = tiktoken.get_encoding("cl100k_base")


# ----------------------------
# Rechunk
# ----------------------------

def rechunk_texto(texto: str, max_tokens: int = MAX_TOKENS_POR_CHUNK) -> list[str]:
    tokens = enc.encode(texto)

    if len(tokens) <= max_tokens:
        return [texto]

    return [
        enc.decode(tokens[i:i+max_tokens])
        for i in range(0, len(tokens), max_tokens)
    ]


# ----------------------------
# Embedding
# ----------------------------

def gerar_embedding(texto: str) -> list[float]:
    resp = client.embeddings.create(
        model="text-embedding-3-large",
        input=texto
    )
    return resp.data[0].embedding


# ----------------------------
# Texto enriquecido
# ----------------------------

def montar_texto_embedding(chunk: dict) -> str:
    return (
        chunk.get("titulo_documento", "") + "\n" +
        " > ".join(chunk.get("hierarquia", [])) + "\n\n" +
        chunk.get("texto", "")
    )


# ----------------------------
# ETAPA 1: gerar embeddings
# ----------------------------

def gerar_embeddings():
    os.makedirs(EMBEDDINGS_FOLDER, exist_ok=True)

    arquivos = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".json")]

    for file_name in arquivos:

        print(f"\nGerando embeddings: {file_name}")

        input_path = os.path.join(INPUT_FOLDER, file_name)
        output_path = os.path.join(
            EMBEDDINGS_FOLDER,
            file_name.replace(".json", "_embeddings.json")
        )

        with open(input_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        embeddings_data = []

        for c in chunks:

            texto = montar_texto_embedding(c)
            subchunks = rechunk_texto(texto)

            for idx, sub_texto in enumerate(subchunks):

                embedding = gerar_embedding(sub_texto)

                embeddings_data.append({
                    "chunk_id": c.get("chunk_id"),
                    "pdf": c.get("pdf"),
                    "pagina_inicio": c.get("pagina_inicio"),
                    "pagina_fim": c.get("pagina_fim"),
                    "subchunk_index": idx,
                    "texto": sub_texto,
                    "embedding": embedding
                })

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(embeddings_data, f, ensure_ascii=False)

        print(f"Salvo: {output_path}")


# ----------------------------
# ETAPA 2: criar FAISS
# ----------------------------

def criar_vector_store():
    print("\nCriando vector store...")

    todos_embeddings = []
    todos_metadados = []

    arquivos = [f for f in os.listdir(EMBEDDINGS_FOLDER) if f.endswith(".json")]

    for file_name in arquivos:

        path = os.path.join(EMBEDDINGS_FOLDER, file_name)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for e in data:
            todos_embeddings.append(e["embedding"])

            # remove embedding do metadata
            meta = {k: v for k, v in e.items() if k != "embedding"}
            todos_metadados.append(meta)

    embeddings_np = np.array(todos_embeddings, dtype="float32")

    # 🔥 normalização para cosine similarity
    faiss.normalize_L2(embeddings_np)

    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatIP(dimension)  # cosine
    index.add(embeddings_np)

    os.makedirs(VECTOR_STORE, exist_ok=True)

    faiss.write_index(index, os.path.join(VECTOR_STORE, "faiss.index"))

    with open(os.path.join(VECTOR_STORE, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(todos_metadados, f, ensure_ascii=False)

    print(f"Vector store criado com {len(todos_embeddings)} vetores")

    return index, todos_metadados


# ----------------------------
# Execução
# ----------------------------

if __name__ == "__main__":
    gerar_embeddings()
    criar_vector_store()