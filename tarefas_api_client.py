"""
tarefas_api_client.py
=====================
Cliente HTTP para o sistema Tem Tarefas?.
Substitui as chamadas diretas ao banco (UsuarioModel / TarefaModel)
por chamadas à API FastAPI no Railway.
Variáveis no .env:
  API_URL_TAREFAS   → URL base da API
  API_TOKEN_TAREFAS → Token de autenticação
"""
import os
import requests
import json
from datetime import datetime, date
from dotenv import load_dotenv
import sys as _sys, os as _os
if getattr(_sys, "frozen", False):
    _base = _sys._MEIPASS
else:
    _base = _os.path.dirname(_os.path.abspath(__file__))
load_dotenv(_os.path.join(_base, ".env"))

_URL     = os.getenv("API_URL_TAREFAS", "https://web-apitarefas.up.railway.app")
_TOKEN   = os.getenv("API_TOKEN_TAREFAS", "")
_HEADERS = {
    "x-token": _TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json",
}
_TIMEOUT = 30


def _request(method, endpoint, **kwargs):
    url = f"{_URL}{endpoint}"
    print(f"🔵 {method} {url}")
    print(f"🔵 Headers: { {k: v for k, v in _HEADERS.items() if k != 'x-token'} }")
    try:
        if "json" in kwargs:
            print(f"🔵 Dados: {kwargs['json']}")
        response = requests.request(
            method=method, url=url, headers=_HEADERS,
            timeout=_TIMEOUT, **kwargs
        )
        print(f"🟢 Resposta: {response.status_code}")
        if response.status_code == 405:
            print(f"🔴 Método não permitido. Allow: {response.headers.get('Allow', 'N/A')}")
        response.raise_for_status()
        return response.json() if response.content else {}
    except requests.Timeout:
        raise Exception(f"Servidor não respondeu (timeout de {_TIMEOUT}s)")
    except requests.ConnectionError:
        raise Exception("Não foi possível conectar ao servidor.")
    except requests.HTTPError as e:
        print(f"🔴 HTTP {e.response.status_code}: {e.response.text}")
        if e.response.status_code == 401:
            raise Exception("Token de autenticação inválido")
        elif e.response.status_code == 404:
            raise Exception(f"Endpoint não encontrado: {endpoint}")
        else:
            raise
    except json.JSONDecodeError as e:
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
# PROXY: UsuarioModel
# ══════════════════════════════════════════════════════════════════════
class UsuarioModel:
    """Proxy da API para substituir o UsuarioModel original."""

    def criar_tabela(self):
        pass

    def cadastrar(self, nome_completo, nome_usuario, email, senha, foto=None) -> int:
        print(f"🔵 Cadastrando usuário: {nome_usuario}")
        r = _post("/tarefas-app/auth/registrar", {
            "nome_completo": nome_completo,
            "nome_usuario":  nome_usuario,
            "email":         email,
            "senha":         senha,
            "foto":          foto or "",
        })
        return r["id"]

    def verificar_login(self, usuario: str, senha: str) -> dict | None:
        print(f"🔵 Verificando login para: {usuario}")
        try:
            r = _post("/tarefas-app/auth/login", {
                "usuario": usuario,
                "senha":   senha,
            })
            print("🟢 Login bem-sucedido!")
            return {
                "id":             r["user_id"],
                "nome_completo":  r["nome_completo"],
                "nome_usuario":   r["nome_usuario"],
                "email":          r["email"],
                "trocar_senha":   r.get("trocar_senha", False),
                "foto":           r.get("foto"),
                "telegram_chat_id": r.get("telegram_chat_id"),
            }
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                return None
            raise
        except Exception as e:
            if "401" in str(e) or "autenticação" in str(e).lower():
                return None
            raise

    def verificar_usuario_existe(self, nome_usuario: str) -> bool:
        try:
            usuarios = _get("/tarefas-app/usuarios")
            # BUG CORRIGIDO: campo correto é "nome_usuario", não "nome"
            return any(u.get("nome_usuario") == nome_usuario for u in usuarios)
        except:
            return False

    def verificar_email_existe(self, email: str) -> bool:
        try:
            usuarios = _get("/tarefas-app/usuarios")
            return any(u.get("email") == email for u in usuarios)
        except:
            return False

    def definir_senha_temporaria(self, email: str, senha_temp: str) -> bool:
        try:
            print(f"🔵 Definindo senha temporária para: {email}")
            _post("/tarefas-app/auth/senha-temporaria", {
                "email":      email,
                "senha_temp": senha_temp,
            })
            return True
        except:
            return False

    def atualizar_senha_definitiva(self, user_id: int, nova_senha: str) -> bool:
        """
        Atualiza para senha definitiva.
        Endpoint: PUT /tarefas-app/auth/atualizar-senha
        Body: { "user_id": ..., "nova_senha": ... }
        """
        try:
            print(f"🔵 Atualizando senha do usuário {user_id}")
            _put("/tarefas-app/auth/atualizar-senha", {
                "user_id":    user_id,
                "nova_senha": nova_senha,
            })
            return True
        except Exception as e:
            print(f"🔴 Erro ao atualizar senha: {e}")
            return False

    def buscar_dados_por_email(self, email: str) -> tuple | None:
        """Retorna (telegram_chat_id, nome_completo) pelo e-mail."""
        try:
            print(f"🔵 Buscando dados por email: {email}")
            usuarios = _get("/tarefas-app/usuarios")
            for u in usuarios:
                if u.get("email") == email:
                    # BUG CORRIGIDO: campo correto é "nome_completo", não "nome"
                    return (u.get("telegram_chat_id"), u.get("nome_completo"))
            return None
        except:
            return None

    def buscar_dados_por_email_ou_id(self, user_id: int) -> dict | None:
        try:
            print(f"🔵 Buscando usuário por ID: {user_id}")
            return _get(f"/tarefas-app/usuarios/{user_id}")
        except:
            return None

    def vincular_telegram(self, user_id: int, telegram_id) -> bool:
        try:
            print(f"🔵 Vinculando Telegram ao usuário {user_id} com chat_id {telegram_id}")
            _post("/tarefas-app/usuarios/telegram", {
                "user_id":     user_id,
                "telegram_id": str(telegram_id),
            })
            print("🟢 Telegram vinculado com sucesso!")
            return True
        except Exception as e:
            print(f"🔴 Erro ao vincular Telegram: {e}")
            return False

    def buscar_telegram_id(self, user_id: int) -> str | None:
        try:
            print(f"🔵 Buscando Telegram ID do usuário {user_id}")
            r = _get(f"/tarefas-app/usuarios/{user_id}/telegram")
            return r.get("telegram_chat_id")
        except:
            return None

    def listar_usuarios_com_telegram(self) -> list:
        try:
            print("🔵 Listando usuários com Telegram")
            return _get("/tarefas-app/usuarios/telegram/todos")
        except:
            return []

    def atualizar_perfil(self, user_id: int, nome_completo: str, email: str, foto=None) -> bool:
        try:
            print(f"🔵 Atualizando perfil do usuário {user_id}")
            _put(f"/tarefas-app/usuarios/{user_id}", {
                "nome":  nome_completo,
                "email": email,
                "ativo": True,
            })
            return True
        except:
            return False


