import requests

TOKEN = '8592583916:AAHSN8S0659NxYs8hiH5K6ceD1_zuxxCBHw'
CHAT_ID = 1827262343

mensagem = """
<b>Tem Tarefas? ✅</b>

Olá! 👋

Recebemos uma solicitação de <b>recuperação de senha</b> para sua conta.

Para continuar, utilize o código abaixo:

<code>847291</code>

Ou clique no link:
<a href="https://seusite.com/reset">Redefinir senha</a>

Se você não solicitou, ignore este e-mail.

<i>Equipe Tem Tarefas</i>
"""

requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML"
    }
)