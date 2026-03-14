"""
notificador_tarefas.py
======================
Envia notificações com botões inline para o Telegram.
"""
import os
import requests
from datetime import datetime, date
import pytz
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Carrega o .env da raiz do projeto (funciona em qualquer subpasta)
load_dotenv(Path(__file__).parent.parent / ".env")

API_URL        = os.getenv("API_URL_TAREFAS", "https://web-apitarefas.up.railway.app")
API_TOKEN      = os.getenv("API_TOKEN_TAREFAS", "")
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM", "")
TZ             = pytz.timezone("America/Sao_Paulo")

HEADERS = {
    "x-token": API_TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

STATUS_VALIDOS = ["pendente", "em_andamento", "concluida", "pra_ja", "depois", "se_der_tempo"]
STATUS_EMOJI   = {
    "pra_ja":       "🔥",
    "depois":       "📋",
    "se_der_tempo": "🕐",
    "pendente":     "⏳",
    "em_andamento": "🔄",
    "concluida":    "✅",
}

HORARIOS_UTC = {
    11: ("completo",  "RESUMO COMPLETO DO DIA"),
    12: ("pendentes", "TAREFAS PENDENTES — MANHÃ"),
    16: ("urgentes",  "ALERTA DE URGÊNCIA"),
    19: ("tarde",     "PENDÊNCIAS DA TARDE"),
    21: ("resumo",    "RESUMO FINAL DO DIA"),
}

SEP = "━━━━━━━━━━━━━━━━━━━━"


# ── Helpers ───────────────────────────────────────────────────────────

def log(msg: str):
    print(f"[{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def get_usuarios_com_telegram() -> List[Dict]:
    try:
        r = requests.get(f"{API_URL}/tarefas-app/usuarios/telegram/todos",
                         headers=HEADERS, timeout=15)
        r.raise_for_status()
        usuarios = r.json()
        log(f"✅ {len(usuarios)} usuário(s) com Telegram")
        return usuarios
    except Exception as e:
        log(f"❌ Erro ao buscar usuários: {e}")
        return []

def get_tarefas_usuario(user_id: int) -> List[Dict]:
    try:
        r = requests.get(f"{API_URL}/tarefas-app/tarefas/{user_id}",
                         headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f"❌ Erro ao buscar tarefas do usuário {user_id}: {e}")
        return []

def enviar_telegram(chat_id: str, texto: str, reply_markup: dict = None) -> bool:
    """Envia mensagem com ou sem botões inline."""
    payload = {
        "chat_id":                  chat_id,
        "text":                     texto,
        "parse_mode":               "Markdown",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage",
            json=payload,
            timeout=10,
        )
        r.raise_for_status()
        log(f"✅ Mensagem enviada → {chat_id}")
        return True
    except Exception as e:
        log(f"❌ Erro Telegram → {chat_id}: {e}")
        return False


# ── Botões inline ─────────────────────────────────────────────────────

def teclado_padrao(user_id: int) -> dict:
    """
    Botões que aparecem em todas as notificações.
    callback_data usa o padrão: "acao:user_id" ou "acao:user_id:tarefa_id"
    """
    return {
        "inline_keyboard": [
            [
                {"text": "📊 Resumo agora",    "callback_data": f"resumo:{user_id}"},
                {"text": "📋 Ver pendências",  "callback_data": f"pendentes:{user_id}"},
            ],
            [
                {"text": "🔕 Silenciar hoje",  "callback_data": f"silenciar:{user_id}"},
                {"text": "✅ Marcar resolvida", "callback_data": f"marcar_menu:{user_id}"},
            ],
        ]
    }

def teclado_marcar_tarefas(user_id: int, tarefas: List[Dict]) -> dict:
    """
    Gera botões para marcar as tarefas pendentes como resolvidas.
    Mostra até 5 tarefas para não poluir.
    """
    pendentes = [
        t for t in tarefas
        if t.get("status") != "concluida"
        and t.get("fase") not in ("resolvido", "cancelado", "cancelada", "suspenso")
    ][:5]

    botoes = []
    for t in pendentes:
        titulo_curto = t["titulo"][:30] + "…" if len(t["titulo"]) > 30 else t["titulo"]
        botoes.append([{
            "text":          f"✅ {titulo_curto}",
            "callback_data": f"concluir:{user_id}:{t['id']}",
        }])

    botoes.append([{"text": "◀️ Voltar", "callback_data": f"resumo:{user_id}"}])
    return {"inline_keyboard": botoes}


# ── Classificação ─────────────────────────────────────────────────────

def classificar_tarefas(tarefas: List[Dict]) -> Dict:
    hoje = date.today()
    resultado = {
        "urgentes":   [],
        "proximas":   [],
        "sem_prazo":  [],
        "pendentes":  [],
        "por_status": {s: [] for s in STATUS_VALIDOS},
    }
    for t in tarefas:
        if not isinstance(t, dict):
            continue
        titulo = t.get("titulo", "Sem título")
        status = t.get("status", "pendente")
        fase   = t.get("fase", "em_andamento")

        if status in resultado["por_status"]:
            resultado["por_status"][status].append(t)

        fases_ignorar = ("resolvido", "cancelado", "cancelada", "suspenso")
        if status == "concluida" or fase in fases_ignorar:
            continue

        resultado["pendentes"].append(titulo)

        data_venc = t.get("data_vencimento")
        if data_venc:
            if isinstance(data_venc, str):
                try:
                    data_venc = date.fromisoformat(data_venc[:10])
                except Exception:
                    resultado["sem_prazo"].append(titulo)
                    continue
            dias = (data_venc - hoje).days
            if dias <= 0:
                resultado["urgentes"].append((titulo, abs(dias)))
            elif dias <= 3:
                resultado["proximas"].append((titulo, dias))
        else:
            resultado["sem_prazo"].append(titulo)

    return resultado


# ── Prioridade e insight ──────────────────────────────────────────────

def calcular_prioridade(tarefa: Dict) -> int:
    score = 0
    status    = tarefa.get("status", "")
    fase      = tarefa.get("fase", "")
    data_venc = tarefa.get("data_vencimento")
    hoje      = date.today()

    if status == "pra_ja":     score += 50
    elif status == "pendente": score += 20
    if fase == "parado":       score += 10

    if data_venc:
        if isinstance(data_venc, str):
            try: data_venc = date.fromisoformat(data_venc[:10])
            except: return score
        dias = (data_venc - hoje).days
        if dias < 0:    score += 40
        elif dias == 0: score += 30
        elif dias <= 3: score += 15

    return score

def tarefas_prioritarias(tarefas: List[Dict], limite: int = 3) -> List[str]:
    scored = []
    for t in tarefas:
        if t.get("status") == "concluida": continue
        if t.get("fase") in ("resolvido", "cancelado", "cancelada", "suspenso"): continue
        scored.append((calcular_prioridade(t), t.get("titulo", "Sem título")))
    scored.sort(reverse=True)
    return [titulo for _, titulo in scored[:limite]]

def gerar_insight(tarefas: List[Dict]) -> str:
    c          = classificar_tarefas(tarefas)
    total      = len(tarefas)
    urgentes   = len(c["urgentes"])
    pendentes  = len(c["pendentes"])
    # Conta por fase=resolvido (campo real no banco)
    concluidas = sum(1 for t in tarefas if t.get("fase") == "resolvido")

    if urgentes > 0:
        return f"⚠️ Você tem *{urgentes} tarefa(s) urgente(s)*. Priorize agora."
    if pendentes > 5:
        return f"📋 Existem *{pendentes} tarefas* pendentes. Hora de priorizar."
    if concluidas > 0 and total > 0:
        pct = int((concluidas / total) * 100)
        return f"📈 Você concluiu *{pct}%* das tarefas. Continue!"
    return "💡 Continue avançando nas suas tarefas!"

def bloco_sugestao(tarefas: List[Dict]) -> List[str]:
    prioridades = tarefas_prioritarias(tarefas)
    if not prioridades:
        return []
    nums = ["1️⃣", "2️⃣", "3️⃣"]
    linhas = ["", "🧠 *Sugestão de prioridade:*"]
    for i, titulo in enumerate(prioridades):
        linhas.append(f"{nums[i]} {titulo}")
    return linhas


# ── Mensagens ─────────────────────────────────────────────────────────

def msg_resumo_completo(nome: str, tarefas: List[Dict]) -> str:
    hoje = datetime.now(TZ).strftime("%d/%m/%Y")
    hora = datetime.now(TZ).strftime("%H:%M")
    c    = classificar_tarefas(tarefas)

    linhas = [
        f"📋 *RESUMO DO DIA*",
        SEP,
        f"👤 *{nome}*",
        f"📅 {hoje}  🕒 {hora}",
        SEP, "",
    ]

    if c["urgentes"]:
        linhas.append("🚨 *URGENTES / ATRASADAS*")
        for titulo, dias in c["urgentes"]:
            label = "VENCE HOJE" if dias == 0 else f"ATRASADA {dias}d"
            linhas += [f"🔴 *{label}*", f"  _{titulo}_", ""]

    if c["proximas"]:
        linhas.append("⏰ *VENCEM EM BREVE*")
        for titulo, dias in c["proximas"]:
            linhas += [f"🟡 *Vence em {dias}d*", f"  _{titulo}_", ""]

    linhas.append("📊 *POR STATUS*")
    for status, lista in c["por_status"].items():
        if lista and status != "concluida":
            emoji = STATUS_EMOJI.get(status, "📌")
            linhas.append(f"{emoji} {status.replace('_',' ').title()}: *{len(lista)}*")

    linhas += ["", SEP, f"📌 *Total pendente:* {len(c['pendentes'])}", "",
               gerar_insight(tarefas)]
    linhas += bloco_sugestao(tarefas)
    return "\n".join(linhas)

def msg_pendentes(nome: str, tarefas: List[Dict], titulo: str) -> str:
    hora = datetime.now(TZ).strftime("%H:%M")
    c    = classificar_tarefas(tarefas)

    linhas = [f"📋 *{titulo}*", SEP, f"👤 *{nome}*", SEP, ""]

    if c["pendentes"]:
        for i, t in enumerate(c["pendentes"][:10], 1):
            linhas.append(f"{i}. {t}")
        if len(c["pendentes"]) > 10:
            linhas.append(f"_...e mais {len(c['pendentes']) - 10} tarefas_")
    else:
        linhas.append("✅ Nenhuma tarefa pendente!")

    linhas += ["", SEP,
               f"📌 *Total:* {len(c['pendentes'])} pendente(s)  🕒 {hora}",
               "", gerar_insight(tarefas)]
    linhas += bloco_sugestao(tarefas)
    return "\n".join(linhas)

def msg_urgentes(nome: str, tarefas: List[Dict]) -> Optional[str]:
    hora = datetime.now(TZ).strftime("%H:%M")
    c    = classificar_tarefas(tarefas)

    if not c["urgentes"] and not c["proximas"]:
        return None

    linhas = [f"🚨 *ALERTA DE URGÊNCIA*", SEP,
              f"👤 *{nome}*, atenção agora:", SEP, ""]

    for titulo, dias in c["urgentes"]:
        label = "VENCE HOJE" if dias == 0 else f"ATRASADA {dias}d"
        linhas += [f"🔴 *{label}*", f"  _{titulo}_", ""]

    for titulo, dias in c["proximas"]:
        linhas += [f"🟡 *Vence em {dias}d*", f"  _{titulo}_", ""]

    linhas += [SEP, f"🕒 {hora}  ⚠️ Acesse o app para atualizar."]
    linhas += bloco_sugestao(tarefas)
    return "\n".join(linhas)

def msg_resumo_final(nome: str, tarefas: List[Dict]) -> str:
    hora       = datetime.now(TZ).strftime("%H:%M")
    hoje       = datetime.now(TZ).strftime("%d/%m/%Y")
    c          = classificar_tarefas(tarefas)
    total      = len(tarefas)
    # Conta por fase=resolvido (campo real no banco) e não por status=concluida
    concluidas = sum(1 for t in tarefas if t.get("fase") == "resolvido")
    pendentes  = len(c["pendentes"])
    urgentes   = len(c["urgentes"])
    produt     = int((concluidas / total) * 100) if total else 0

    linhas = [
        f"📊 *RESUMO FINAL DO DIA*", SEP,
        f"👤 *{nome}*", f"📅 {hoje}  🕒 {hora}", SEP, "",
        f"✅ Concluídas:  *{concluidas}*",
        f"📋 Pendentes:   *{pendentes}*",
        f"🔥 Urgentes:    *{urgentes}*", "",
        f"🏆 Produtividade: *{produt}%*", "",
        SEP, gerar_insight(tarefas),  # sem 💡 extra — gerar_insight já inclui
    ]
    linhas += bloco_sugestao(tarefas)
    linhas += ["", "Até amanhã! 👋"]
    return "\n".join(linhas)


# ── Main ──────────────────────────────────────────────────────────────

def main():
    log("🚀 Iniciando notificador de tarefas")

    if not TOKEN_TELEGRAM:
        log("❌ TOKEN_TELEGRAM não configurado"); return
    if not API_TOKEN:
        log("❌ API_TOKEN_TAREFAS não configurado"); return

    hora_utc = datetime.utcnow().hour
    log(f"⏰ Hora UTC atual: {hora_utc:02d}h")

    tipo, titulo_notif = HORARIOS_UTC.get(hora_utc, (None, None))
    if not tipo:
        tipo, titulo_notif = HORARIOS_UTC.get(hora_utc - 1, (None, None))
        if tipo:
            log(f"⚠️  Usando hora anterior ({hora_utc - 1}h UTC)")

    if not tipo:
        log(f"⏰ Hora {hora_utc:02d}h UTC — sem notificação programada"); return

    log(f"📋 Tipo: {tipo} — {titulo_notif}")

    usuarios = get_usuarios_com_telegram()
    if not usuarios:
        log("⚠️  Nenhum usuário com Telegram"); return

    enviados = falhas = 0

    for usuario in usuarios:
        user_id = usuario.get("id")
        nome    = usuario.get("nome_completo") or "Usuário"
        chat_id = usuario.get("telegram_chat_id")

        if not user_id or not chat_id:
            continue

        log(f"📱 Processando: {nome} (ID: {user_id})")
        tarefas = get_tarefas_usuario(user_id)

        if not tarefas:
            log(f"ℹ️  {nome} não tem tarefas"); continue

        if tipo == "completo":
            mensagem = msg_resumo_completo(nome, tarefas)
        elif tipo in ("pendentes", "tarde"):
            mensagem = msg_pendentes(nome, tarefas, titulo_notif)
        elif tipo == "urgentes":
            mensagem = msg_urgentes(nome, tarefas)
            if not mensagem:
                log(f"ℹ️  {nome} sem urgências — pulando"); continue
        elif tipo == "resumo":
            mensagem = msg_resumo_final(nome, tarefas)
        else:
            continue

        # Botões inline em todas as notificações
        teclado = teclado_padrao(user_id)

        if enviar_telegram(chat_id, mensagem, reply_markup=teclado):
            enviados += 1
        else:
            falhas += 1

    log(f"✅ Finalizado: {enviados} enviado(s), {falhas} falha(s)")


if __name__ == "__main__":
    main()