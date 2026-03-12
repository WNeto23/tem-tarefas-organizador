import requests
import json

url = "https://web-apitarefas.up.railway.app/tarefas-app/auth/login"
headers = {"Content-Type": "application/json"}
data = {
    "usuario": "wneto",
    "senha": "Neto2308@"
}

print(f"Enviando requisição para: {url}")
print(f"Dados: {data}")

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Resposta: {response.text}")
    
    if response.status_code == 200:
        print("✅ Login bem-sucedido!")
        print(f"Token: {response.json().get('access_token')}")
    else:
        print(f"❌ Erro: {response.status_code}")
        
except Exception as e:
    print(f"❌ Erro na requisição: {e}")