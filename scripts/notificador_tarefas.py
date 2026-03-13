"""
notificador_tarefas.py
======================
Script executado pelo GitHub Actions para enviar notificações de tarefas.
Determina o tipo de notificação pela hora UTC recebida via env HORARIO_UTC,
sem janela rígida de minutos — tolerante ao atraso do GitHub Actions.

Horários BRT → UTC:
  08:00 BRT = 11:00 UTC → resumo completo
  09:00 BRT = 12:00 UTC → tarefas pendentes
  13:00 BRT = 16:00 UTC → urgentes
  16:00 BRT = 19:00 UTC → pendências da tarde
  18:00 BRT = 21:00 UTC → resumo final
"""
import os
import requests
from datetime import datetime, date
import pytz
from typing import Dict, List, Optional

# ── Configurações ─────────────────────────────────────────────────────
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

# Mapa hora UTC → (tipo, título)
# O GitHub Actions dispara no horário UTC do cron.
# Usamos só a HORA (sem minuto) para tolerar atrasos.
HORARIOS_UTC = {
    11: ("completo",  "RESUMO COMPLETO DO DIA"),
    12: ("pendentes", "TAREFAS PENDENTES — MANHÃ"),
    16: ("urgentes",  "ALERTA DE URGÊNCIA"),
    19: ("tarde",     "PENDÊNCIAS DA TARDE"),
    21: ("resumo",    "RESUMO FINAL DO DIA"),
}


# ── Helpers ───────────────────────────────────────────────────────────
def log(msg: str):
    agora = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{agora}] {msg}")


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
        tarefas = r.json()
        log(f"✅ Usuário {user_id}: {len(tarefas)} tarefa(s)")
        return tarefas
    except Exception as e:
        log(f"❌ Erro ao buscar tarefas do usuário {user_id}: {e}")
        return []


def enviar_telegram(chat_id: str, texto: str) -> bool:
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": texto,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        r.raise_for_status()
        log(f"✅ Mensagem enviada → {chat_id}")
        return True
    except Exception as e:
        log(f"❌ Erro Telegram → {chat_id}: {e}")
        return False


