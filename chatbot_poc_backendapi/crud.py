from sqlalchemy.orm import Session
import models
import auth


def get_user_by_email(db: Session, email: str) -> models.Usuario | None:
    """Busca um usuário pelo e-mail.

    Args:
        db: Sessão ativa do SQLAlchemy.
        email: E-mail do usuário a ser buscado.

    Returns:
        models.Usuario | None: Instância do usuário encontrado,
            ou None se não existir.
    """
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()


def create_user(db: Session, nome: str, email: str, password: str) -> models.Usuario:
    """Cria e persiste um novo usuário com senha hasheada.

    Args:
        db: Sessão ativa do SQLAlchemy.
        nome: Nome completo do usuário.
        email: E-mail do usuário.
        password: Senha em texto puro, que será hasheada antes de persistir.

    Returns:
        models.Usuario: Instância do usuário recém-criado e atualizada do banco.
    """
    hashed_password = auth.hash_password(password)
    user = models.Usuario(nome=nome, email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> models.Usuario | bool:
    """Valida as credenciais de um usuário.

    Busca o usuário pelo e-mail e verifica se a senha fornecida
    corresponde ao hash armazenado.

    Args:
        db: Sessão ativa do SQLAlchemy.
        email: E-mail do usuário.
        password: Senha em texto puro a ser verificada.

    Returns:
        models.Usuario | bool: Instância do usuário autenticado em caso de
            sucesso, ou False se o usuário não existir ou a senha for inválida.
    """
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not auth.verify_password(password, user.hashed_password):
        return False
    return user


def create_chat_message(
    db: Session,
    id_usuario: int,
    id_conversa: int,
    papel: str,
    conteudo: str
) -> models.ChatHistorico:
    """Cria e persiste uma mensagem no histórico de chat.

    Args:
        db: Sessão ativa do SQLAlchemy.
        id_usuario: Identificador do usuário autor da mensagem.
        id_conversa: Identificador da conversa à qual a mensagem pertence.
        papel: Papel do autor da mensagem (``"user"`` ou ``"assistant"``).
        conteudo: Conteúdo textual da mensagem.

    Returns:
        models.ChatHistorico: Instância da mensagem recém-criada e atualizada do banco.
    """
    db_message = models.ChatHistorico(
        id_usuario=id_usuario,
        id_conversa=id_conversa,
        papel=papel,
        conteudo=conteudo
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_recent_chat_history(
    db: Session,
    id_usuario: int,
    id_conversa: int,
    limit: int = 10
) -> list[models.ChatHistorico]:
    """Busca as últimas mensagens de uma conversa específica de um usuário.

    Aplica filtro duplo por usuário e conversa para garantir isolamento
    de dados entre sessões. O resultado é retornado em ordem cronológica
    crescente (pergunta → resposta).

    Args:
        db: Sessão ativa do SQLAlchemy.
        id_usuario: Identificador do usuário — filtro de segurança.
        id_conversa: Identificador da conversa a ser recuperada.
        limit: Número máximo de mensagens a retornar. Padrão: 10.

    Returns:
        list[models.ChatHistorico]: Lista das mensagens mais recentes
            ordenadas cronologicamente de forma crescente.
    """
    return db.query(models.ChatHistorico)\
        .filter(
            models.ChatHistorico.id_usuario == id_usuario,  # Filtro de segurança por Usuário
            models.ChatHistorico.id_conversa == id_conversa  # Filtro por Sessão
        )\
        .order_by(models.ChatHistorico.criado_em.desc())\
        .limit(limit)\
        .all()[::-1]  # Inverte para manter a ordem: Pergunta -> Resposta