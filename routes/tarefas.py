"""
routes/tarefas.py
=================
Endpoints do sistema de Tarefas.

Token  : API_TOKEN_TAREFAS  (header x-token)
Banco  : NEON_CONN_DB       (db_tarefas)
Prefix : /tarefas-app

REGRA IMPORTANTE: rotas estáticas SEMPRE antes de rotas com parâmetros
  ✅ /usuarios/login          (estática)
  ✅ /usuarios/cadastrar      (estática)
  ✅ /usuarios/telegram/todos (estática)
  ✅ /usuarios/{user_id}      (parâmetro — vai por último)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel as PydanticBase
from typing import Optional
from datetime import date

from security import token_tarefas
from models.tarefa import TarefaModel
from models.usuario import UsuarioModel

router = APIRouter(
    prefix="/tarefas-app",
    dependencies=[Depends(token_tarefas)],
)


# ── Schemas ───────────────────────────────────────────────────────────

class UsuarioCadastro(PydanticBase):
    nome_completo: str
    nome_usuario:  str
    email:         str
    senha:         str
    foto:          Optional[str] = None

class UsuarioLogin(PydanticBase):
    usuario: str
    senha:   str

class UsuarioPerfil(PydanticBase):
    nome_completo: str
    email:         str
    foto:          Optional[str] = None

class AlterarSenha(PydanticBase):
    user_id:    int
    nova_senha: str

class SenhaTemporaria(PydanticBase):
    email:      str
    senha_temp: str

class TelegramVinculo(PydanticBase):
    user_id:     int
    telegram_id: str

class TarefaCriar(PydanticBase):
    usuario_id: int
    titulo:     str
    descricao:  Optional[str] = None
    status:     str = "depois"

class TarefaDetalhes(PydanticBase):
    titulo:          str
    descricao_longa: Optional[str] = None
    fase:            str
    data_vencimento: Optional[date] = None
    responsavel:     Optional[str] = None
    comentarios:     Optional[str] = None

class TarefaStatus(PydanticBase):
    status: str

class TarefaTitulo(PydanticBase):
    titulo: str

class ChecklistItem(PydanticBase):
    texto: str

class ChecklistMarcar(PydanticBase):
    concluido: bool


# ══════════════════════════════════════════════════════════════════════
# USUÁRIOS — rotas estáticas primeiro, parâmetros por último
# ══════════════════════════════════════════════════════════════════════

@router.get("/usuarios/telegram/todos", tags=["Tarefas - Usuários"])
def listar_usuarios_telegram():
    return UsuarioModel().listar_usuarios_com_telegram()


@router.post("/usuarios/cadastrar", tags=["Tarefas - Usuários"])
def cadastrar_usuario(dados: UsuarioCadastro):
    m = UsuarioModel()
    if m.verificar_usuario_existe(dados.nome_usuario):
        raise HTTPException(status_code=409, detail="Nome de usuário já existe")
    if m.verificar_email_existe(dados.email):
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    user_id = m.cadastrar(
        dados.nome_completo, dados.nome_usuario,
        dados.email, dados.senha, dados.foto
    )
    return {"id": user_id, "mensagem": "Usuário cadastrado com sucesso"}


@router.post("/usuarios/login", tags=["Tarefas - Usuários"])
def autenticar_usuario(dados: UsuarioLogin):
    usuario = UsuarioModel().verificar_login(dados.usuario, dados.senha)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    return usuario


@router.post("/usuarios/senha-temporaria", tags=["Tarefas - Usuários"])
def senha_temporaria(dados: SenhaTemporaria):
    ok = UsuarioModel().definir_senha_temporaria(dados.email, dados.senha_temp)
    if not ok:
        raise HTTPException(status_code=404, detail="E-mail não encontrado")
    return {"mensagem": "Senha temporária definida"}


@router.post("/usuarios/telegram", tags=["Tarefas - Usuários"])
def vincular_telegram(dados: TelegramVinculo):
    ok = UsuarioModel().vincular_telegram(dados.user_id, dados.telegram_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"mensagem": "Telegram vinculado"}


# ── Rotas com parâmetro /{user_id} — SEMPRE após as estáticas ────────

@router.get("/usuarios/{user_id}", tags=["Tarefas - Usuários"])
def buscar_usuario(user_id: int):
    usuario = UsuarioModel().buscar_dados_por_email_ou_id(user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario


@router.put("/usuarios/{user_id}/perfil", tags=["Tarefas - Usuários"])
def atualizar_perfil(user_id: int, dados: UsuarioPerfil):
    ok = UsuarioModel().atualizar_perfil(user_id, dados.nome_completo, dados.email, dados.foto)
    if not ok:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"mensagem": "Perfil atualizado"}


@router.put("/usuarios/{user_id}/senha", tags=["Tarefas - Usuários"])
def alterar_senha(user_id: int, dados: AlterarSenha):
    ok = UsuarioModel().atualizar_senha_definitiva(user_id, dados.nova_senha)
    if not ok:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"mensagem": "Senha alterada com sucesso"}


@router.get("/usuarios/{user_id}/telegram", tags=["Tarefas - Usuários"])
def buscar_telegram(user_id: int):
    telegram_id = UsuarioModel().buscar_telegram_id(user_id)
    return {"telegram_chat_id": telegram_id}


# ══════════════════════════════════════════════════════════════════════
# TAREFAS — rotas estáticas primeiro, parâmetros por último
# ══════════════════════════════════════════════════════════════════════

@router.post("/tarefas", tags=["Tarefas"])
def criar_tarefa(dados: TarefaCriar):
    tarefa_id = TarefaModel().criar(
        dados.usuario_id, dados.titulo, dados.descricao, dados.status
    )
    return {"id": tarefa_id, "mensagem": "Tarefa criada"}


@router.get("/tarefas/detalhe/{tarefa_id}", tags=["Tarefas"])
def buscar_tarefa(tarefa_id: int):
    tarefa = TarefaModel().buscar_por_id(tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return tarefa


@router.get("/tarefas/{usuario_id}", tags=["Tarefas"])
def listar_tarefas(usuario_id: int, arquivadas: bool = False):
    m = TarefaModel()
    if arquivadas:
        return m.listar_arquivadas(usuario_id)
    return m.listar_nao_arquivadas(usuario_id)


@router.put("/tarefas/{tarefa_id}/detalhes", tags=["Tarefas"])
def atualizar_detalhes(tarefa_id: int, dados: TarefaDetalhes):
    ok = TarefaModel().atualizar_detalhes(
        tarefa_id, dados.titulo, dados.descricao_longa,
        dados.fase, dados.data_vencimento,
        dados.responsavel, dados.comentarios
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return {"mensagem": "Tarefa atualizada"}


@router.patch("/tarefas/{tarefa_id}/status", tags=["Tarefas"])
def atualizar_status(tarefa_id: int, dados: TarefaStatus):
    ok = TarefaModel().atualizar_status(tarefa_id, dados.status)
    if not ok:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return {"mensagem": "Status atualizado"}


@router.patch("/tarefas/{tarefa_id}/titulo", tags=["Tarefas"])
def atualizar_titulo(tarefa_id: int, dados: TarefaTitulo):
    ok = TarefaModel().atualizar_titulo(tarefa_id, dados.titulo)
    if not ok:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return {"mensagem": "Título atualizado"}


@router.delete("/tarefas/{tarefa_id}", tags=["Tarefas"])
def excluir_tarefa(tarefa_id: int):
    if not TarefaModel().excluir(tarefa_id):
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return {"mensagem": "Tarefa excluída"}


@router.patch("/tarefas/{tarefa_id}/arquivar", tags=["Tarefas"])
def arquivar_tarefa(tarefa_id: int):
    ok = TarefaModel().arquivar_manual(tarefa_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return {"mensagem": "Tarefa arquivada"}


@router.patch("/tarefas/{tarefa_id}/restaurar", tags=["Tarefas"])
def restaurar_tarefa(tarefa_id: int):
    ok = TarefaModel().restaurar_do_arquivo(tarefa_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return {"mensagem": "Tarefa restaurada"}


@router.delete("/tarefas/{tarefa_id}/permanente", tags=["Tarefas"])
def excluir_permanente(tarefa_id: int):
    ok = TarefaModel().excluir_permanentemente(tarefa_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Tarefa não está arquivada ou não encontrada")
    return {"mensagem": "Tarefa excluída permanentemente"}


@router.post("/tarefas/{usuario_id}/arquivar-antigas", tags=["Tarefas"])
def arquivar_antigas(usuario_id: int):
    qtde = TarefaModel().arquivar_tarefas_antigas(usuario_id)
    return {"arquivadas": qtde}


# ══════════════════════════════════════════════════════════════════════
# CHECKLIST
# ══════════════════════════════════════════════════════════════════════

@router.get("/tarefas/{tarefa_id}/checklist", tags=["Tarefas - Checklist"])
def listar_checklist(tarefa_id: int):
    return TarefaModel().checklist_listar(tarefa_id)


@router.post("/tarefas/{tarefa_id}/checklist", tags=["Tarefas - Checklist"])
def adicionar_checklist(tarefa_id: int, dados: ChecklistItem):
    item_id = TarefaModel().checklist_adicionar(tarefa_id, dados.texto)
    return {"id": item_id, "mensagem": "Item adicionado"}


@router.patch("/checklist/{item_id}", tags=["Tarefas - Checklist"])
def marcar_checklist(item_id: int, dados: ChecklistMarcar):
    ok = TarefaModel().checklist_marcar(item_id, dados.concluido)
    if not ok:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return {"mensagem": "Item atualizado"}


@router.delete("/checklist/{item_id}", tags=["Tarefas - Checklist"])
def excluir_checklist(item_id: int):
    if not TarefaModel().checklist_excluir(item_id):
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return {"mensagem": "Item removido"}