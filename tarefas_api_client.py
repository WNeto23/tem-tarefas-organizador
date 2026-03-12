"""
tarefas_api_client.py
=====================
Cliente HTTP para o sistema Tem Tarefas?.
Substitui as chamadas diretas ao banco (UsuarioModel / TarefaModel)
por chamadas à API FastAPI no Railway.

Variáveis no .env:
  API_URL_TAREFAS   → URL base da API
  API_TOKEN_TAREFAS → Token de autenticação

Interface mantida idêntica aos models originais para que
main.py e dashboard.py precisem do mínimo de alterações.
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

_URL   = os.getenv("API_URL_TAREFAS", "https://web-apitarefas.up.railway.app")
_TOKEN = os.getenv("API_TOKEN_TAREFAS", "")
_HEADERS = {
    "x-token": _TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json"
}
_TIMEOUT = 30


def _request(method, endpoint, **kwargs):
    """Faz requisição com tratamento de erro melhorado"""
    url = f"{_URL}{endpoint}"
    print(f"🔵 {method} {url}")
    print(f"🔵 Headers: { {k:v for k,v in _HEADERS.items() if k != 'x-token'} }")
    
    try:
        if 'json' in kwargs:
            print(f"🔵 Dados: {kwargs['json']}")
        
        response = requests.request(
            method=method,
            url=url,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            **kwargs
        )
        print(f"🟢 Resposta: {response.status_code}")
        
        if response.status_code == 405:
            print(f"🔴 Método não permitido. Allow: {response.headers.get('Allow', 'N/A')}")
            
        response.raise_for_status()
        return response.json() if response.content else {}
        
    except requests.Timeout:
        print(f"🔴 Timeout após {_TIMEOUT}s: {url}")
        raise Exception(f"Servidor não respondeu (timeout de {_TIMEOUT}s)")
    except requests.ConnectionError as e:
        print(f"🔴 Erro de conexão: {e}")
        raise Exception(f"Não foi possível conectar ao servidor.")
    except requests.HTTPError as e:
        print(f"🔴 HTTP {e.response.status_code}: {e.response.text}")
        if e.response.status_code == 401:
            raise Exception("Token de autenticação inválido")
        elif e.response.status_code == 404:
            raise Exception(f"Endpoint não encontrado: {endpoint}")
        else:
            raise
    except json.JSONDecodeError as e:
        print(f"🔴 Erro ao decodificar JSON: {e}")
        raise Exception("Resposta inválida do servidor")
    except Exception as e:
        print(f"🔴 Erro inesperado: {e}")
        raise


def _get(endpoint, params=None):
    return _request("GET", endpoint, params=params)

def _post(endpoint, data):
    return _request("POST", endpoint, json=data)

def _put(endpoint, data):
    return _request("PUT", endpoint, json=data)

def _patch(endpoint, data=None):
    return _request("PATCH", endpoint, json=data or {})

def _delete(endpoint):
    return _request("DELETE", endpoint)


# ══════════════════════════════════════════════════════════════════════
# PROXY: UsuarioModel  — adaptado à API real com novo endpoint de registro
# ══════════════════════════════════════════════════════════════════════

class UsuarioModel:
    """Proxy da API para substituir o UsuarioModel original."""

    def criar_tabela(self):
        pass

    def cadastrar(self, nome_completo, nome_usuario, email, senha, foto=None) -> int:
        """
        Cadastra um novo usuário usando o endpoint /auth/registrar
        que aceita todos os campos, incluindo senha.
        """
        try:
            print(f"🔵 Cadastrando usuário: {nome_usuario}")
            
            # Usa o novo endpoint de registro sem token
            r = _post("/tarefas-app/auth/registrar", {
                "nome_completo": nome_completo,
                "nome_usuario": nome_usuario,
                "email": email,
                "senha": senha,
                "foto": foto or "",
            })
            
            return r["id"]
            
        except Exception as e:
            print(f"🔴 Erro no cadastro: {e}")
            raise

    def verificar_login(self, usuario: str, senha: str) -> dict | None:
        """
        Verifica login do usuário via JWT.
        """
        try:
            print(f"🔵 Verificando login para: {usuario}")
            
            resultado = _post("/tarefas-app/auth/login", {
                "usuario": usuario,
                "senha": senha,
            })
            
            print(f"🟢 Login bem-sucedido!")
            
            # Converte a resposta da API para o formato esperado pelo dashboard
            return {
                'id': resultado["user_id"],
                'nome_completo': resultado["nome_completo"],
                'nome_usuario': resultado["nome_usuario"],
                'email': resultado["email"],
                'trocar_senha': resultado.get("trocar_senha", False),
                'foto': resultado.get("foto"),
                'telegram_chat_id': resultado.get("telegram_chat_id"),
            }
            
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                print(f"🟡 Credenciais inválidas")
                return None
            print(f"🔴 Erro HTTP: {e}")
            raise
        except Exception as e:
            print(f"🔴 Erro inesperado: {e}")
            raise

    def verificar_usuario_existe(self, nome_usuario: str) -> bool:
        """
        Verifica se nome de usuário já existe usando a listagem.
        """
        try:
            usuarios = _get("/tarefas-app/usuarios")
            for u in usuarios:
                # Compara com o campo 'nome' da API (já que não temos nome_usuario)
                if u.get("nome") == nome_usuario:
                    return True
            return False
        except:
            return False

    def verificar_email_existe(self, email: str) -> bool:
        """
        Verifica se email já existe.
        """
        try:
            usuarios = _get("/tarefas-app/usuarios")
            for u in usuarios:
                if u.get("email") == email:
                    return True
            return False
        except:
            return False

    def definir_senha_temporaria(self, email: str, senha_temp: str) -> bool:
        """
        Define uma senha temporária para o usuário.
        NOTA: Funcionalidade não implementada na API
        """
        print(f"⚠️ API não suporta senha temporária")
        return False

    def atualizar_senha_definitiva(self, user_id: int, nova_senha: str) -> bool:
        """
        Atualiza para senha definitiva.
        NOTA: Funcionalidade não implementada na API
        """
        print(f"⚠️ API não suporta alteração de senha")
        return False

    def buscar_dados_por_email(self, email: str) -> tuple | None:
        """
        Retorna (telegram_chat_id, nome_completo) pelo e-mail.
        """
        try:
            print(f"🔵 Buscando dados por email: {email}")
            usuarios = _get("/tarefas-app/usuarios")
            for u in usuarios:
                if u.get("email") == email:
                    # A API não retorna telegram_chat_id na listagem
                    return (None, u.get("nome"))
            return None
        except Exception:
            return None

    def buscar_dados_por_email_ou_id(self, user_id: int) -> dict | None:
        """
        Busca usuário por ID
        """
        try:
            print(f"🔵 Buscando usuário por ID: {user_id}")
            return _get(f"/tarefas-app/usuarios/{user_id}")
        except Exception:
            return None

    def vincular_telegram(self, user_id: int, telegram_id) -> bool:
        """
        Vincula Telegram ao usuário via API.
        """
        try:
            print(f"🔵 Vinculando Telegram ao usuário {user_id} com chat_id {telegram_id}")
            
            # Faz a chamada POST para o endpoint de Telegram
            resultado = _post("/tarefas-app/usuarios/telegram", {
                "user_id": user_id,
                "telegram_id": str(telegram_id)
            })
            
            print(f"🟢 Telegram vinculado com sucesso!")
            return True
            
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print(f"🔴 Usuário não encontrado")
            else:
                print(f"🔴 Erro HTTP: {e}")
            return False
        except Exception as e:
            print(f"🔴 Erro inesperado: {e}")
            return False

    def buscar_telegram_id(self, user_id: int) -> str | None:
        """
        Busca Telegram ID do usuário via API.
        """
        try:
            print(f"🔵 Buscando Telegram ID do usuário {user_id}")
            resultado = _get(f"/tarefas-app/usuarios/{user_id}/telegram")
            return resultado.get("telegram_chat_id")
        except Exception as e:
            print(f"🔴 Erro ao buscar Telegram ID: {e}")
            return None

    def listar_usuarios_com_telegram(self) -> list:
        """
        Lista todos os usuários com Telegram via API.
        """
        try:
            print(f"🔵 Listando usuários com Telegram")
            return _get("/tarefas-app/usuarios/telegram/todos")
        except Exception as e:
            print(f"🔴 Erro ao listar usuários com Telegram: {e}")
            return []

    def atualizar_perfil(self, user_id: int, nome_completo: str, email: str, foto=None) -> bool:
        """
        Atualiza perfil do usuário.
        Usa o endpoint PUT /usuarios/{id} da API
        """
        try:
            print(f"🔵 Atualizando perfil do usuário {user_id}")
            _put(f"/tarefas-app/usuarios/{user_id}", {
                "nome": nome_completo,
                "email": email,
                "ativo": True
            })
            return True
        except Exception:
            return False


# ══════════════════════════════════════════════════════════════════════
# PROXY: TarefaModel
# ══════════════════════════════════════════════════════════════════════

class TarefaModel:
    """Proxy da API para substituir o TarefaModel original."""

    def criar_tabela(self):
        pass

    def criar(self, usuario_id: int, titulo: str, descricao: str = None, status: str = "depois") -> int:
        """
        Cria uma nova tarefa.
        """
        print(f"🔵 Criando tarefa para usuário {usuario_id}: {titulo}")
        r = _post("/tarefas-app/tarefas", {
            "titulo": titulo,
            "descricao": descricao,
            "responsavel": None,
            "usuario_id": usuario_id,
            "prazo": None,
            "status": status,
        })
        return r["id"]

    def listar_por_usuario(self, usuario_id: int) -> list:
        """
        Lista todas as tarefas do usuário.
        Filtra localmente pois a API não tem filtro por usuário.
        """
        print(f"🔵 Listando tarefas do usuário {usuario_id}")
        dados = _get("/tarefas-app/tarefas")
        tarefas_usuario = [d for d in dados if d.get("usuario_id") == usuario_id]
        return [self._dict_para_tupla(d) for d in tarefas_usuario]

    def listar_nao_arquivadas(self, usuario_id: int) -> list:
        """Lista tarefas não arquivadas (mesmo que listar_por_usuario)"""
        return self.listar_por_usuario(usuario_id)

    def listar_arquivadas(self, usuario_id: int) -> list:
        """Lista tarefas arquivadas (não suportado pela API)"""
        return []

    def buscar_por_id(self, tarefa_id: int) -> dict | None:
        """Busca tarefa por ID"""
        try:
            print(f"🔵 Buscando tarefa {tarefa_id}")
            d = _get(f"/tarefas-app/tarefas/{tarefa_id}")
            from datetime import datetime, date
            
            # Converte strings de data
            if d.get("prazo") and isinstance(d["prazo"], str):
                d["data_vencimento"] = date.fromisoformat(d["prazo"])
            if d.get("criado_em") and isinstance(d["criado_em"], str):
                d["data_criacao"] = datetime.fromisoformat(d["criado_em"])
            
            return d
        except Exception:
            return None

    def atualizar_status(self, tarefa_id: int, novo_status: str) -> bool:
        """Atualiza o status da tarefa"""
        try:
            print(f"🔵 Atualizando status da tarefa {tarefa_id} para {novo_status}")
            _patch(f"/tarefas-app/tarefas/{tarefa_id}/status", {"status": novo_status})
            return True
        except Exception:
            return False

    def atualizar_fase(self, tarefa_id: int, nova_fase: str) -> bool:
        """Alias para atualizar_status"""
        return self.atualizar_status(tarefa_id, nova_fase)

    def excluir(self, tarefa_id: int) -> bool:
        """Exclui tarefa"""
        try:
            print(f"🔵 Excluindo tarefa {tarefa_id}")
            _delete(f"/tarefas-app/tarefas/{tarefa_id}")
            return True
        except Exception:
            return False

    def arquivar_manual(self, tarefa_id: int) -> bool:
        """Arquiva tarefa manualmente (não suportado)"""
        return False

    def restaurar_do_arquivo(self, tarefa_id: int) -> bool:
        """Restaura tarefa do arquivo (não suportado)"""
        return False

    def excluir_permanentemente(self, tarefa_id: int) -> bool:
        """Exclui tarefa permanentemente (não suportado)"""
        return False

    def arquivar_tarefas_antigas(self, usuario_id=None) -> int:
        """Arquiva tarefas antigas (não suportado)"""
        return 0

    # --- Helpers internos ---

    def _dict_para_tupla(self, d: dict) -> tuple:
        """
        Converte dict da API para tupla no formato esperado pelo dashboard.
        """
        from datetime import datetime, date
        
        def parse_date(v):
            if not v:
                return None
            if isinstance(v, (date, datetime)):
                return v
            try:
                return date.fromisoformat(str(v)[:10])
            except:
                return None
                
        def parse_dt(v):
            if not v:
                return None
            if isinstance(v, datetime):
                return v
            try:
                return datetime.fromisoformat(str(v))
            except:
                return None
        
        return (
            d.get("id"),
            d.get("titulo"),
            d.get("descricao"),
            d.get("status"),
            parse_dt(d.get("criado_em")),
            d.get("status"),  # fase = status
            parse_date(d.get("prazo")),
            d.get("responsavel"),
        )

    def _dict_para_tupla_arquivada(self, d: dict) -> tuple:
        """Para tarefas arquivadas (não usado)"""
        return self._dict_para_tupla(d) + (None,)