import os
import logging
import psycopg2
from psycopg2 import pool, OperationalError, InterfaceError
from dotenv import load_dotenv
from contextlib import contextmanager
from typing import Optional

load_dotenv()

logger = logging.getLogger(__name__)

POOL_MIN_CONN = 1
POOL_MAX_CONN = 10


class DatabaseConnection:
    _instance = None
    _pool     = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance

    def _initialize_pool(self):
        conn_string = os.getenv('NEON_CONN_DB')

        if not conn_string:
            raise EnvironmentError(
                "Variável NEON_CONN_DB não encontrada no .env — "
                "configure a string de conexão do NeonDB."
            )

        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                POOL_MIN_CONN,
                POOL_MAX_CONN,
                conn_string,
                sslmode='require',
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
                connect_timeout=10,  # 🔥 Timeout de conexão
            )
            logger.info("Conectado ao NeonDB com sucesso!")
        except OperationalError as e:
            logger.critical(f"Falha ao conectar ao NeonDB: {e}")
            raise

    def _testar_conexao(self, conn) -> bool:
        """Testa se a conexão ainda está viva"""
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            return True
        except (OperationalError, InterfaceError, psycopg2.Error) as e:
            logger.warning(f"Conexão morta detectada: {e}")
            return False

    @contextmanager
    def get_connection(self):
        if self._pool is None:
            raise RuntimeError("Pool de conexões não inicializado.")

        conn = None
        try:
            # Pega conexão do pool
            conn = self._pool.getconn()
            
            # Testa se a conexão está viva
            if not self._testar_conexao(conn):
                logger.warning("Conexão morta, obtendo nova...")
                self._pool.putconn(conn, close=True)
                conn = self._pool.getconn()
            
            yield conn
            conn.commit()  # Commit automático se tudo der certo
            
        except InterfaceError as e:
            # 🔥 Erro específico de conexão fechada
            logger.error(f"Erro de interface com banco: {e}")
            if conn and not conn.closed:
                try:
                    conn.rollback()
                except:
                    pass
            raise
            
        except Exception as e:
            # 🔥 Em caso de erro, tenta rollback apenas se a conexão estiver viva
            logger.error(f"Erro na operação com banco: {e}")
            if conn and not conn.closed:
                try:
                    conn.rollback()
                except (InterfaceError, OperationalError) as rb_error:
                    logger.error(f"Erro ao fazer rollback: {rb_error}")
            raise
            
        finally:
            # 🔥 Sempre tenta devolver a conexão ao pool
            if conn:
                try:
                    if conn.closed:
                        logger.warning("Conexão já estava fechada, não será devolvida ao pool")
                    else:
                        self._pool.putconn(conn)
                except (InterfaceError, OperationalError) as e:
                    logger.error(f"Erro ao devolver conexão ao pool: {e}")
                    # Se não conseguir devolver, tenta fechar
                    try:
                        if not conn.closed:
                            conn.close()
                    except:
                        pass

    def fechar_pool(self):
        """Encerra todas as conexões corretamente"""
        if self._pool:
            try:
                self._pool.closeall()
                logger.info("Pool de conexões encerrado.")
            except Exception as e:
                logger.error(f"Erro ao fechar pool: {e}")