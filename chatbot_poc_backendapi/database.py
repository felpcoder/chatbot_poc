import os
import time
import psycopg2
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()


# ---------------------------------------------------------------------------
# Funções puras / utilitárias
# ---------------------------------------------------------------------------

def _wait_for_db(database_url: str, interval: float = 2.0) -> None:
    """Aguarda o banco de dados ficar disponível antes de prosseguir.

    Tenta estabelecer uma conexão direta via psycopg2 em loop, com pausa
    entre tentativas, até que o banco esteja acessível. Útil em ambientes
    Docker/Compose onde o banco pode subir após a aplicação.

    Args:
        database_url: DSN de conexão no formato
            ``postgresql://user:pass@host:port/db``.
        interval: Tempo em segundos entre cada tentativa. Padrão: 2.0.

    Returns:
        None
    """
    while True:
        try:
            conn = psycopg2.connect(database_url)
            conn.close()
            return
        except psycopg2.OperationalError:
            print("Banco ainda não pronto, aguardando 2s...")
            time.sleep(interval)


def _build_engine(database_url: str) -> Engine:
    """Cria e retorna o engine do SQLAlchemy.

    Instancia um :class:`sqlalchemy.engine.Engine` configurado com a
    API futura (SQLAlchemy 2.x) a partir do DSN fornecido.

    Args:
        database_url: DSN de conexão no formato
            ``postgresql://user:pass@host:port/db``.

    Returns:
        Engine: Instância do engine pronta para uso.
    """
    return create_engine(database_url, future=True)


def _build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Cria e retorna a fábrica de sessões vinculada ao engine fornecido.

    Configura o :class:`~sqlalchemy.orm.sessionmaker` sem autocommit e
    sem autoflush, padrão recomendado para uso com FastAPI + Depends.

    Args:
        engine: Engine do SQLAlchemy ao qual as sessões serão vinculadas.

    Returns:
        sessionmaker[Session]: Fábrica de sessões configurada.
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def test_connection(engine: Engine) -> None:
    """Testa a conectividade com o banco de dados executando ``SELECT 1``.

    Abre uma conexão explícita, executa uma query trivial e imprime o
    resultado. Em caso de falha, captura e exibe a exceção sem propagar.

    Args:
        engine: Engine do SQLAlchemy a ser testado.

    Returns:
        None
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Conexão OK:", result.scalar())
            conn.commit()
    except Exception as e:
        print("Erro na conexão:", e)


# ---------------------------------------------------------------------------
# Inicialização (executada na importação do módulo)
# ---------------------------------------------------------------------------

_wait_for_db(DATABASE_URL)

engine = _build_engine(DATABASE_URL)
SessionLocal = _build_session_factory(engine)


# ---------------------------------------------------------------------------
# Ponto de entrada para teste manual
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_connection(engine)