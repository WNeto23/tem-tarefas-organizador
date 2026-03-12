"""
notificador_tarefas.py
Script executado pelo GitHub Actions para enviar notificações de tarefas
"""

import os
import requests
from datetime import datetime, date
import pytz
from typing import Dict, List

# ------------------------------
# Configurações
# ------------------------------

API_URL = os.getenv("API_URL_TAREFAS", "https://web-apitarefas.up.railway.app")
API_TOKEN = os.getenv("API_TOKEN_TAREFAS", "")
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM", "")

TZ = pytz.timezone("America/Sao_Paulo")

HEADERS = {
    "x-token": API_TOKEN,
    "Accept": "application/json"
}

session = requests.Session()

# ------------------------------
# Utilidades
# ------------------------------

def log(msg: str):
    agora = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{agora}] {msg}")


def request_with_retry(method, url, **kwargs):
    """Executa requisição com retry automático"""
    for tentativa in range(3):
        try:
            response = session.request(method, url, timeout=15, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            if tentativa == 2:
                log(f"❌ Erro definitivo na requisição {url}: {e}")
                return None
            log("🔄 Tentando novamente...")


# ------------------------------
# API
# ------------------------------

def get_usuarios_com_telegram() -> List[Dict]:

    url = f"{API_URL}/tarefas-app/usuarios/telegram/todos"

    response = request_with_retry("GET", url, headers=HEADERS)

    if not response:
        return []

    try:
        return response.json()
    except Exception:
        log("❌ Erro ao interpretar resposta da API")
        return []


def get_tarefas_usuario(user_id: int) -> List[Dict]:

    url = f"{API_URL}/tarefas-app/tarefas/{user_id}"

    response = request_with_retry("GET", url, headers=HEADERS)

    if not response:
        return []

    try:
        return response.json()
    except Exception:
        log("❌ Erro ao interpretar tarefas")
        return []


# ------------------------------
# Telegram
# ------------------------------

def enviar_telegram(chat_id: str, texto: str) -> bool:

    if len(texto) > 4000:
        texto = texto[:3900] + "\n\n... mensagem truncada"

    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    response = request_with_retry("POST", url, json=payload)

    return response is not None


# ------------------------------
# Classificação de tarefas
# ------------------------------

def classificar_tarefas(tarefas: List[Dict]) -> Dict:

    hoje = date.today()

    classificadas = {
        "urgentes": [],
        "proximas": [],
        "futuras": [],
        "sem_prazo": [],
        "pendentes": [],
        "concluidas": []
    }

    for t in tarefas:

        if not isinstance(t, dict):
            continue

        titulo = t.get("titulo", "Sem título")
        fase = t.get("fase", "em_andamento")
        data_venc = t.get("data_vencimento") or t.get("prazo")

        if fase in ["resolvido", "cancelado", "concluida"]:
            classificadas["concluidas"].append(titulo)
            continue

        classificadas["pendentes"].append(titulo)

        if data_venc:

            try:
                if isinstance(data_venc, str):
                    data_venc = date.fromisoformat(data_venc)

                dias = (data_venc - hoje).days

                if dias < 0:
                    classificadas["urgentes"].append((titulo, abs(dias)))
                elif dias == 0:
                    classificadas["urgentes"].append((titulo, 0))
                elif dias <= 3:
                    classificadas["proximas"].append((titulo, dias))
                else:
                    classificadas["futuras"].append((titulo, dias))

            except Exception:
                classificadas["sem_prazo"].append(titulo)

        else:
            classificadas["sem_prazo"].append(titulo)

    return classificadas


# ------------------------------
# Mensagens
# ------------------------------

def gerar_resumo_completo(nome: str, tarefas: List[Dict]) -> str:

    hoje = datetime.now(TZ).strftime("%d/%m/%Y")
    classificadas = classificar_tarefas(tarefas)

    linhas = [
        f"📋 *RESUMO COMPLETO — {hoje}*",
        f"`{'─' * 30}`",
        "",
        f"Olá *{nome}*! Bom dia! 🌅",
        ""
    ]

    if classificadas["urgentes"]:

        linhas.append("🚨 *URGENTES / ATRASADAS:*")

        for titulo, dias in classificadas["urgentes"]:
            if dias == 0:
                linhas.append(f"  🔴 VENCE HOJE › {titulo}")
            else:
                linhas.append(f"  ⚠️ ATRASADA {dias}d › {titulo}")

        linhas.append("")

    if classificadas["proximas"]:

        linhas.append("⏰ *VENCEM EM BREVE:*")

        for titulo, dias in classificadas["proximas"]:
            linhas.append(f"  🟡 {dias}d › {titulo}")

        linhas.append("")

    total_pendentes = len(classificadas["pendentes"])

    linhas.append(f"`{'─' * 30}`")
    linhas.append(f"📊 Total pendente: {total_pendentes}")
    linhas.append(f"🕒 Gerado às {datetime.now(TZ).strftime('%H:%M')}")

    return "\n".join(linhas)


def gerar_urgentes(nome: str, tarefas: List[Dict]):

    classificadas = classificar_tarefas(tarefas)

    if not classificadas["urgentes"]:
        return None

    linhas = [
        "🚨 *ALERTA DE URGÊNCIA*",
        f"`{'─' * 30}`",
        "",
        f"Olá *{nome}*, você tem tarefas urgentes:",
        ""
    ]

    for titulo, dias in classificadas["urgentes"]:

        if dias == 0:
            linhas.append(f"  🔴 VENCE HOJE › {titulo}")
        else:
            linhas.append(f"  ⚠️ ATRASADA {dias}d › {titulo}")

    linhas.append("")
    linhas.append(f"`{'─' * 30}`")
    linhas.append(f"🕒 {datetime.now(TZ).strftime('%H:%M')}")

    return "\n".join(linhas)


# ------------------------------
# Main
# ------------------------------

def main():

    log("🚀 Iniciando notificador")

    if not TOKEN_TELEGRAM:
        log("❌ TOKEN_TELEGRAM não configurado")
        return

    if not API_TOKEN:
        log("❌ API_TOKEN_TAREFAS não configurado")
        return

    agora = datetime.now(TZ)
    hora = agora.hour
    minuto = agora.minute

    if hora == 8 and minuto < 10:
        tipo = "completo"
    elif hora == 13 and minuto < 10:
        tipo = "urgentes"
    else:
        log(f"⏰ {hora}:{minuto} - sem notificação programada")
        return

    usuarios = get_usuarios_com_telegram()

    log(f"👥 {len(usuarios)} usuários encontrados")

    total_enviadas = 0

    for usuario in usuarios:

        user_id = usuario.get("id") or usuario.get("user_id")
        nome = usuario.get("nome_completo") or usuario.get("nome", "Usuário")
        chat_id = usuario.get("telegram_chat_id")

        if not chat_id:
            continue

        log(f"📱 {nome}")

        tarefas = get_tarefas_usuario(user_id)

        if not tarefas:
            continue

        if tipo == "completo":
            mensagem = gerar_resumo_completo(nome, tarefas)
        else:
            mensagem = gerar_urgentes(nome, tarefas)

        if mensagem:

            if enviar_telegram(chat_id, mensagem):
                total_enviadas += 1
                log("✅ Enviado")

            else:
                log("❌ Falha envio")

    log(f"📊 {total_enviadas} mensagens enviadas")
    log("🏁 Finalizado")


if __name__ == "__main__":
    main()