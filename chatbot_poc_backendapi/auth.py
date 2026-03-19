from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from fastapi import Depends, HTTPException, status, Cookie
import database
from sqlalchemy.orm import Session
import crud
from jose import JWTError
import os

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """Gera o hash de uma senha em texto puro.

    Args:
        password: Senha em texto puro a ser hasheada.

    Returns:
        str: Hash da senha gerado pelo algoritmo argon2.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se uma senha em texto puro corresponde ao hash armazenado.

    Args:
        plain_password: Senha em texto puro fornecida pelo usuário.
        hashed_password: Hash armazenado para comparação.

    Returns:
        bool: True se a senha corresponde ao hash, False caso contrário.
    """
    return pwd_context.verify(plain_password, hashed_password)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # token válido por 60 minutos

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Cria um JWT de acesso com tempo de expiração.

    Args:
        data: Payload a ser codificado no token (ex: ``{"sub": email}``).
        expires_delta: Duração customizada de validade do token. Se não
            fornecida, usa ``ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns:
        str: Token JWT codificado e assinado.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> dict | None:
    """Decodifica e valida um JWT de acesso.

    Args:
        token: Token JWT a ser verificado.

    Returns:
        dict | None: Payload decodificado se o token for válido,
            ou None se estiver expirado ou malformado.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None
    
def get_db() -> Session:
    """Fornece uma sessão de banco de dados para injeção de dependência.

    Abre uma sessão, a disponibiliza via ``yield`` e garante o fechamento
    ao final da requisição, mesmo em caso de exceção.

    Yields:
        Session: Sessão ativa do SQLAlchemy.
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), access_token: str = Cookie(None)):
    """Obtém o usuário autenticado a partir do cookie de acesso.

    Decodifica o JWT presente no cookie ``access_token``, extrai o e-mail
    do payload e busca o usuário correspondente no banco de dados.

    Args:
        db: Sessão do banco de dados injetada via ``Depends``.
        access_token: Token JWT lido automaticamente do cookie da requisição.

    Raises:
        HTTPException: 401 se o token estiver ausente, inválido ou se o
            usuário não for encontrado.

    Returns:
        Usuario: Instância do modelo de usuário autenticado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
    )
    if not access_token:
        raise credentials_exception
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user