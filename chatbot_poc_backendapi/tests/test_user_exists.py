from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import models
import crud
import auth
from database import SessionLocal

def main():
    db: Session = SessionLocal()

    email_teste = "email@example.com"  # e-mail que você quer checar

    usuario = crud.get_user_by_email(db, email_teste)

    if usuario:
        print(f"Usuário encontrado: id={usuario.id}, nome={usuario.nome}, email={usuario.email}")
    else:
        print("Usuário não encontrado.")

    db.close()

if __name__ == "__main__":
    main()