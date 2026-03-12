"""
routes/auth_routes.py
=====================
Endpoints de autenticação JWT para o sistema de tarefas.
Mantém compatibilidade com o UsuarioModel existente.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import os
from jose import JWTError, jwt
from dotenv import load_dotenv

from models.usuario import UsuarioModel

load_dotenv()

router = APIRouter(
    prefix="/tarefas-app/auth",
    tags=["Tarefas - Autenticação"]
)

# Configurações JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sua-chave-secreta-aqui-mude-em-producao")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))  # 24 horas


# ── Schemas ───────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    usuario: str  # Pode ser nome_usuario ou email
    senha: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    nome_completo: str
    nome_usuario: str
    email: EmailStr
    foto: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    trocar_senha: bool = False

class TokenData(BaseModel):
    user_id: Optional[int] = None
    nome_usuario: Optional[str] = None


# ── Funções JWT ───────────────────────────────────────────────────────

def criar_token_jwt(user_id: int, nome_usuario: str) -> str:
    """Cria um token JWT para o usuário"""
    expiracao = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    
    payload = {
        "sub": str(user_id),
        "usuario": nome_usuario,
        "exp": expiracao,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verificar_token_jwt(token: str) -> Optional[TokenData]:
    """Verifica e decodifica um token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        nome_usuario = payload.get("usuario")
        
        if user_id is None or nome_usuario is None:
            return None
            
        return TokenData(user_id=user_id, nome_usuario=nome_usuario)
    except JWTError:
        return None


# ── Endpoints ─────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(credenciais: LoginRequest):
    """
    Realiza login do usuário.
    Aceita tanto nome_usuario quanto email no campo 'usuario'.
    Retorna token JWT e dados do usuário.
    """
    usuario_model = UsuarioModel()
    
    # Tenta fazer login com as credenciais fornecidas
    usuario = usuario_model.verificar_login(
        credenciais.usuario, 
        credenciais.senha
    )
    
    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos"
        )
    
    # Cria o token JWT
    access_token = criar_token_jwt(
        user_id=usuario["id"],
        nome_usuario=usuario["nome_usuario"]
    )
    
    # Retorna os dados do usuário junto com o token
    return LoginResponse(
        access_token=access_token,
        user_id=usuario["id"],
        nome_completo=usuario["nome_completo"],
        nome_usuario=usuario["nome_usuario"],
        email=usuario["email"],
        foto=usuario.get("foto"),
        telegram_chat_id=usuario.get("telegram_chat_id"),
        trocar_senha=usuario.get("trocar_senha", False)
    )


@router.post("/registrar")
async def registrar(
    nome_completo: str,
    nome_usuario: str,
    email: EmailStr,
    senha: str,
    foto: Optional[str] = None
):
    """
    Registra um novo usuário.
    Mantém compatibilidade com o método cadastrar existente.
    """
    usuario_model = UsuarioModel()
    
    # Verifica se usuário já existe
    if usuario_model.verificar_usuario_existe(nome_usuario):
        raise HTTPException(
            status_code=409,
            detail="Nome de usuário já está em uso"
        )
    
    if usuario_model.verificar_email_existe(email):
        raise HTTPException(
            status_code=409,
            detail="E-mail já está cadastrado"
        )
    
    # Cadastra o novo usuário
    user_id = usuario_model.cadastrar(
        nome_completo=nome_completo,
        nome_usuario=nome_usuario,
        email=email,
        senha=senha,
        foto=foto
    )
    
    return {
        "id": user_id,
        "mensagem": "Usuário registrado com sucesso",
        "nome_usuario": nome_usuario,
        "email": email
    }


@router.post("/refresh")
async def refresh_token(token: str):
    """
    Renova um token JWT expirado/válido.
    """
    token_data = verificar_token_jwt(token)
    
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado"
        )
    
    usuario_model = UsuarioModel()
    usuario = usuario_model.buscar_dados_por_email_ou_id(token_data.user_id)
    
    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )
    
    # Gera novo token
    novo_token = criar_token_jwt(
        user_id=usuario["id"],
        nome_usuario=usuario["nome_usuario"]
    )
    
    return {
        "access_token": novo_token,
        "token_type": "bearer"
    }


@router.get("/me")
async def usuario_atual(token: str):
    """
    Retorna os dados do usuário baseado no token fornecido.
    """
    token_data = verificar_token_jwt(token)
    
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado"
        )
    
    usuario_model = UsuarioModel()
    usuario = usuario_model.buscar_dados_por_email_ou_id(token_data.user_id)
    
    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )
    
    return usuario