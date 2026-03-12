import logging
from models.base_model import BaseModel

logger = logging.getLogger(__name__)

FASES_DISPONIVEIS = [
    ("🔄 Em análise",  "em_andamento"),
    ("✅ Resolvido",   "resolvido"),
    ("⏸️ Parado",      "parado"),
    ("🚫 Cancelado",   "cancelado"),
    ("⚠️ Suspenso",    "suspenso"),
]
STATUS_KANBAN = [
    ("🔥 Pra Já",       "pra_ja"),
    ("📋 Depois",       "depois"),
    ("🕐 Se Der Tempo", "se_der_tempo"),
]
CORES_STATUS = {
    "pra_ja":       "#FF5252",
    "depois":       "#FFB74D",
    "se_der_tempo": "#64B5F6",
    "em_andamento": "#BA68C8",
    "resolvido":    "#66BB6A",
    "parado":       "#9E9E9E",
    "cancelado":    "#D32F2F",
    "suspenso":     "#FFA726",
}

class TarefaModel(BaseModel):
    def criar_tabela(self):
        query = """
            CREATE TABLE IF NOT EXISTS tarefas (
                id              SERIAL PRIMARY KEY,
                usuario_id      INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
                titulo          VARCHAR(200) NOT NULL,
                descricao       TEXT,
                descricao_longa TEXT,
                status          VARCHAR(20) DEFAULT 'depois'
                    CHECK (status IN ('pra_ja', 'depois', 'se_der_tempo')),
                fase            VARCHAR(50) DEFAULT 'em_andamento',
                data_criacao    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_conclusao  TIMESTAMP,
                data_vencimento DATE,
                responsavel     VARCHAR(200),
                comentarios     TEXT
            )
        """
        self.execute_query(query)
        query_check = """
            CREATE TABLE IF NOT EXISTS checklist_itens (
                id           SERIAL PRIMARY KEY,
                tarefa_id    INTEGER REFERENCES tarefas(id) ON DELETE CASCADE,
                texto        VARCHAR(300) NOT NULL,
                concluido    BOOLEAN DEFAULT FALSE,
                ordem        INTEGER DEFAULT 0,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.execute_query(query_check)
        logger.info("Tabelas 'tarefas' e 'checklist_itens' verificadas/criadas")

    def criar(self, usuario_id: int, titulo: str, descricao: str = None, status: str = "depois") -> int:
        query = """
            INSERT INTO tarefas (usuario_id, titulo, descricao, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        result = self.execute_query(query, (usuario_id, titulo, descricao, status), fetch_one=True)
        return result[0]

    def listar_por_usuario(self, usuario_id: int) -> list:
        query = """
            SELECT id, titulo, descricao, status, data_criacao, fase,
                   data_vencimento, responsavel
            FROM tarefas
            WHERE usuario_id = %s
            ORDER BY
                CASE status
                    WHEN 'pra_ja'       THEN 1
                    WHEN 'depois'       THEN 2
                    WHEN 'se_der_tempo' THEN 3
                END,
                data_criacao DESC
        """
        return self.execute_query(query, (usuario_id,), fetch_all=True) or []

    def buscar_por_id(self, tarefa_id: int) -> dict | None:
        query = """
            SELECT id, titulo, descricao, descricao_longa, status, fase,
                   data_criacao, data_vencimento, responsavel, comentarios
            FROM tarefas WHERE id = %s
        """
        r = self.execute_query(query, (tarefa_id,), fetch_one=True)
        if not r:
            return None
        return {
            "id":              r[0],
            "titulo":          r[1],
            "descricao":       r[2],
            "descricao_longa": r[3],
            "status":          r[4],
            "fase":            r[5],
            "data_criacao":    r[6],
            "data_vencimento": r[7],
            "responsavel":     r[8],
            "comentarios":     r[9],
        }

    def atualizar_detalhes(
        self,
        tarefa_id: int,
        titulo: str,
        descricao_longa: str,
        fase: str,
        data_vencimento,
        responsavel: str,
        comentarios: str,
    ) -> bool:
        query = """
            UPDATE tarefas
            SET titulo          = %s,
                descricao_longa = %s,
                fase            = %s,
                data_vencimento = %s,
                responsavel     = %s,
                comentarios     = %s,
                data_conclusao  = CASE
                    WHEN %s = 'resolvido' THEN CURRENT_TIMESTAMP
                    ELSE NULL
                END
            WHERE id = %s
        """
        return self.execute_query(
            query,
            (titulo, descricao_longa, fase, data_vencimento,
             responsavel, comentarios, fase, tarefa_id)
        ) > 0

    def atualizar_fase(self, tarefa_id: int, nova_fase: str) -> bool:
        query = "UPDATE tarefas SET fase = %s WHERE id = %s"
        return self.execute_query(query, (nova_fase, tarefa_id)) > 0

    def atualizar_status(self, tarefa_id: int, novo_status: str) -> bool:
        query = """
            UPDATE tarefas
            SET status = %s,
                data_conclusao = CASE
                    WHEN %s = 'resolvido' THEN CURRENT_TIMESTAMP
                    ELSE data_conclusao
                END
            WHERE id = %s
        """
        return self.execute_query(query, (novo_status, novo_status, tarefa_id)) > 0

    def atualizar_titulo(self, tarefa_id: int, novo_titulo: str) -> bool:
        query = "UPDATE tarefas SET titulo = %s WHERE id = %s"
        return self.execute_query(query, (novo_titulo, tarefa_id)) > 0

    def excluir(self, tarefa_id: int) -> bool:
        query = "DELETE FROM tarefas WHERE id = %s"
        return self.execute_query(query, (tarefa_id,)) > 0

    # --- Checklist ---
    def checklist_listar(self, tarefa_id: int) -> list:
        query = """
            SELECT id, texto, concluido FROM checklist_itens
            WHERE tarefa_id = %s ORDER BY ordem, data_criacao
        """
        return self.execute_query(query, (tarefa_id,), fetch_all=True) or []

    def checklist_adicionar(self, tarefa_id: int, texto: str) -> int:
        query = """
            INSERT INTO checklist_itens (tarefa_id, texto)
            VALUES (%s, %s) RETURNING id
        """
        result = self.execute_query(query, (tarefa_id, texto), fetch_one=True)
        return result[0]

    def checklist_marcar(self, item_id: int, concluido: bool) -> bool:
        query = "UPDATE checklist_itens SET concluido = %s WHERE id = %s"
        return self.execute_query(query, (concluido, item_id)) > 0

    def checklist_excluir(self, item_id: int) -> bool:
        query = "DELETE FROM checklist_itens WHERE id = %s"
        return self.execute_query(query, (item_id,)) > 0

    # --- Arquivamento ---
    def arquivar_tarefas_antigas(self, usuario_id=None):
        try:
            self._verificar_colunas_arquivamento()
            if usuario_id:
                query = """
                    UPDATE tarefas
                    SET arquivado = TRUE
                    WHERE usuario_id = %s
                    AND fase = 'resolvido'
                    AND data_conclusao IS NOT NULL
                    AND data_conclusao <= CURRENT_TIMESTAMP - INTERVAL '10 days'
                    AND (arquivado IS NULL OR arquivado = FALSE)
                    RETURNING id
                """
                result = self.execute_query(query, (usuario_id,), fetch_all=True)
            else:
                query = """
                    UPDATE tarefas
                    SET arquivado = TRUE
                    WHERE fase = 'resolvido'
                    AND data_conclusao IS NOT NULL
                    AND data_conclusao <= CURRENT_TIMESTAMP - INTERVAL '10 days'
                    AND (arquivado IS NULL OR arquivado = FALSE)
                    RETURNING id
                """
                result = self.execute_query(query, fetch_all=True)
            qtde = len(result) if result else 0
            if qtde > 0:
                logger.info(f"{qtde} tarefas arquivadas automaticamente")
            return qtde
        except Exception as e:
            logger.error(f"Erro ao arquivar tarefas: {e}")
            return 0

    def _verificar_colunas_arquivamento(self):
        try:
            result = self.execute_query("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'tarefas' AND column_name = 'arquivado'
            """, fetch_all=True)
            if not result:
                self.execute_query(
                    "ALTER TABLE tarefas ADD COLUMN arquivado BOOLEAN DEFAULT FALSE"
                )
                logger.info("Coluna 'arquivado' adicionada")
            result = self.execute_query("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'tarefas' AND column_name = 'data_conclusao'
            """, fetch_all=True)
            if not result:
                self.execute_query(
                    "ALTER TABLE tarefas ADD COLUMN data_conclusao TIMESTAMP"
                )
                logger.info("Coluna 'data_conclusao' adicionada")
        except Exception as e:
            logger.error(f"Erro ao verificar colunas: {e}")

    def listar_nao_arquivadas(self, usuario_id: int) -> list:
        try:
            self._verificar_colunas_arquivamento()
            query = """
                SELECT id, titulo, descricao, status, data_criacao, fase,
                       data_vencimento, responsavel
                FROM tarefas
                WHERE usuario_id = %s
                AND (arquivado IS NULL OR arquivado = FALSE)
                ORDER BY
                    CASE status
                        WHEN 'pra_ja'       THEN 1
                        WHEN 'depois'       THEN 2
                        WHEN 'se_der_tempo' THEN 3
                        ELSE 4
                    END,
                    data_vencimento NULLS LAST,
                    data_criacao DESC
            """
            return self.execute_query(query, (usuario_id,), fetch_all=True) or []
        except Exception as e:
            logger.error(f"Erro ao listar tarefas não arquivadas: {e}")
            return self.listar_por_usuario(usuario_id)

    def listar_arquivadas(self, usuario_id: int) -> list:
        try:
            self._verificar_colunas_arquivamento()
            query = """
                SELECT id, titulo, descricao, status, data_criacao, fase,
                       data_vencimento, responsavel, data_conclusao
                FROM tarefas
                WHERE usuario_id = %s
                AND arquivado = TRUE
                ORDER BY data_conclusao DESC NULLS LAST
            """
            return self.execute_query(query, (usuario_id,), fetch_all=True) or []
        except Exception as e:
            logger.error(f"Erro ao listar tarefas arquivadas: {e}")
            return []

    def restaurar_do_arquivo(self, tarefa_id: int) -> bool:
        try:
            return self.execute_query(
                "UPDATE tarefas SET arquivado = FALSE WHERE id = %s",
                (tarefa_id,)
            ) > 0
        except Exception as e:
            logger.error(f"Erro ao restaurar tarefa {tarefa_id}: {e}")
            return False

    def excluir_permanentemente(self, tarefa_id: int) -> bool:
        try:
            result = self.execute_query(
                "SELECT arquivado FROM tarefas WHERE id = %s",
                (tarefa_id,),
                fetch_one=True,
            )
            if result and result[0]:
                return self.excluir(tarefa_id)
            return False
        except Exception as e:
            logger.error(f"Erro ao excluir permanentemente tarefa {tarefa_id}: {e}")
            return False

    def arquivar_manual(self, tarefa_id: int) -> bool:
        try:
            return self.execute_query(
                "UPDATE tarefas SET arquivado = TRUE WHERE id = %s",
                (tarefa_id,)
            ) > 0
        except Exception as e:
            logger.error(f"Erro ao arquivar manualmente tarefa {tarefa_id}: {e}")
            return False