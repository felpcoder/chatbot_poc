import json
import faiss
import numpy as np
from openai import OpenAI
import os

# Inicializa cliente OpenAI
api_key = os.getenv("API_KEY")
client = OpenAI(api_key=api_key)


def buscar_chunks(pergunta: str, embeddings_data: list[dict], index: faiss.IndexFlatL2, top_k: int = 10) -> list[dict]:
    """Realiza busca semântica por similaridade no índice FAISS.

    Gera o embedding da pergunta via OpenAI e recupera os ``top_k``
    chunks mais próximos no espaço vetorial L2.

    Args:
        pergunta: Texto da pergunta do usuário.
        embeddings_data: Lista de metadados indexados, alinhada com o índice FAISS.
        index: Índice FAISS previamente construído.
        top_k: Número de chunks a retornar. Padrão: 10.

    Returns:
        list[dict]: Lista dos ``top_k`` chunks mais relevantes, cada um
            contendo ao menos os campos ``pdf``, ``pagina``, ``subchunk_index`` e ``texto``.
    """
    pergunta_emb = client.embeddings.create(
        model="text-embedding-3-large",
        input=pergunta
    ).data[0].embedding
    
    pergunta_emb = np.array([pergunta_emb], dtype="float32")
    
    D, I = index.search(pergunta_emb, top_k)
    return [embeddings_data[i] for i in I[0]]


