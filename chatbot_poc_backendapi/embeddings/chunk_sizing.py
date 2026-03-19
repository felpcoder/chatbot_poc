import json
import os
import tiktoken

INPUT_FOLDER = "base_conhecimento/silver"
OUTPUT_FOLDER = "base_conhecimento/gold"
MAX_TOKENS_POR_CHUNK = 1300

enc = tiktoken.encoding_for_model("gpt-3.5-turbo")


def _rechunkear_chunk(chunk: dict, enc: tiktoken.Encoding, max_tokens: int) -> list[dict]:
    """Divide um chunk em subchunks respeitando o limite de tokens.

    Se o chunk couber dentro do limite, é retornado intacto com
    ``subchunk_index`` 0. Caso contrário, é fatiado em subchunks
    sequenciais de até ``max_tokens`` tokens cada.

    Args:
        chunk: Dicionário com ao menos os campos ``texto``, ``pdf`` e ``pagina``.
        enc: Codificador tiktoken usado para tokenizar e decodificar o texto.
        max_tokens: Número máximo de tokens por subchunk.

    Returns:
        list[dict]: Lista de subchunks, cada um com os campos
            ``pdf``, ``pagina``, ``subchunk_index`` e ``texto``.
    """
    texto = chunk["texto"]
    tokens = enc.encode(texto)
    num_tokens = len(tokens)

    if num_tokens <= max_tokens:
        return [{
            "pdf": chunk.get("pdf"),
            "pagina": chunk.get("pagina"),
            "subchunk_index": 0,
            "texto": texto
        }]

    subchunks = []
    for i in range(0, num_tokens, max_tokens):
        sub_tokens = tokens[i:i + max_tokens]
        sub_texto = enc.decode(sub_tokens)
        subchunks.append({
            "pdf": chunk.get("pdf"),
            "pagina": chunk.get("pagina"),
            "subchunk_index": i // max_tokens,
            "texto": sub_texto
        })
    return subchunks


def _processar_arquivo(input_path: str, output_path: str, enc: tiktoken.Encoding, max_tokens: int) -> int:
    """Lê um arquivo JSON, rechunka seus chunks e salva o resultado.

    Args:
        input_path: Caminho completo do arquivo JSON de entrada.
        output_path: Caminho completo do arquivo JSON de saída.
        enc: Codificador tiktoken usado para tokenizar e decodificar o texto.
        max_tokens: Número máximo de tokens por subchunk.

    Returns:
        int: Total de subchunks gerados e salvos no arquivo de saída.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        chunks_originais = json.load(f)

    chunks_rechunked = []
    for chunk in chunks_originais:
        chunks_rechunked.extend(_rechunkear_chunk(chunk, enc, max_tokens))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks_rechunked, f, ensure_ascii=False, indent=2)

    return len(chunks_rechunked)


def main() -> None:
    """Processa todos os arquivos JSON da pasta silver, gerando chunks na pasta gold.

    Itera sobre os arquivos ``.json`` em ``INPUT_FOLDER``, aplica o rechunking
    respeitando ``MAX_TOKENS_POR_CHUNK`` e salva os resultados em ``OUTPUT_FOLDER``.

    Returns:
        None
    """
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    for file_name in os.listdir(INPUT_FOLDER):
        if not file_name.endswith(".json"):
            continue

        input_path = os.path.join(INPUT_FOLDER, file_name)
        output_path = os.path.join(OUTPUT_FOLDER, file_name.replace(".json", "_rechunked.json"))

        total = _processar_arquivo(input_path, output_path, enc, MAX_TOKENS_POR_CHUNK)
        print(f"{file_name} → {total} chunks salvos")


if __name__ == "__main__":
    main()