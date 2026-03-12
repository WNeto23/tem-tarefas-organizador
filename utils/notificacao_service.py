import logging
from datetime import datetime, date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class NotificacaoService:
    def __init__(self, tarefa_model, usuario_model, bot_telegram):
        self.tarefa_model  = tarefa_model
        self.usuario_model = usuario_model
        self.bot           = bot_telegram
        self.scheduler     = BackgroundScheduler(timezone="America/Sao_Paulo")
        self._configurar_jobs()

    def _configurar_jobs(self):
        # Resumo diário — todo dia às 08:00
        self.scheduler.add_job(
            self._resumo_diario,
            CronTrigger(hour=8, minute=0),
            id="resumo_diario",
            replace_existing=True,
        )

        # Verificação de vencimentos — a cada 2 horas
        self.scheduler.add_job(
            self._verificar_vencimentos,
            CronTrigger(minute=0, hour="*/2"),
            id="verificar_vencimentos",
            replace_existing=True,
        )

    def iniciar(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("NotificacaoService iniciado.")

    def parar(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("NotificacaoService encerrado.")

    # ------------------------------------------------------------------ #
    # RESUMO DIÁRIO                                                        #
    # ------------------------------------------------------------------ #
    def _resumo_diario(self):
        try:
            usuarios = self.usuario_model.listar_usuarios_com_telegram()
            logger.info(f"Encontrados {len(usuarios)} usuários com Telegram")
            
            for usuario in usuarios:
                user_id    = usuario.get("id") or usuario.get("user_id")
                nome       = usuario.get("nome_completo") or usuario.get("nome")
                chat_id    = usuario.get("telegram_chat_id")
                
                if not chat_id:
                    continue
                    
                self._enviar_resumo(user_id, nome, chat_id)
        except Exception as e:
            logger.error(f"Erro no resumo diário: {e}")

    def _enviar_resumo(self, user_id: int, nome: str, chat_id: str):
        try:
            tarefas = self.tarefa_model.listar_nao_arquivadas(user_id)
            if not tarefas:
                return

            hoje    = date.today()
            urgente = []   # atrasadas ou vencem hoje
            proximas = []  # vencem em até 3 dias
            sem_prazo_pra_ja = []  # pra_já sem data

            for t in tarefas:
                # Adapta para o formato retornado pela API
                if isinstance(t, dict):
                    tid = t.get("id")
                    titulo = t.get("titulo")
                    status = t.get("status")
                    fase = t.get("fase") or t.get("status")
                    data_venc = t.get("data_vencimento") or t.get("prazo")
                else:  # Se for tupla (formato antigo)
                    tid, titulo, _, status, _, fase, data_venc, _ = t

                if fase in ["resolvido", "cancelado", "concluida"]:
                    continue

                if data_venc:
                    # Converte string para date se necessário
                    if isinstance(data_venc, str):
                        data_venc = date.fromisoformat(data_venc)
                    
                    dias = (data_venc - hoje).days
                    if dias < 0:
                        urgente.append((titulo, status, dias, "⚠️ ATRASADA"))
                    elif dias == 0:
                        urgente.append((titulo, status, dias, "🔴 VENCE HOJE"))
                    elif dias <= 3:
                        proximas.append((titulo, status, dias, f"🟡 {dias}d"))
                elif status == "pra_ja":
                    sem_prazo_pra_ja.append((titulo, status))

            if not urgente and not proximas and not sem_prazo_pra_ja:
                return

            # Monta a mensagem
            agora = datetime.now().strftime("%H:%M")
            linhas = [
                f"📋 *RESUMO DIÁRIO — {hoje.strftime('%d/%m/%Y')}*",
                f"`{'─' * 30}`",
                f"",
                f"Olá *{nome}*! Aqui está seu resumo de tarefas:",
                f"",
            ]

            if urgente:
                linhas.append("🚨 *URGENTE / ATRASADAS:*")
                for titulo, status, dias, label in urgente:
                    status_emoji = self._emoji_status(status)
                    linhas.append(f"  {label} › {status_emoji} {titulo}")
                linhas.append("")

            if proximas:
                linhas.append("⏰ *VENCEM EM BREVE:*")
                for titulo, status, dias, label in proximas:
                    status_emoji = self._emoji_status(status)
                    linhas.append(f"  {label} › {status_emoji} {titulo}")
                linhas.append("")

            if sem_prazo_pra_ja:
                linhas.append("🔥 *PRA JÁ SEM PRAZO:*")
                for titulo, status in sem_prazo_pra_ja:
                    linhas.append(f"  • {titulo}")
                linhas.append("")

            total_urgente = len(urgente)
            total_proximas = len(proximas)
            linhas.append(f"`{'─' * 30}`")
            linhas.append(
                f"📊 {total_urgente} urgente(s) · {total_proximas} chegando · "
                f"{len(sem_prazo_pra_ja)} pra já sem prazo"
            )
            linhas.append(f"🕒 Gerado às {agora}")

            self.bot.enviar_mensagem(chat_id, "\n".join(linhas))

        except Exception as e:
            logger.error(f"Erro ao enviar resumo para user_id {user_id}: {e}")

    # ------------------------------------------------------------------ #
    # VERIFICAÇÃO DE VENCIMENTOS                                           #
    # ------------------------------------------------------------------ #
    def _verificar_vencimentos(self):
        try:
            usuarios = self.usuario_model.listar_usuarios_com_telegram()
            for usuario in usuarios:
                user_id = usuario.get("id") or usuario.get("user_id")
                chat_id = usuario.get("telegram_chat_id")
                nome    = usuario.get("nome_completo") or usuario.get("nome")
                
                if not chat_id:
                    continue
                    
                self._checar_vencimentos_usuario(user_id, nome, chat_id)
        except Exception as e:
            logger.error(f"Erro na verificação de vencimentos: {e}")

    def _checar_vencimentos_usuario(self, user_id: int, nome: str, chat_id: str):
        try:
            tarefas = self.tarefa_model.listar_nao_arquivadas(user_id)
            hoje    = date.today()
            amanha  = hoje + timedelta(days=1)
            alertas = []

            for t in tarefas:
                if isinstance(t, dict):
                    tid = t.get("id")
                    titulo = t.get("titulo")
                    status = t.get("status")
                    fase = t.get("fase") or t.get("status")
                    data_venc = t.get("data_vencimento") or t.get("prazo")
                else:
                    tid, titulo, _, status, _, fase, data_venc, _ = t

                if not data_venc:
                    continue
                if fase in ("resolvido", "cancelado", "concluida"):
                    continue

                if isinstance(data_venc, str):
                    data_venc = date.fromisoformat(data_venc)

                dias = (data_venc - hoje).days

                # Alerta só para: atrasadas, vencem hoje ou amanhã
                if dias < 0:
                    alertas.append((titulo, status, f"⚠️ ATRASADA há {abs(dias)}d", "urgente"))
                elif dias == 0:
                    alertas.append((titulo, status, "🔴 VENCE HOJE", "urgente"))
                elif dias == 1:
                    alertas.append((titulo, status, "🟡 VENCE AMANHÃ", "aviso"))

            if not alertas:
                return

            # Só envia se tiver algo urgente para não ser spam
            tem_urgente = any(p == "urgente" for _, _, _, p in alertas)
            if not tem_urgente:
                return

            agora  = datetime.now().strftime("%H:%M")
            linhas = [
                f"⏰ *ALERTA DE VENCIMENTO*",
                f"`{'─' * 30}`",
                f"",
            ]

            for titulo, status, label, _ in alertas:
                status_emoji = self._emoji_status(status)
                linhas.append(f"{label}")
                linhas.append(f"  {status_emoji} _{titulo}_")
                linhas.append("")

            linhas.append(f"`{'─' * 30}`")
            linhas.append(f"🕒 {agora} · Acesse o app para atualizar")

            self.bot.enviar_mensagem(chat_id, "\n".join(linhas))

        except Exception as e:
            logger.error(f"Erro ao checar vencimentos para user_id {user_id}: {e}")

    # ------------------------------------------------------------------ #
    # HELPERS                                                              #
    # ------------------------------------------------------------------ #
    def _emoji_status(self, status: str) -> str:
        return {
            "pra_ja":       "🔥",
            "depois":       "📋",
            "se_der_tempo": "🕐",
            "pendente":     "⏳",
            "em_andamento": "🔄",
            "concluida":    "✅",
        }.get(status, "•")