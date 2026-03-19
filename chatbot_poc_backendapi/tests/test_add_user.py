from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import models
import crud
import auth
from database import SessionLocal

def main():
    # Cria sessão
    db: Session = SessionLocal()

    # Dados do usuário que queremos adicionar
    nome = "Usuário de Teste"
    email = "user@example.com"
    senha = "senha_segura"

    # Tenta criar o usuário
    user = crud.create_user(db, nome=nome, email=email, password=senha)
    print(f"Usuário criado: id={user.id}, nome={user.nome}, email={user.email}")

    db.close()

if __name__ == "__main__":
    main()