# ── Classificação ─────────────────────────────────────────────────────
def classificar_tarefas(tarefas: List[Dict]) -> Dict:
    hoje = date.today()
    resultado = {
        "urgentes":   [],   # atrasadas ou vencem hoje → (titulo, dias_atraso)
        "proximas":   [],   # vencem em 1-3 dias → (titulo, dias)
        "sem_prazo":  [],   # sem data
        "pendentes":  [],   # todas não concluídas (titulo)
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

        # Ignora apenas quando REALMENTE finalizada:
        # - status "concluida" → coluna concluída no kanban
        # - fase "cancelado"   → cancelada explicitamente
        #
        # NOTIFICA tudo mais, incluindo:
        # - status: pra_ja, depois, se_der_tempo, pendente, em_andamento
        # - fase:   em_andamento, resolvido, parado, suspenso
        # Uma tarefa "resolvido" ou "parado" ainda aparece no kanban
        # e pode estar atrasada — deve ser notificada normalmente.
        if status == "concluida" or fase == "cancelado":
            continue

        resultado["pendentes"].append(titulo)

        data_venc = t.get("data_vencimento")
        if data_venc:
            if isinstance(data_venc, str):
                try:
                    data_venc = date.fromisoformat(data_venc[:10])
                except:
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


# ── Mensagens ─────────────────────────────────────────────────────────
def msg_resumo_completo(nome: str, tarefas: List[Dict]) -> str:
    hoje = datetime.now(TZ).strftime("%d/%m/%Y")
    c    = classificar_tarefas(tarefas)

    linhas = [
        f"📋 *RESUMO COMPLETO — {hoje}*",
        f"`{'─' * 30}`",
        f"",
        f"Bom dia, *{nome}*! 🌅",
        f"",
    ]

    if c["urgentes"]:
        linhas.append("🚨 *URGENTES / ATRASADAS:*")
        for titulo, dias in c["urgentes"]:
            linhas.append(f"  🔴 {'VENCE HOJE' if dias == 0 else f'ATRASADA {dias}d'} › {titulo}")
        linhas.append("")

    if c["proximas"]:
        linhas.append("⏰ *VENCEM EM BREVE:*")
        for titulo, dias in c["proximas"]:
            linhas.append(f"  🟡 {dias}d › {titulo}")
        linhas.append("")

    linhas.append("📊 *POR STATUS:*")
    for status, lista in c["por_status"].items():
        if lista and status != "concluida":
            emoji = STATUS_EMOJI.get(status, "📌")
            linhas.append(f"  {emoji} {status.replace('_', ' ').title()}: {len(lista)}")

    linhas += [
        "",
        f"`{'─' * 30}`",
        f"📌 Total pendente: {len(c['pendentes'])}",
        f"🕒 {datetime.now(TZ).strftime('%H:%M')}",
    ]
    return "\n".join(linhas)


def msg_pendentes(nome: str, tarefas: List[Dict], titulo: str) -> str:
    c = classificar_tarefas(tarefas)

    linhas = [
        f"📋 *{titulo}*",
        f"`{'─' * 30}`",
        f"",
        f"Olá *{nome}*, suas pendências:",
        f"",
    ]

    if c["pendentes"]:
        for i, t in enumerate(c["pendentes"][:10], 1):
            linhas.append(f"  {i}. {t}")
        if len(c["pendentes"]) > 10:
            linhas.append(f"  _...e mais {len(c['pendentes']) - 10} tarefas_")
    else:
        linhas.append("  ✅ Nenhuma tarefa pendente!")

    linhas += [
        "",
        f"`{'─' * 30}`",
        f"📌 Total: {len(c['pendentes'])} pendente(s)",
        f"🕒 {datetime.now(TZ).strftime('%H:%M')}",
    ]
    return "\n".join(linhas)


def msg_urgentes(nome: str, tarefas: List[Dict]) -> Optional[str]:
    c = classificar_tarefas(tarefas)

    if not c["urgentes"] and not c["proximas"]:
        return None

    linhas = [
        f"🚨 *ALERTA DE URGÊNCIA*",
        f"`{'─' * 30}`",
        f"",
        f"Olá *{nome}*, atenção:",
        f"",
    ]

    for titulo, dias in c["urgentes"]:
        linhas.append(f"  🔴 {'VENCE HOJE' if dias == 0 else f'ATRASADA {dias}d'} › {titulo}")

    for titulo, dias in c["proximas"]:
        linhas.append(f"  🟡 Vence em {dias}d › {titulo}")

    linhas += [
        "",
        f"`{'─' * 30}`",
        f"🕒 {datetime.now(TZ).strftime('%H:%M')}",
    ]
    return "\n".join(linhas)


# ── Main ──────────────────────────────────────────────────────────────
def main():
    log("🚀 Iniciando notificador de tarefas")

    if not TOKEN_TELEGRAM:
        log("❌ TOKEN_TELEGRAM não configurado")
        return
    if not API_TOKEN:
        log("❌ API_TOKEN_TAREFAS não configurado")
        return

    # Determina tipo pela hora UTC atual (tolerante a atrasos)
    hora_utc = datetime.utcnow().hour
    log(f"⏰ Hora UTC atual: {hora_utc:02d}h")

    tipo, titulo_notif = HORARIOS_UTC.get(hora_utc, (None, None))

    if not tipo:
        # Tenta hora anterior (caso atraso de ~1h)
        tipo, titulo_notif = HORARIOS_UTC.get(hora_utc - 1, (None, None))
        if tipo:
            log(f"⚠️  Horário exato não encontrado, usando hora anterior ({hora_utc - 1}h UTC)")

    if not tipo:
        log(f"⏰ Hora {hora_utc:02d}h UTC — sem notificação programada para este horário")
        return

    log(f"📋 Tipo: {tipo} — {titulo_notif}")

    usuarios = get_usuarios_com_telegram()
    if not usuarios:
        log("⚠️  Nenhum usuário com Telegram")
        return

    enviados = 0
    falhas   = 0

    for usuario in usuarios:
        user_id = usuario.get("id")
        nome    = usuario.get("nome_completo") or usuario.get("nome", "Usuário")
        chat_id = usuario.get("telegram_chat_id")

        if not user_id or not chat_id:
            log(f"⚠️  Usuário sem id ou chat_id: {usuario}")
            continue

        log(f"📱 Processando: {nome} (ID: {user_id})")

        tarefas = get_tarefas_usuario(user_id)
        if not tarefas:
            log(f"ℹ️  {nome} não tem tarefas")
            continue

        if tipo == "completo":
            mensagem = msg_resumo_completo(nome, tarefas)
        elif tipo in ("pendentes", "tarde", "resumo"):
            mensagem = msg_pendentes(nome, tarefas, titulo_notif)
        elif tipo == "urgentes":
            mensagem = msg_urgentes(nome, tarefas)
            if not mensagem:
                log(f"ℹ️  {nome} não tem tarefas urgentes — pulando")
                continue
        else:
            continue

        if enviar_telegram(chat_id, mensagem):
            enviados += 1
        else:
            falhas += 1

    log(f"✅ Finalizado: {enviados} enviado(s), {falhas} falha(s)")


if __name__ == "__main__":
    main()