# ══════════════════════════════════════════════════════════════════════
# PROXY: TarefaModel
# ══════════════════════════════════════════════════════════════════════
class TarefaModel:
    """Proxy da API para substituir o TarefaModel original."""

    def criar_tabela(self):
        pass

    def criar(self, usuario_id: int, titulo: str, descricao: str = None,
              status: str = "depois") -> int:
        print(f"🔵 Criando tarefa para usuário {usuario_id}: {titulo}")
        r = _post("/tarefas-app/tarefas", {
            "titulo":      titulo,
            "descricao":   descricao,
            "responsavel": None,
            "usuario_id":  usuario_id,
            "prazo":       None,
            "status":      status,
        })
        return r["id"]

    def listar_por_usuario(self, usuario_id: int) -> list:
        print(f"🔵 Listando tarefas do usuário {usuario_id}")
        try:
            dados = _get(f"/tarefas-app/tarefas/{usuario_id}")
            return [self._dict_para_tupla(d) for d in dados]
        except Exception as e:
            print(f"🔴 Erro ao listar tarefas: {e}")
            return []

    def listar_nao_arquivadas(self, usuario_id: int) -> list:
        return self.listar_por_usuario(usuario_id)

    def listar_arquivadas(self, usuario_id: int) -> list:
        try:
            print(f"🔵 Listando tarefas arquivadas do usuário {usuario_id}")
            dados = _get(f"/tarefas-app/tarefas/arquivadas/{usuario_id}")
            return [self._dict_para_tupla_arquivada(d) for d in dados]
        except Exception as e:
            print(f"🔴 Erro ao listar tarefas arquivadas: {e}")
            return []

    def buscar_por_id(self, tarefa_id: int) -> dict | None:
        try:
            print(f"🔵 Buscando tarefa {tarefa_id}")
            d = _get(f"/tarefas-app/tarefas/detalhe/{tarefa_id}")
            # Converte datas
            for campo in ("data_vencimento",):
                if d.get(campo) and isinstance(d[campo], str):
                    try:
                        d[campo] = date.fromisoformat(d[campo][:10])
                    except:
                        pass
            for campo in ("data_criacao", "data_conclusao"):
                if d.get(campo) and isinstance(d[campo], str):
                    try:
                        d[campo] = datetime.fromisoformat(d[campo])
                    except:
                        pass
            # Fallback: se descricao_longa estiver vazia, usa descricao (campo legado)
            if not d.get("descricao_longa") and d.get("descricao"):
                d["descricao_longa"] = d["descricao"]
            # Garante que comentarios nunca seja None
            if d.get("comentarios") is None:
                d["comentarios"] = ""
            return d
        except Exception as e:
            print(f"🔴 Erro ao buscar tarefa: {e}")
            return None

    def atualizar_detalhes(
        self,
        tarefa_id: int,
        titulo: str,
        descricao_longa: str,
        fase: str,
        data_vencimento,
        responsavel: str,
        comentarios: str,
    ) -> bool:
        """
        Atualiza os detalhes completos de uma tarefa.
        Endpoint: PUT /tarefas-app/tarefas/{tarefa_id}

        ATENÇÃO: O campo "fase" do detalhe é diferente do "status" do kanban.
        O PUT espera um "status" válido (pendente, em_andamento, etc.).
        A fase visual ("Em análise", etc.) é atualizada pelo PATCH /fase separadamente.
        Por isso mandamos status="em_andamento" como padrão e atualizamos
        só os campos de detalhe aqui.
        """
        try:
            print(f"🔵 Atualizando detalhes da tarefa {tarefa_id}")

            # Converte data para string ISO se necessário
            prazo_str = None
            if data_vencimento:
                if isinstance(data_vencimento, (date, datetime)):
                    prazo_str = data_vencimento.isoformat()
                else:
                    prazo_str = str(data_vencimento)

            # BUG CORRIGIDO: não mapear "fase" para "status"
            # O PUT atualiza os campos de detalhe; status não muda aqui.
            # Primeiro busca o status atual para não sobrescrever.
            tarefa_atual = self.buscar_por_id(tarefa_id)
            status_atual = tarefa_atual.get("status", "em_andamento") if tarefa_atual else "em_andamento"

            _put(f"/tarefas-app/tarefas/{tarefa_id}", {
                "titulo":          titulo,
                "descricao":       descricao_longa,
                "descricao_longa": descricao_longa,
                "comentarios":     comentarios or "",
                "responsavel":     responsavel or "",
                "usuario_id":      tarefa_atual.get("usuario_id") if tarefa_atual else None,
                "prazo":           prazo_str,
                "status":          status_atual,
                "fase":            fase,
            })
            print(f"🟢 Detalhes da tarefa {tarefa_id} atualizados com sucesso")
            return True
        except Exception as e:
            print(f"🔴 Erro ao atualizar detalhes: {e}")
            return False

    def atualizar_status(self, tarefa_id: int, novo_status: str) -> bool:
        try:
            print(f"🔵 Atualizando status da tarefa {tarefa_id} para {novo_status}")
            _patch(f"/tarefas-app/tarefas/{tarefa_id}/status", {"status": novo_status})
            return True
        except Exception as e:
            print(f"🔴 Erro ao atualizar status: {e}")
            return False

    def atualizar_fase(self, tarefa_id: int, nova_fase: str) -> bool:
        try:
            print(f"🔵 Atualizando fase da tarefa {tarefa_id} para {nova_fase}")
            _patch(f"/tarefas-app/tarefas/{tarefa_id}/fase", {"fase": nova_fase})
            return True
        except Exception as e:
            print(f"🔴 Erro ao atualizar fase: {e}")
            return False

    def excluir(self, tarefa_id: int) -> bool:
        try:
            print(f"🔵 Excluindo tarefa {tarefa_id}")
            _delete(f"/tarefas-app/tarefas/{tarefa_id}")
            return True
        except Exception as e:
            print(f"🔴 Erro ao excluir tarefa: {e}")
            return False

    def arquivar_manual(self, tarefa_id: int) -> bool:
        try:
            print(f"🔵 Arquivando tarefa {tarefa_id}")
            _patch(f"/tarefas-app/tarefas/{tarefa_id}/arquivar")
            return True
        except Exception as e:
            print(f"🔴 Erro ao arquivar tarefa: {e}")
            return False

    def restaurar_do_arquivo(self, tarefa_id: int) -> bool:
        try:
            print(f"🔵 Restaurando tarefa {tarefa_id}")
            _patch(f"/tarefas-app/tarefas/{tarefa_id}/restaurar")
            return True
        except Exception as e:
            print(f"🔴 Erro ao restaurar tarefa: {e}")
            return False

    def excluir_permanentemente(self, tarefa_id: int) -> bool:
        try:
            print(f"🔵 Excluindo permanentemente tarefa {tarefa_id}")
            _delete(f"/tarefas-app/tarefas/{tarefa_id}/permanente")
            return True
        except Exception as e:
            print(f"🔴 Erro ao excluir permanentemente: {e}")
            return False

    def arquivar_tarefas_antigas(self, usuario_id=None) -> int:
        try:
            print(f"🔵 Arquivando tarefas antigas do usuário {usuario_id}")
            params = {"usuario_id": usuario_id} if usuario_id else {}
            r = requests.post(
                f"{_URL}/tarefas-app/tarefas/arquivar-antigas",
                headers=_HEADERS,
                params=params,
                timeout=_TIMEOUT,
            )
            r.raise_for_status()
            return r.json().get("arquivadas", 0)
        except Exception as e:
            print(f"ℹ️ Endpoint de arquivar não disponível: {e}")
            return 0

    # =================================================================
    # CHECKLIST
    # =================================================================

    def checklist_listar(self, tarefa_id: int) -> list:
        try:
            print(f"🔵 Listando checklist da tarefa {tarefa_id}")
            dados = _get(f"/tarefas-app/tarefas/{tarefa_id}/checklist")
            return [(item["id"], item["texto"], item["concluido"]) for item in dados]
        except Exception as e:
            print(f"🔴 Erro ao listar checklist: {e}")
            return []

    def checklist_adicionar(self, tarefa_id: int, texto: str) -> int:
        try:
            print(f"🔵 Adicionando item ao checklist da tarefa {tarefa_id}: {texto}")
            r = _post(f"/tarefas-app/tarefas/{tarefa_id}/checklist", {"texto": texto})
            return r["id"]
        except Exception as e:
            print(f"🔴 Erro ao adicionar item ao checklist: {e}")
            raise

    def checklist_marcar(self, item_id: int, concluido: bool) -> bool:
        try:
            print(f"🔵 Marcando item {item_id} como {concluido}")
            _patch(f"/tarefas-app/checklist/{item_id}", {"concluido": concluido})
            return True
        except Exception as e:
            print(f"🔴 Erro ao marcar item do checklist: {e}")
            return False

    def checklist_excluir(self, item_id: int) -> bool:
        try:
            print(f"🔵 Excluindo item {item_id} do checklist")
            _delete(f"/tarefas-app/checklist/{item_id}")
            return True
        except Exception as e:
            print(f"🔴 Erro ao excluir item do checklist: {e}")
            return False

    # =================================================================
    # HELPERS INTERNOS
    # =================================================================

    def _dict_para_tupla(self, d: dict) -> tuple:
        """
        Converte dict da API para tupla no formato esperado pelo dashboard:
        (id, titulo, descricao, status, data_criacao, fase, data_vencimento, responsavel)
        """
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
            parse_dt(d.get("data_criacao")),
            d.get("fase") or d.get("status"),
            parse_date(d.get("data_vencimento")),
            d.get("responsavel"),
        )

    def _dict_para_tupla_arquivada(self, d: dict) -> tuple:
        t = self._dict_para_tupla(d)
        def parse_dt(v):
            if not v:
                return None
            try:
                return datetime.fromisoformat(str(v))
            except:
                return None
        return t + (parse_dt(d.get("data_conclusao")),)