def gerar_resposta(mensagem_usuario: str, id_conversa: str, id_usuario: str, top_k: int = 15) -> str:
    """Gera uma resposta técnica fundamentada em RAG para a mensagem do usuário.

    Carrega o índice FAISS e os metadados do disco, busca os chunks mais
    relevantes por similaridade semântica, monta o contexto documental e
    chama o modelo GPT-4 Turbo com um system prompt especializado em
    Risco de Crédito e Regulação Bancária.

    Args:
        mensagem_usuario: Mensagem enviada pelo usuário.
        id_conversa: Identificador da conversa atual, usado no system prompt
            para manter coerência histórica.
        id_usuario: Identificador do usuário autenticado.
        top_k: Número de chunks recuperados do índice para compor o contexto.
            Padrão: 15.

    Returns:
        str: Resposta gerada pelo LLM, ou mensagem de erro em caso de falha.
    """
    try:
        index = faiss.read_index("base_conhecimento/gold/vector_store/faiss.index")

        with open("base_conhecimento/gold/vector_store/metadata.json", "r", encoding="utf-8") as f:
            embeddings_data = json.load(f)

        chunks_relevantes = buscar_chunks(
            mensagem_usuario,
            embeddings_data=embeddings_data,
            index=index,
            top_k=top_k
        )

        contexto = ""
        for c in chunks_relevantes:
            pagina_info = ""

            if c.get("pagina_inicio") and c.get("pagina_fim"):
                if c["pagina_inicio"] == c["pagina_fim"]:
                    pagina_info = f"Página: {c['pagina_inicio']}"
                else:
                    pagina_info = f"Páginas: {c['pagina_inicio']}-{c['pagina_fim']}"
            elif c.get("pagina_inicio"):
                pagina_info = f"Página: {c['pagina_inicio']}"
            else:
                pagina_info = "Página: N/A"

            contexto += (
                f"[PDF: {c.get('pdf', 'N/A')} | {pagina_info} | Subchunk: {c.get('subchunk_index', 'N/A')}]\n"
            )
            contexto += f"{c.get('texto', '')}\n\n"
        
        system_prompt = (
            f"Você é o **'Especialista em Risco de Crédito e Regulação Bancária'**, assistente técnico de alta senioridade para a squad de dados (Cientistas, Engenheiros e PMs) de um grande banco brasileiro.\n\n"

            f"BASE DOCUMENTAL DISPONÍVEL (seus embeddings contêm estes documentos regulatórios):\n"
            f"- Basileia III\n"
            f"- Circular BACEN 3.749\n"
            f"- Plano Contábil COSIF\n"
            f"- Resoluções BACEN: 4.401, 4.553, 4.557, 4.616, 4.677, 4.950, 4.995, 5.077\n"
            f"- Resolução CMN 4.955\n"
            f"- SCR - Instruções de Preenchimento Doc 3040\n"
            f"- IFRS 9\n"
            f"- LGPD\n\n"
            
            f"ESCOPO:\n"
            f"- Risco de Crédito (PD, LGD, EAD, ECL)\n"
            f"- Capital regulatório e provisão\n"
            f"- Regulação bancária\n"
            f"- Engenharia de Dados (ETL, pipelines, modelagem)\n"
            f"- Ciência de Dados (modelos, features, validação)\n\n"
            
            f"IDENTIDADE E COMPORTAMENTO:\n"
            f"- Seja direto, técnico e objetivo. NUNCA use frases introdutórias como 'Sim, tenho conhecimento sobre...' ou 'Ótima pergunta!'.\n"
            f"- Antes de qualquer resposta técnica, lembre-se que você está falando com pessoas. Seja atencioso, paciente e gentil — especialmente quando precisar redirecionar o assunto.\n"            f"- Para perguntas sobre sua identidade, metodologia ou funcionamento, responda com clareza e profissionalismo.\n"
            f"- Para perguntas de caráter operacional sobre o próprio assistente (ex: sugestões de melhoria, feedback de UX), responda de forma colaborativa e construtiva.\n"
            f"- Reserve o redirecionamento técnico APENAS para perguntas genuinamente vagas ou sem qualquer relação com o contexto do banco/squad.\n\n"

            f"QUANDO REDIRECIONAR:\n"
            f"Se a pergunta não tiver relação com Risco de Crédito, Regulação Bancária, Arquitetura de Dados para Risco ou o funcionamento deste assistente, responda:\n"
            f"'Meu escopo de atuação é Risco de Crédito e Regulação Bancária. Posso ajudar com temas como PD/LGD, ECL, Basileia III, IFRS 9, COSIF ou ETL para modelos de crédito. Como posso ajudá-lo nesse contexto?'\n\n"

            f"DIRETRIZES DE RESPOSTA:\n"
            f"1. **AUTORIDADE TÉCNICA**: Fundamente sempre nos documentos da base documental. Se for legislação, cite o documento de origem e, quando possível, o artigo ou seção. Se não for legislação, evite citações diretas e cópias de trechos longos de livros ou artigos, sintetize com suas palavras mas sem inventar fatos.\n"
            f"2. **IMPACTO DE NEGÓCIO**: Em respostas sobre risco, mencione obrigatoriamente.\n"
            f"3. **FORMATO**: Use Markdown com títulos, bullets e **negrito** para termos-chave. Sem parágrafos introdutórios.\n"
            f"4. **DADOS E ARQUITETURA**: Para perguntas sobre dados, responda com foco em schema de tabelas, granularidade e fluxos ETL para modelos de risco.\n"
            f"5. **LIMITES DOCUMENTAIS**: Nunca invente normativas ou artigos. Se o contexto dos embeddings for insuficiente, responda: 'Base documental insuficiente para este tema. Consulte diretamente: https://www.bcb.gov.br'\n"
            f"6. **METODOLOGIA**: Quando questionado sobre como funciona, explique que opera via arquitetura **RAG (Retrieval-Augmented Generation)**: os documentos foram indexados como embeddings e, a cada pergunta, os trechos mais relevantes são recuperados por similaridade semântica e passados como contexto para o modelo **GPT-4o** (OpenAI). A infraestrutura é containerizada em **Docker** com serviços **PostgreSQL**, **React** e **FastAPI**, rodando em **WSL Ubuntu**.\n\n"

            f"CONTEXTO EXTRAÍDO DOS DOCUMENTOS (fonte primária — priorize sempre):\n"
            f"{contexto}\n\n"

            f"HISTÓRICO DA CONVERSA (ID: {id_conversa} | Usuário: {id_usuario}):\n"
            f"Use o histórico para manter coerência técnica, evitando repetir conceitos já explicados.\n"
        )

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": mensagem_usuario}
            ],
            temperature=0.1,
            max_tokens=4096
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao processar a mensagem: {str(e)}"
