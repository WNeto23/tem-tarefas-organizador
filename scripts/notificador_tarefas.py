"""
notificador_tarefas.py
=====================
Script executado pelo GitHub Actions para enviar notificações de tarefas.
Envia mensagens para Telegram com base no horário:
- 08:00: Resumo completo do dia
- 09:00: Tarefas pendentes
- 13:00: Tarefas urgentes (vencendo hoje/atrasadas)
- 16:00: Pendências da tarde
- 18:00: Resumo final
"""
import os
import requests
import json
from datetime import datetime, date, timedelta
import pytz
from typing import Dict, List, Optional, Tuple

# Configurações
API_URL = os.getenv("API_URL_TAREFAS", "https://web-apitarefas.up.railway.app")
API_TOKEN = os.getenv("API_TOKEN_TAREFAS", "")
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM", "")
TZ = pytz.timezone("America/Sao_Paulo")

# Headers para API
HEADERS = {
    "x-token": API_TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Status válidos
STATUS_VALIDOS = ["pendente", "em_andamento", "concluida", "pra_ja", "depois", "se_der_tempo"]

# Cores para emojis
STATUS_EMOJI = {
    "pra_ja": "🔥",
    "depois": "📋",
    "se_der_tempo": "🕐",
    "pendente": "⏳",
    "em_andamento": "🔄",
    "concluida": "✅"
}

def log(msg: str):
    """Log com timestamp"""
    agora = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{agora}] {msg}")

def get_usuarios_com_telegram() -> List[Dict]:
    """Busca usuários com Telegram vinculado"""
    try:
        url = f"{API_URL}/tarefas-app/usuarios/telegram/todos"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        usuarios = response.json()
        log(f"✅ Encontrados {len(usuarios)} usuários com Telegram")
        return usuarios
    except Exception as e:
        log(f"❌ Erro ao buscar usuários com Telegram: {e}")
        return []

def get_tarefas_usuario(user_id: int) -> List[Dict]:
    """Busca tarefas não arquivadas de um usuário"""
    try:
        url = f"{API_URL}/tarefas-app/tarefas/{user_id}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        tarefas = response.json()
        log(f"✅ Usuário {user_id}: {len(tarefas)} tarefas encontradas")
        return tarefas
    except Exception as e:
        log(f"❌ Erro ao buscar tarefas do usuário {user_id}: {e}")
        return []

def enviar_telegram(chat_id: str, texto: str) -> bool:
    """Envia mensagem via Telegram"""
    if not TOKEN_TELEGRAM:
        log("❌ TOKEN_TELEGRAM não configurado")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": texto,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        log(f"✅ Mensagem enviada para chat_id {chat_id}")
        return True
    except Exception as e:
        log(f"❌ Erro ao enviar Telegram para {chat_id}: {e}")
        return False

def classificar_tarefas(tarefas: List[Dict]) -> Dict:
    """Classifica tarefas por categoria"""
    hoje = date.today()
    
    classificadas = {
        "urgentes": [],      # atrasadas ou vencem hoje
        "proximas": [],      # vencem em 1-3 dias
        "futuras": [],       # vencem em mais de 3 dias
        "sem_prazo": [],     # sem data de vencimento
        "pendentes": [],     # todas não concluídas
        "concluidas": [],    # concluídas
        "por_status": {}     # organizado por status
    }
    
    # Inicializa por_status
    for status in STATUS_VALIDOS:
        classificadas["por_status"][status] = []
    
    for t in tarefas:
        if not isinstance(t, dict):
            continue
            
        titulo = t.get("titulo", "Sem título")
        status = t.get("status", "pendente")
        fase = t.get("fase", "em_andamento")
        data_venc = t.get("data_vencimento")
        
        # Adiciona à organização por status
        if status in classificadas["por_status"]:
            classificadas["por_status"][status].append(t)
        
        # Ignora concluídas/arquivadas
        if fase in ["resolvido", "cancelado", "concluida"] or status == "concluida":
            classificadas["concluidas"].append(titulo)
            continue
            
        classificadas["pendentes"].append(titulo)
        
        if data_venc:
            if isinstance(data_venc, str):
                try:
                    data_venc = date.fromisoformat(data_venc)
                except:
                    continue
            dias = (data_venc - hoje).days
            
            if dias < 0:
                classificadas["urgentes"].append((titulo, abs(dias)))
            elif dias == 0:
                classificadas["urgentes"].append((titulo, 0))
            elif dias <= 3:
                classificadas["proximas"].append((titulo, dias))
            else:
                classificadas["futuras"].append((titulo, dias))
        else:
            classificadas["sem_prazo"].append(titulo)
    
    return classificadas

