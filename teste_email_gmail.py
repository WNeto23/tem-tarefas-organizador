import smtplib
from email.mime.text import MIMEText

# CONFIGURAÇÕES
EMAIL = "temtarefasorganizador@gmail.com"
SENHA = "wmiv glce cqic scsx"
DESTINO = "waltuiro.neto@unimedrv.com.br"

msg = MIMEText("Teste de envio de email via Python com Gmail.")
msg["Subject"] = "Teste Python Gmail"
msg["From"] = EMAIL
msg["To"] = DESTINO

try:
    servidor = smtplib.SMTP("smtp.gmail.com", 587)
    servidor.starttls()
    servidor.login(EMAIL, SENHA)
    servidor.send_message(msg)
    servidor.quit()

    print("✅ Email enviado com sucesso!")

except Exception as e:
    print("❌ Erro:", e)