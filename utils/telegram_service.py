import requests
import logging
from requests.exceptions import Timeout, ConnectionError, RequestException

logger = logging.getLogger(__name__)

# MELHORIA 1: constantes fora da classe
TIMEOUT_PADRAO = 5
TIMEOUT_ENVIO  = 10  # envio pode precisar de um pouco mais


class TelegramService:
    def __init__(self, token: str):
        # MELHORIA 2: valida o token na inicialização
        if not token:
            raise ValueError("TOKEN_TELEGRAM não encontrado no .env")
        self.token    = token
        self.base_url = f"https://api.telegram.org/bot{self.token}"

        # MELHORIA 3: Session reutiliza a conexão TCP entre chamadas
        # em vez de abrir e fechar uma conexão nova a cada requests.get/post
        self.session = requests.Session()

    def capturar_id_automatico(self, codigo_esperado: str = None) -> tuple[int | None, str | None]:
        """
        Busca a última mensagem recebida pelo bot e confirma a leitura.
        Se codigo_esperado for fornecido, verifica se a mensagem contém exatamente esse código.
        Retorna (chat_id, primeiro_nome) ou (None, None) se não houver mensagens válidas.
        """
        url = f"{self.base_url}/getUpdates"
        try:
            response = self.session.get(url, timeout=TIMEOUT_PADRAO)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok") or not data.get("result"):
                logger.info("Nenhum update encontrado")
                return None, None

            # Pega o update mais recente
            ultimo_update = data["result"][-1]
            update_id = ultimo_update["update_id"]

            # Confirma leitura (marca como processado)
            self.session.get(
                url,
                params={"offset": update_id + 1},
                timeout=TIMEOUT_PADRAO
            )

            if "message" not in ultimo_update:
                logger.info("Update não contém mensagem")
                return None, None

            mensagem = ultimo_update["message"]
            chat_id = mensagem["chat"]["id"]
            first_name = mensagem["from"].get("first_name", "Usuário")
            
            # Pega o texto da mensagem
            texto = mensagem.get("text", "")
            logger.info(f"Mensagem recebida: '{texto}' de {first_name} (chat_id: {chat_id})")
            
            # Se um código foi esperado, verifica se a mensagem contém exatamente ele
            if codigo_esperado:
                if texto.strip() != codigo_esperado:
                    logger.warning(f"Código incorreto. Esperado: '{codigo_esperado}', Recebido: '{texto}'")
                    return None, None
                logger.info(f"Código validado com sucesso!")

            return chat_id, first_name

        except Timeout:
            logger.warning("Timeout ao buscar updates do Telegram")
            return None, None
        except ConnectionError:
            logger.warning("Sem conexão ao buscar updates do Telegram")
            return None, None
        except RequestException as e:
            logger.error(f"Erro de requisição ao Telegram (getUpdates): {e}")
            return None, None
        except (KeyError, ValueError) as e:
            logger.error(f"Resposta inesperada da API do Telegram: {e}")
            return None, None

    def enviar_mensagem(self, chat_id: int | str, texto: str) -> bool:
        """
        Envia uma mensagem para o chat_id especificado.
        Retorna True se enviada com sucesso, False caso contrário.
        """
        # MELHORIA 7: a função original não retornava nada — impossível saber se falhou
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id":    chat_id,
            "text":       texto,
            "parse_mode": "Markdown",
            # MELHORIA 8: desativa preview de links nas notificações do app
            "disable_web_page_preview": True,
        }
        try:
            response = self.session.post(url, json=payload, timeout=TIMEOUT_ENVIO)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                # MELHORIA 9: loga a descrição de erro que a API do Telegram devolve
                logger.error(f"Telegram recusou a mensagem: {data.get('description')}")
                return False

            return True

        except Timeout:
            logger.warning(f"Timeout ao enviar mensagem para chat_id {chat_id}")
            return False
        except ConnectionError:
            logger.warning("Sem conexão ao enviar mensagem pelo Telegram")
            return False
        except RequestException as e:
            logger.error(f"Erro de requisição ao Telegram (sendMessage): {e}")
            return False

    def close(self):
        """MELHORIA 3: fecha a Session quando o serviço não for mais usado"""
        self.session.close()