def gerar_resumo_completo(nome: str, tarefas: List[Dict]) -> str:
    """Gera resumo completo do dia (08:00)"""
    hoje = datetime.now(TZ).strftime("%d/%m/%Y")
    classificadas = classificar_tarefas(tarefas)
    
    linhas = [
        f"📋 *RESUMO COMPLETO — {hoje}*",
        f"`{'─' * 30}`",
        f"",
        f"Olá *{nome}*! Bom dia! 🌅",
        f""
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
    
    # Adiciona resumo por status
    linhas.append("📊 *TAREFAS POR STATUS:*")
    for status, lista in classificadas["por_status"].items():
        if lista and status not in ["concluida"]:
            emoji = STATUS_EMOJI.get(status, "📌")
            linhas.append(f"  {emoji} {status.replace('_', ' ').title()}: {len(lista)}")
    linhas.append("")
    
    total_pendentes = len(classificadas["pendentes"])
    linhas.append(f"`{'─' * 30}`")
    linhas.append(f"📊 Total pendente: {total_pendentes}")
    linhas.append(f"🕒 Gerado às {datetime.now(TZ).strftime('%H:%M')}")
    
    return "\n".join(linhas)

def gerar_resumo_pendentes(nome: str, tarefas: List[Dict], titulo: str) -> str:
    """Gera resumo de pendências"""
    classificadas = classificar_tarefas(tarefas)
    
    linhas = [
        f"📋 *{titulo}*",
        f"`{'─' * 30}`",
        f"",
        f"Olá *{nome}*, aqui estão suas pendências:",
        f""
    ]
    
    if classificadas["pendentes"]:
        for i, t in enumerate(classificadas["pendentes"][:10], 1):
            linhas.append(f"  {i}. {t}")
        if len(classificadas["pendentes"]) > 10:
            linhas.append(f"  ... e mais {len(classificadas['pendentes'])-10} tarefas")
    else:
        linhas.append("  ✅ Nenhuma tarefa pendente!")
    
    linhas.append("")
    linhas.append(f"`{'─' * 30}`")
    linhas.append(f"📊 Total: {len(classificadas['pendentes'])} pendentes")
    linhas.append(f"🕒 {datetime.now(TZ).strftime('%H:%M')}")
    
    return "\n".join(linhas)

def gerar_urgentes(nome: str, tarefas: List[Dict]) -> Optional[str]:
    """Gera alerta de tarefas urgentes"""
    classificadas = classificar_tarefas(tarefas)
    
    if not classificadas["urgentes"]:
        return None
    
    linhas = [
        f"🚨 *ALERTA DE URGÊNCIA*",
        f"`{'─' * 30}`",
        f"",
        f"Olá *{nome}*, você tem tarefas urgentes:",
        f""
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

def main():
    log("🚀 Iniciando notificador de tarefas")
    
    # Verifica token do Telegram
    if not TOKEN_TELEGRAM:
        log("❌ TOKEN_TELEGRAM não configurado")
        return
    
    # Verifica token da API
    if not API_TOKEN:
        log("❌ API_TOKEN_TAREFAS não configurado")
        return
    
    # Determina o tipo de notificação baseado no horário
    agora = datetime.now(TZ)
    hora = agora.hour
    minuto = agora.minute
    
    # Mapeia horários para tipos de notificação
    horarios = {
        (8, 0, 15): ("completo", "RESUMO COMPLETO DO DIA"),
        (9, 0, 15): ("pendentes", "TAREFAS PENDENTES - MANHÃ"),
        (13, 0, 15): ("urgentes", "ALERTA DE URGÊNCIA"),
        (16, 0, 15): ("tarde", "PENDÊNCIAS DA TARDE"),
        (18, 0, 15): ("resumo", "RESUMO FINAL DO DIA"),
    }
    
    tipo_notificacao = None
    titulo_notificacao = None
    
    for (h, m_inicio, m_fim), (tipo, titulo) in horarios.items():
        if hora == h and m_inicio <= minuto <= m_fim:
            tipo_notificacao = tipo
            titulo_notificacao = titulo
            break
    
    if not tipo_notificacao:
        log(f"⏰ Horário {hora:02d}:{minuto:02d} - sem notificação programada")
        return
    
    log(f"📋 Tipo de notificação: {tipo_notificacao} - {titulo_notificacao}")
    
    # Busca usuários com Telegram
    usuarios = get_usuarios_com_telegram()
    
    if not usuarios:
        log("⚠️ Nenhum usuário com Telegram encontrado")
        return
    
    # Processa cada usuário
    enviados = 0
    falhas = 0
    
    for usuario in usuarios:
        user_id = usuario.get("id") or usuario.get("user_id")
        nome = usuario.get("nome_completo") or usuario.get("nome", "Usuário")
        chat_id = usuario.get("telegram_chat_id")
        
        if not chat_id:
            continue
            
        log(f"📱 Processando usuário: {nome} (ID: {user_id})")
        
        # Busca tarefas do usuário
        tarefas = get_tarefas_usuario(user_id)
        
        if not tarefas:
            log(f"ℹ️ Usuário {nome} não tem tarefas")
            continue
        
        # Gera mensagem conforme o tipo
        mensagem = None
        if tipo_notificacao == "completo":
            mensagem = gerar_resumo_completo(nome, tarefas)
        elif tipo_notificacao in ["pendentes", "tarde", "resumo"]:
            mensagem = gerar_resumo_pendentes(nome, tarefas, titulo_notificacao)
        elif tipo_notificacao == "urgentes":
            mensagem = gerar_urgentes(nome, tarefas)
        
        if mensagem:
            log(f"📨 Enviando mensagem para {nome}...")
            if enviar_telegram(chat_id, mensagem):
                enviados += 1
            else:
                falhas += 1
    
    log(f"✅ Notificador finalizado: {enviados} enviados, {falhas} falhas")

if __name__ == "__main__":
    main()