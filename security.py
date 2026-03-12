"""
security.py
===========
Autenticação por token separada por sistema.
O cliente envia o token no header:  x-token

Tokens configurados no Railway (variáveis de ambiente):
  API_TOKEN          → Calendário / Notificações
  API_TOKEN_TAREFAS  → Tarefas
"""
import os
from fastapi import Header, HTTPException, status
from dotenv import load_dotenv

load_dotenv()


def _verificar(token_recebido: str | None, env_var: str, sistema: str):
    esperado = os.getenv(env_var)
    if not esperado:
        raise RuntimeError(f"'{env_var}' não configurado no .env / Railway")
    if not token_recebido or token_recebido != esperado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido para o sistema '{sistema}'",
        )


def token_calendario(x_token: str | None = Header(default=None)):
    """Protege /prestadores  /datas  /log — usa API_TOKEN."""
    _verificar(x_token, "API_TOKEN", "Calendário")


def token_tarefas(x_token: str | None = Header(default=None)):
    """Protege /tarefas-app/... — usa API_TOKEN_TAREFAS."""
    _verificar(x_token, "API_TOKEN_TAREFAS", "Tarefas")


# ── Template para novos sistemas ──────────────────────────────────────
# 1. Adicionar no Railway:   API_TOKEN_NOVOSISTEMA=...
# 2. Criar a dependência:
#
# def token_novosistema(x_token: str | None = Header(default=None)):
#     _verificar(x_token, "API_TOKEN_NOVOSISTEMA", "NoveSistema")