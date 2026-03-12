import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# MELHORIA 1: logger no lugar de print — em produção você consegue
# redirecionar para arquivo, Sentry, etc. sem mudar o código
logger = logging.getLogger(__name__)

# MELHORIA 2: constantes fora da função — eram recriadas a cada chamada
SMTP_SERVER    = "smtp.gmail.com"
SMTP_PORT      = 587
AMARELO_BANANA = '#F2C94C'
CINZA_FUNDO    = '#121212'
CINZA_CARD     = '#1E1E1E'


def _construir_html(nome_usuario: str, senha_provisoria: str) -> str:
    """
    MELHORIA 3: HTML extraído para função privada.
    Mantém enviar_email_recuperacao() limpa e focada só no envio.
    """
    ano_atual = datetime.now().year  # MELHORIA 4: rodapé com ano dinâmico no e-mail

    return f"""
    <html>
    <body style="margin:0; padding:0; font-family:sans-serif;
                 background-color:{CINZA_FUNDO}; color:white;">

        <table width="100%" border="0" cellspacing="0" cellpadding="0"
               style="background-color:{CINZA_FUNDO}; padding:40px 0;">
            <tr>
                <td align="center">
                    <table width="400" border="0" cellspacing="0" cellpadding="0"
                           style="background-color:{CINZA_CARD}; border-radius:30px;
                                  padding:40px; text-align:center;
                                  border:1px solid {AMARELO_BANANA}33;">
                        <tr>
                            <td>
                                <!-- Cabeçalho -->
                                <h1 style="color:{AMARELO_BANANA}; margin-bottom:10px;">
                                    ✅ Tem Tarefas?
                                </h1>
                                <p style="font-size:18px; font-weight:bold; margin-bottom:25px;">
                                    Senha Temporária
                                </p>

                                <!-- Saudação -->
                                <p style="color:#CCCCCC; line-height:1.6; font-size:14px;">
                                    Olá, <strong>{nome_usuario}</strong>!<br>
                                    Use o código abaixo para acessar sua conta.
                                    Você deverá criar uma nova senha assim que fizer o login.
                                </p>

                                <!-- Código de acesso -->
                                <div style="margin:30px 0; padding:20px;
                                            background-color:{CINZA_FUNDO};
                                            border:2px dashed {AMARELO_BANANA};
                                            border-radius:15px;">
                                    <span style="color:#888888; font-size:11px;
                                                 text-transform:uppercase; letter-spacing:2px;">
                                        CÓDIGO DE ACESSO:
                                    </span><br>
                                    <span style="color:{AMARELO_BANANA}; font-size:32px;
                                                 font-weight:bold;
                                                 font-family:'Courier New', monospace;
                                                 letter-spacing:5px;">
                                        {senha_provisoria}
                                    </span>
                                </div>

                                <!-- MELHORIA 5: aviso de validade -->
                                <div style="margin:0 0 20px 0; padding:12px;
                                            background-color:#1a1a2e;
                                            border-left:3px solid {AMARELO_BANANA};
                                            border-radius:8px; text-align:left;">
                                    <span style="color:{AMARELO_BANANA}; font-size:12px;">
                                        ⏱️ Este código é válido por <strong>30 minutos</strong>.
                                    </span>
                                </div>

                                <!-- Aviso de segurança -->
                                <p style="color:#888888; font-size:12px;">
                                    🔒 Por segurança, não compartilhe este código com ninguém.<br>
                                    Se você não solicitou a recuperação, ignore este e-mail.
                                </p>

                                <!-- MELHORIA 4: rodapé com ano dinâmico -->
                                <hr style="border:none; border-top:1px solid #333333; margin:25px 0;">
                                <p style="color:#555555; font-size:11px; margin:0;">
                                    🇧🇷 © {ano_atual} Tem Tarefas? · Todos os direitos reservados
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>

    </body>
    </html>
    """


def enviar_email_recuperacao(destinatario: str, senha_provisoria: str, nome_usuario: str = "Usuário") -> bool:
    """
    Envia e-mail com senha temporária para recuperação de acesso.
    Retorna True se enviado com sucesso, False caso contrário.
    """
    email_sender   = os.getenv("GMAIL_USER")
    email_password = os.getenv("GMAIL_APP_PASS")

    # MELHORIA 6: valida credenciais antes de tentar conectar
    if not email_sender or not email_password:
        logger.error("Credenciais de e-mail não encontradas no .env (GMAIL_USER / GMAIL_APP_PASS)")
        return False

    msg = MIMEMultipart()
    msg["From"]    = f"Tem Tarefas? <{email_sender}>"
    msg["To"]      = destinatario
    msg["Subject"] = "🟡 Sua Senha Temporária - Tem Tarefas?"
    # MELHORIA 7: header anti-spam — marca o e-mail como transacional
    msg["X-Priority"]        = "1"
    msg["X-Mailer"]          = "Tem Tarefas? Mailer"
    msg.attach(MIMEText(_construir_html(nome_usuario, senha_provisoria), "html"))

    # MELHORIA 8: with garante que a conexão fecha mesmo se der erro,
    # sem precisar chamar server.quit() manualmente
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(email_sender, email_password)
            server.send_message(msg)

        logger.info(f"E-mail de recuperação enviado para {destinatario}")
        return True

    except smtplib.SMTPAuthenticationError:
        # MELHORIA 9: exceções específicas com mensagens úteis
        logger.error("Falha de autenticação no Gmail. Verifique GMAIL_USER e GMAIL_APP_PASS no .env")
        return False

    except smtplib.SMTPRecipientsRefused:
        logger.error(f"Destinatário recusado pelo servidor: {destinatario}")
        return False

    except TimeoutError:
        logger.error("Timeout ao conectar ao servidor SMTP do Gmail")
        return False

    except Exception as e:
        logger.error(f"Erro inesperado ao enviar e-mail: {e}")
        return False