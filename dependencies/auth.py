# dependencies/auth.py
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from routes.auth_routes import verificar_token_jwt
from models.usuario import UsuarioModel

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Dependência para obter o usuário atual a partir do token JWT.
    Use em rotas que precisam de autenticação.
    """
    token = credentials.credentials
    
    # Verifica o token
    token_data = verificar_token_jwt(token)
    
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado"
        )
    
    # Busca o usuário no banco
    usuario_model = UsuarioModel()
    usuario = usuario_model.buscar_dados_por_email_ou_id(token_data.user_id)
    
    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Usuário não encontrado"
        )
    
    return usuario