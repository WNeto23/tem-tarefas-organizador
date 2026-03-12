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
from datetime import datetime, date
import pytz
from typing import Dict, List, Optional

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
        return response.json()
    except Exception as e:
        log(f"❌ Erro ao buscar usuários com Telegram: {e}")
        return []

def get_tarefas_usuario(user_id: int) -> List[Dict]:
    """Busca tarefas não arquivadas de um usuário"""
    try:
        url = f"{API_URL}/tarefas-app/tarefas/{user_id}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log(f"❌ Erro ao buscar tarefas do usuário {user_id}: {e}")
        return []

def enviar_telegram(chat_id: str, texto: str) -> bool:
    """Envia mensagem via Telegram"""
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
        "concluidas": []     # concluídas
    }
    
    for t in tarefas:
        if not isinstance(t, dict):
            continue
            
        titulo = t.get("titulo", "Sem título")
        status = t.get("status", "pendente")
        fase = t.get("fase", "em_andamento")
        data_venc = t.get("data_vencimento") or t.get("prazo")
        
        # Ignora concluídas/arquivadas
        if fase in ["resolvido", "cancelado", "concluida"]:
            classificadas["concluidas"].append(titulo)
            continue
            
        classificadas["pendentes"].append(titulo)
        
        if data_venc:
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
        for t in classificadas["pendentes"][:10]:  # Limite de 10
            linhas.append(f"  • {t}")
        if len(classificadas["pendentes"]) > 10:
            linhas.append(f"  ... e mais {len(classificadas['pendentes'])-10} tarefas")
    else:
        linhas.append("  ✅ Nenhuma tarefa pendente!")
    
    linhas.append("")
    linhas.append(f"`{'─' * 30}`")
    linhas.append(f"🕒 {datetime.now(TZ).strftime('%H:%M')}")
    
    return "\n".join(linhas)

def gerar_urgentes(nome: str, tarefas: List[Dict]) -> str:
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
    
    # Verifica token
    if not TOKEN_TELEGRAM:
        log("❌ TOKEN_TELEGRAM não configurado")
        return
    
    # Determina o tipo de notificação baseado no horário
    hora = datetime.now(TZ).hour
    minuto = datetime.now(TZ).minute
    
    if hora == 8 and minuto < 10:
        tipo = "completo"
        titulo = "RESUMO COMPLETO DO DIA"
    elif hora == 9 and minuto < 10:
        tipo = "pendentes"
        titulo = "TAREFAS PENDENTES"
    elif hora == 13 and minuto < 10:
        tipo = "urgentes"
        titulo = "ALERTA DE URGÊNCIA"
    elif hora == 16 and minuto < 10:
        tipo = "tarde"
        titulo = "PENDÊNCIAS DA TARDE"
    elif hora == 18 and minuto < 10:
        tipo = "resumo"
        titulo = "RESUMO FINAL DO DIA"
    else:
        log(f"⏰ Horário {hora:02d}:{minuto:02d} - sem notificação programada")
        return
    
    log(f"📋 Tipo de notificação: {tipo}")
    
    # Busca usuários com Telegram
    usuarios = get_usuarios_com_telegram()
    log(f"👥 Encontrados {len(usuarios)} usuários com Telegram")
    
    if not usuarios:
        log("⚠️ Nenhum usuário com Telegram encontrado")
        return
    
    # Processa cada usuário
    for usuario in usuarios:
        user_id = usuario.get("id") or usuario.get("user_id")
        nome = usuario.get("nome_completo") or usuario.get("nome", "Usuário")
        chat_id = usuario.get("telegram_chat_id")
        
        if not chat_id:
            continue
            
        log(f"📱 Processando usuário: {nome} (ID: {user_id})")
        
        # Busca tarefas do usuário
        tarefas = get_tarefas_usuario(user_id)
        log(f"📊 Encontradas {len(tarefas)} tarefas")
        
        if not tarefas:
            continue
        
        # Gera mensagem conforme o tipo
        mensagem = None
        if tipo == "completo":
            mensagem = gerar_resumo_completo(nome, tarefas)
        elif tipo in ["pendentes", "tarde", "resumo"]:
            mensagem = gerar_resumo_pendentes(nome, tarefas, titulo)
        elif tipo == "urgentes":
            mensagem = gerar_urgentes(nome, tarefas)
        
        if mensagem:
            log(f"📨 Enviando mensagem para {nome}...")
            if enviar_telegram(chat_id, mensagem):
                log(f"✅ Mensagem enviada com sucesso")
            else:
                log(f"❌ Falha ao enviar mensagem")
    
    log("✅ Notificador finalizado")

if __name__ == "__main__":
    main()