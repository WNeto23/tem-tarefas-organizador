import logging
import time
from database.connection import DatabaseConnection
from psycopg2 import InterfaceError, OperationalError

logger = logging.getLogger(__name__)

class BaseModel:
    def __init__(self):
        self.db            = DatabaseConnection()
        self.max_tentativas = 3

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        tentativa  = 0
        ultimo_erro = None
        while tentativa < self.max_tentativas:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(query, params or ())
                        if fetch_one:
                            return cur.fetchone()
                        elif fetch_all:
                            return cur.fetchall()
                        else:
                            return cur.rowcount
            except (InterfaceError, OperationalError) as e:
                tentativa  += 1
                ultimo_erro = e
                logger.warning(
                    f"Erro de conexão (tentativa {tentativa}/{self.max_tentativas}): {e}"
                )
                if tentativa < self.max_tentativas:
                    time.sleep(0.5 * tentativa)
                continue
            except Exception as e:
                logger.error(f"Erro inesperado na query: {e}")
                logger.error(f"Query: {query[:200]}")
                raise
        logger.error(
            f"Todas as {self.max_tentativas} tentativas falharam. Último erro: {ultimo_erro}"
        )
        if fetch_one:
            return None
        elif fetch_all:
            return []
        else:
            return 0

    def execute_query_safe(self, query, params=None, fetch_one=False, fetch_all=False):
        """Versão que nunca levanta exceção — útil para operações não críticas."""
        try:
            return self.execute_query(query, params, fetch_one, fetch_all)
        except Exception as e:
            logger.error(f"Erro em execute_query_safe: {e}")
            if fetch_one:
                return None
            elif fetch_all:
                return []
            else:
                return 0

    def testar_conexao(self) -> bool:
        try:
            result = self.execute_query("SELECT 1", fetch_one=True)
            return result is not None and result[0] == 1
        except Exception as e:
            logger.error(f"Falha no teste de conexão: {e}")
            return False