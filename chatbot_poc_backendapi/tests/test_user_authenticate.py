import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
import models
import crud
import auth
from sqlalchemy.orm import Session
from database import SessionLocal

def main():
    db: Session = SessionLocal()

    email_teste = "email@example.com"
    senha_teste = "senha_segura"  # a senha que você criou

    usuario = crud.authenticate_user(db, email_teste, senha_teste)

    if usuario:
        print(f"Autenticação bem-sucedida! Usuário: id={usuario.id}, nome={usuario.nome}, email={usuario.email}")
    else:
        print("Falha na autenticação: e-mail ou senha incorretos.")

    db.close()

if __name__ == "__main__":
    main()