from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import models, schemas, database, crud, auth, chat_bot_openai
from fastapi.middleware.cors import CORSMiddleware
from auth import get_current_user
from collections import defaultdict
import time

# Rate limiting simples sem dependência externa
login_attempts: dict = defaultdict(list)

def check_rate_limit(ip: str, max_attempts: int = 5, window: int = 60) -> None:
    """Verifica e aplica rate limiting por IP para o endpoint de login.

    Mantém um histórico de tentativas por IP dentro de uma janela de tempo.
    Lança exceção HTTP 429 se o limite de tentativas for excedido.

    Args:
        ip: Endereço IP do cliente.
        max_attempts: Número máximo de tentativas permitidas na janela. Padrão: 5.
        window: Duração da janela de tempo em segundos. Padrão: 60.

    Raises:
        HTTPException: 429 se o número de tentativas exceder ``max_attempts``
            dentro do período ``window``.

    Returns:
        None
    """
    now = time.time()
    attempts = [t for t in login_attempts[ip] if now - t < window]
    login_attempts[ip] = attempts
    if len(attempts) >= max_attempts:
        raise HTTPException(status_code=429, detail="Muitas tentativas. Tente novamente em 1 minuto.")
    login_attempts[ip].append(now)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend.devpersonalprojects.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
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

@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.UserOut:
    """Registra um novo usuário na aplicação.

    Verifica se o e-mail já está em uso antes de criar o registro.

    Args:
        user: Dados do novo usuário (nome, e-mail, senha).
        db: Sessão do banco de dados injetada via ``Depends``.

    Raises:
        HTTPException: 400 se o e-mail já estiver cadastrado.

    Returns:
        UserOut: Dados públicos do usuário criado.
    """
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Este e-mail já está registrado")
    return crud.create_user(db, nome=user.nome, email=user.email, password=user.password)

@app.post("/login")
def login(request: Request, user: schemas.UserLogin, db: Session = Depends(get_db)) -> JSONResponse:
    """Autentica um usuário e define o cookie de acesso.

    Aplica rate limiting por IP, valida as credenciais e, em caso de sucesso,
    gera um JWT e o armazena em cookie HttpOnly.

    Args:
        request: Objeto da requisição FastAPI, usado para extrair o IP do cliente.
        user: Credenciais de login (e-mail e senha).
        db: Sessão do banco de dados injetada via ``Depends``.

    Raises:
        HTTPException: 429 se o rate limit for excedido.
        HTTPException: 401 se as credenciais forem inválidas.

    Returns:
        JSONResponse: Dados públicos do usuário com o cookie ``access_token`` definido.
    """
    check_rate_limit(request.client.host)
    db_user = crud.authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access_token = auth.create_access_token(data={"sub": db_user.email})
    response = JSONResponse(content={
        "user": schemas.UserOut.from_orm(db_user).model_dump()
    })
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )
    return response

@app.post("/request_message")
async def request_message(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
) -> dict:
    """Processa uma mensagem do usuário e retorna a resposta do assistente.

    Persiste a mensagem do usuário, gera a resposta via OpenAI e persiste
    a resposta do assistente, tudo vinculado à conversa informada.

    Args:
        request: Dados da requisição contendo a mensagem e o ID da conversa.
        db: Sessão do banco de dados injetada via ``Depends``.
        current_user: Usuário autenticado injetado via ``Depends``.

    Returns:
        dict: Resposta do assistente e ID da conversa,
            no formato ``{"resposta_assistente": str, "id_conversa": str}``.
    """
    crud.create_chat_message(
        db=db,
        id_usuario=current_user.id,
        id_conversa=request.conversation_id,
        papel="user",
        conteudo=request.message
    )

    resposta = chat_bot_openai.gerar_resposta(
        request.message,
        request.conversation_id,
        current_user.id
    )

    crud.create_chat_message(
        db=db,
        id_usuario=current_user.id,
        id_conversa=request.conversation_id,
        papel="assistant",
        conteudo=resposta
    )

    return {
        "resposta_assistente": resposta,
        "id_conversa": request.conversation_id
    }

@app.post("/logout")
def logout(response: Response) -> dict:
    """Encerra a sessão do usuário removendo o cookie de acesso.

    Args:
        response: Objeto de resposta FastAPI usado para deletar o cookie.

    Returns:
        dict: Confirmação no formato ``{"status": "ok"}``.
    """
    response.delete_cookie("access_token")
    return {"status": "ok"}


@app.get("/me")
def me(current_user: models.Usuario = Depends(get_current_user)) -> schemas.UserOut:
    """Retorna os dados públicos do usuário autenticado.

    Args:
        current_user: Usuário autenticado injetado via ``Depends``.

    Returns:
        UserOut: Dados públicos do usuário autenticado.
    """
    return schemas.UserOut.from_orm(current_user)