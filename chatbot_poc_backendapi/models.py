from sqlalchemy import Column, Integer, String, TIMESTAMP, Text
from database import Base
from sqlalchemy.sql import func


class Usuario(Base):
    """Modelo ORM representando a tabela de usuários da aplicação.

    Attributes:
        id: Chave primária auto-incrementada.
        nome: Nome completo do usuário.
        email: E-mail único do usuário, usado como identificador de login.
        hashed_password: Hash da senha armazenado na coluna ``senha_hash``.
        criado_em: Timestamp de criação do registro, preenchido automaticamente pelo banco.
    """

    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column("senha_hash", String, nullable=False)
    criado_em = Column(TIMESTAMP(timezone=True), server_default=func.now())


class ChatHistorico(Base):
    """Modelo ORM representando o histórico de mensagens do chat.

    Cada registro corresponde a uma única mensagem, podendo ser do
    usuário (``"user"``) ou do assistente (``"assistant"``).

    Attributes:
        id: Chave primária auto-incrementada.
        id_conversa: Identificador da conversa à qual a mensagem pertence.
        id_usuario: Identificador do usuário autor da mensagem.
        papel: Papel do autor — ``"user"`` ou ``"assistant"``.
        conteudo: Conteúdo textual da mensagem.
        criado_em: Timestamp de criação do registro, preenchido automaticamente pelo banco.
    """

    __tablename__ = "chat_historico"

    id = Column(Integer, primary_key=True, index=True)
    id_conversa = Column(Integer, index=True)
    id_usuario = Column(Integer, index=True)
    papel = Column(String)  # 'user' ou 'assistant'
    conteudo = Column(Text)
    criado_em = Column(TIMESTAMP(timezone=True), server_default=func.now())