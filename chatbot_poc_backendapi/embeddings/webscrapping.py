import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────

BASE_URL   = "https://learn.microsoft.com"
START_URL  = "https://learn.microsoft.com/pt-br/azure/databricks/"
MAX_PAGES  = 9999
DELAY      = 1.0

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_PATH = BASE_DIR / "base_conhecimento" / "raw" / "databricks"
SILVER_PATH = BASE_DIR / "base_conhecimento" / "silver" / "databricks"

RAW_PATH.mkdir(parents=True, exist_ok=True)
SILVER_PATH.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pt-BR,pt;q=0.9"
}


# ── HTTP ───────────────────────────────────────────────────────────────

def get_soup(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"Erro: {url} → {e}")
        return None


# ── Utils ──────────────────────────────────────────────────────────────

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def split_chunks(text, max_chars=800):
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""

    for s in sentences:
        if len(current) + len(s) <= max_chars:
            current += (" " if current else "") + s
        else:
            chunks.append(current)
            current = s

    if current:
        chunks.append(current)

    return chunks


def extract_links(soup):
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(BASE_URL, a["href"]).split("#")[0]
        if "/azure/databricks" in href:
            links.add(href)
    return list(links)


# ── RAW (Bronze) ───────────────────────────────────────────────────────

def parse_raw(soup, url):
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else "Sem título"

    main = soup.find("main") or soup.body

    content = []
    for tag in main.find_all(["h2", "h3", "p", "li"]):
        content.append({
            "tag": tag.name,
            "text": clean_text(tag.get_text(" ", strip=True))
        })

    return {
        "url": url,
        "title": title,
        "content": content
    }


# ── SILVER ─────────────────────────────────────────────────────────────

def build_chunks(pages):

    chunks = []
    global_id = 0

    for page_idx, page in enumerate(pages):

        doc_name = f"databricks_{page_idx}.html"

        sec = ""
        sub = ""
        hierarchy = []

        page_chunks = []

        for item in page["content"]:

            if item["tag"] == "h2":
                sec = item["text"]
                sub = ""
                hierarchy = [sec]

            elif item["tag"] == "h3":
                sub = item["text"]
                hierarchy = [sec, sub]

            else:
                text = item["text"]

                if len(text) < 30:
                    continue

                for chunk in split_chunks(text):

                    page_chunks.append({
                        "text": chunk,
                        "sec": sec,
                        "sub": sub,
                        "hierarchy": hierarchy.copy()
                    })

        # montar estrutura final com contexto
        total = len(page_chunks)

        for i, ch in enumerate(page_chunks):

            chunk_id = f"DOC_{page_idx}_p1_c{str(i).zfill(4)}"

            prev_text = page_chunks[i-1]["text"][:100] if i > 0 else ""
            next_text = page_chunks[i+1]["text"][:100] if i < total-1 else ""

            chunks.append({
                "chunk_id": chunk_id,
                "pdf": doc_name,
                "pagina_inicio": 1,
                "pagina_fim": 1,
                "posicao_relativa": round(i / total, 3) if total else 0,

                "titulo_documento": page["title"],
                "secao": ch["sec"],
                "subsecao": ch["sub"],
                "hierarquia": ch["hierarchy"],

                "qualidade_extracao": "boa",
                "metodo_extracao": "html_semantico",
                "tem_tabelas": False,

                "texto": ch["text"],
                "num_caracteres": len(ch["text"]),

                "chunk_anterior_preview": prev_text,
                "chunk_proximo_preview": next_text
            })

            global_id += 1

    return chunks


# ── RUN ────────────────────────────────────────────────────────────────

def run():

    visited = set()
    queue = [START_URL]
    pages = []

    while queue and len(visited) < MAX_PAGES:

        url = queue.pop(0)
        if url in visited:
            continue

        print(f"{len(visited)+1} → {url}")

        soup = get_soup(url)
        visited.add(url)

        if not soup:
            continue

        raw = parse_raw(soup, url)
        pages.append(raw)

        new_links = [l for l in extract_links(soup)
                     if l not in visited and l not in queue]

        queue.extend(new_links)

        time.sleep(DELAY)

    return pages


# ── SAVE ───────────────────────────────────────────────────────────────

def save(pages):

    # RAW
    raw_file = RAW_PATH / "databricks_raw.json"
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)

    print(f"RAW salvo em: {raw_file}")

    # SILVER
    chunks = build_chunks(pages)

    silver_file = SILVER_PATH / "databricks_chunks.json"
    with open(silver_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"SILVER salvo em: {silver_file}")
    print(f"Total de chunks: {len(chunks)}")


# ── MAIN ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pages = run()
    save(pages)