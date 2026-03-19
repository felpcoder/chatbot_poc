import sys
import os
from fastapi import FastAPI, Depends, HTTPException

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from database import SessionLocal
from models import ChatHistorico

def test_insert():
    try:
        db: Session = SessionLocal()

        # 1. Busca o usuário que você acabou de criar (ou um existente)
        email_teste = "email@example.com"
        user = crud.get_user_by_email(db, email=email_teste)

        if user:
            # 2. Testa a inserção no histórico (conforme seu layout integer)
            nova_mensagem = models.ChatHistorico(
                id_usuario=user.id,        # integer
                id_conversa=1,             # integer 
                papel="user",              # varchar(10)
                conteudo="Teste de Risco de Crédito"
            )
            
            db.add(nova_mensagem)
            db.commit()
            print(f"✅ Histórico gravado para o usuário {user.id}!")
        
        db.close()
        print("✅ Registro inserido com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_insert()