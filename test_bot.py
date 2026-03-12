import requests

TOKEN = "8592583916:AAHSN8S0659NxYs8hiH5K6ceD1_zuxxCBHw"  # Cole o token correto

def testar_bot():
    url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    response = requests.get(url)
    print("Status Code:", response.status_code)
    print("Resposta:", response.json())

if __name__ == "__main__":
    testar_bot()