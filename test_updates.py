import requests
import time

TOKEN = "8592583916:AAHSN8S0659NxYs8hiH5K6ceD1_zuxxCBHw"  # Seu token

def verificar_updates():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    
    # Limpa updates anteriores
    response = requests.get(url, params={"offset": -1})
    print("Limpando updates...")
    
    # Aguarda o usuário enviar mensagem
    input("\n📱 Envie uma mensagem para o bot no Telegram e pressione ENTER...")
    
    # Busca as mensagens
    response = requests.get(url, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Resposta completa: {response.json()}")

if __name__ == "__main__":
    verificar_updates()