import flet as ft
from datetime import datetime, timedelta
from tarefas_api_client import TarefaModel
from models.tarefa import FASES_DISPONIVEIS
from utils.tarefa_detalhe import criar_tarefa_detalhe_overlay
# Configuração de debug
DEBUG = True
def log_debug(msg):
    if DEBUG:
        print(f"🔍 [DEBUG] {msg}")
FASES_RESOLVIDAS = {"concluido", "finalizado", "aprovado", "validado", "resolvido"}
FASES_CONCLUIDAS = FASES_RESOLVIDAS
FASES_ARQUIVADAS = {"arquivado", "cancelado", "reprovado", "indeferido"}
def criar_arquivo_morto_view(page, AMARELO_BANANA, CINZA_FUNDO, CINZA_CARD, tarefa_model, user_id):
    """View separada listando todas as tarefas arquivadas."""
    log_debug("Abrindo Arquivo Morto")
    COR_BORDA = "#2A2A2A"
    lista = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    def carregar_arquivadas():
        log_debug("Carregando tarefas arquivadas")
        lista.controls.clear()
        tarefas = tarefa_model.listar_por_usuario(user_id)
        arquivadas = [t for t in tarefas if t[5] in FASES_ARQUIVADAS]
        log_debug(f"Encontradas {len(arquivadas)} tarefas arquivadas")
        if not arquivadas:
            lista.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color="#444444", size=48),
                        ft.Text("Nenhuma tarefa arquivada", color="#666666", size=14),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    alignment=ft.alignment.center,
                    expand=True,
                    padding=60,
                )
            )
            return
        for t in arquivadas:
            t_id    = t[0]
            titulo  = t[1]
            fase    = t[5] or ""
            venc    = t[6]
            resp    = t[7] or ""
            data_c  = t[4]
            data_str = data_c.strftime("%d/%m/%Y") if hasattr(data_c, "strftime") else str(data_c)
            venc_str = venc.strftime("%d/%m/%Y") if venc and hasattr(venc, "strftime") else "—"
            def ao_desarquivar(e, tid=t_id):
                log_debug(f"Desarquivando tarefa {tid}")
                tarefa_model.atualizar_fase(tid, "em_andamento")
                carregar_arquivadas()
                lista.update()
            def ao_excluir_arq(e, tid=t_id):
                log_debug(f"Excluindo permanentemente tarefa {tid}")
                tarefa_model.excluir(tid)
                carregar_arquivadas()
                lista.update()
            lista.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color="#666666", size=20),
                        ft.Column([
                            ft.Text(titulo, size=13, weight="bold", color="white"),
                            ft.Row([
                                ft.Text(fase.replace("_", " ").title(), size=10, color="#888888"),
                                ft.Text(f"Criado: {data_str}", size=10, color="#555555"),
                                ft.Text(f"Venc: {venc_str}", size=10, color="#555555"),
                            ], spacing=10),
                        ], expand=True, spacing=2),
                        ft.Tooltip(
                            message="Desarquivar",
                            content=ft.IconButton(
                                icon=ft.Icons.UNARCHIVE_OUTLINED,
                                icon_color=AMARELO_BANANA,
                                icon_size=18,
                                on_click=ao_desarquivar,
                            ),
                        ),
                        ft.Tooltip(
                            message="Excluir permanentemente",
                            content=ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color="#FF6B6B",
                                icon_size=18,
                                on_click=ao_excluir_arq,
                            ),
                        ),
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=CINZA_CARD,
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    border=ft.border.all(1, COR_BORDA),
                )
            )
    carregar_arquivadas()
    return ft.View(
        "/arquivo_morto",
        bgcolor=CINZA_FUNDO,
        padding=0,
        controls=[
            ft.AppBar(
                title=ft.Text("Arquivo Morto", color=CINZA_FUNDO, weight="bold"),
                bgcolor=AMARELO_BANANA,
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=CINZA_FUNDO,
                    on_click=lambda _: (page.views.pop(), page.update()),
                ),
            ),
            ft.Container(
                content=lista,
                padding=20,
                expand=True,
            ),
        ],
    )
def criar_dashboard(
    page: ft.Page,
    AMARELO_BANANA,
    CINZA_FUNDO,
    CINZA_CARD,
    user_model=None,
    on_nova_tarefa=None
):
    log_debug("Iniciando criação do dashboard")
    # ── Sessão ───────────────────────────────────────────────────────────────
    user_id   = page.session.get("user_id")
    user_name = page.session.get("user_name") or "Usuário"
    user_foto = page.session.get("user_foto")
    iniciais  = "".join([n[0] for n in user_name.split()[:2]]).upper()
    log_debug(f"Usuário: {user_name} (ID: {user_id})")
    hora     = datetime.now().hour
    saudacao = "Bom dia" if 5 <= hora < 12 else "Boa tarde" if 12 <= hora < 18 else "Boa noite"
    tarefa_model = TarefaModel()
    COR_PRA_JA = "#FF6B6B"
    COR_DEPOIS = AMARELO_BANANA
    COR_SE_DER = "#6BCB77"
    COR_BORDA  = "#2A2A2A"
    # ── Arquivamento automático ───────────────────────────────────────────────
    def arquivar_resolvidas_antigas():
        try:
            log_debug("Verificando tarefas para arquivar")
            tarefas = tarefa_model.listar_por_usuario(user_id)
            limite  = datetime.today().date() - timedelta(days=10)
            arquivadas = 0
            for t in tarefas:
                t_id = t[0]
                fase = t[5]
                if fase not in FASES_RESOLVIDAS:
                    continue
                try:
                    data_conclusao = t[8]
                except IndexError:
                    continue
                if not data_conclusao:
                    continue
                if hasattr(data_conclusao, "date"):
                    data_conclusao = data_conclusao.date()
                if data_conclusao <= limite:
                    tarefa_model.atualizar_fase(t_id, "arquivado")
                    arquivadas += 1
            if arquivadas > 0:
                log_debug(f"{arquivadas} tarefas arquivadas automaticamente")
        except Exception as ex:
            print(f"[arquivamento automático] {ex}")
    arquivar_resolvidas_antigas()
    # ── Stack principal ───────────────────────────────────────────────────────
    stack_principal = ft.Stack(expand=True)
    def fechar_overlay():
        log_debug("Fechando overlay")
        if len(stack_principal.controls) > 1:
            stack_principal.controls.pop()
            stack_principal.update()
        carregar_tudo()
    def ao_abrir_detalhe(tarefa_id: int):
        log_debug(f"Abrindo detalhe da tarefa {tarefa_id}")
        overlay = criar_tarefa_detalhe_overlay(
            page=page,
            tarefa_id=tarefa_id,
            AMARELO_BANANA=AMARELO_BANANA,
            CINZA_FUNDO=CINZA_FUNDO,
            CINZA_CARD=CINZA_CARD,
            tarefa_model=tarefa_model,
            on_fechar=fechar_overlay,
        )
        if not overlay:
            log_debug("Falha ao criar overlay")
            return
        if len(stack_principal.controls) > 1:
            stack_principal.controls.pop()
        stack_principal.controls.append(overlay)
        stack_principal.update()
        
    def ao_abrir_arquivo_morto(e):
        log_debug("Abrindo arquivo morto")
        # 👇 MUDE PARA USAR A VERSÃO DO UTILS
        from utils.arquivo_morto import criar_arquivo_morto
        view = criar_arquivo_morto(
            page,
            AMARELO_BANANA,
            CINZA_FUNDO,
            CINZA_CARD,
            tarefa_model=tarefa_model,
            user_id=user_id,
        )
        page.views.append(view)
        page.go("/arquivo_morto")
    # ── Saída ────────────────────────────────────────────────────────────────
    def ao_sair(e):
        log_debug("Usuário saiu")
        page.session.clear()
        page.views.clear()
        page.go("/")
        page.update()
    def vincular_click(e):
        log_debug("Vincular Telegram clicado")
        if hasattr(page, "on_vincular_telegram"):
            page.on_vincular_telegram(e)
    # ── Header ───────────────────────────────────────────────────────────────
    header = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Text(f"{saudacao},", size=12, color="#888888"),
                ft.Text(user_name, size=18, weight="bold", color="white"),
            ], spacing=0),
            ft.PopupMenuButton(
                content=ft.CircleAvatar(
                    foreground_image_src=user_foto,
                    content=ft.Text(iniciais, color="black", weight="bold"),
                    bgcolor=AMARELO_BANANA,
                    radius=20,
                ),
                items=[
                    ft.PopupMenuItem(icon=ft.Icons.PERSON, text="Perfil"),
                    ft.PopupMenuItem(
                        icon=ft.Icons.SEND_SHARP,
                        text="Vincular Telegram",
                        on_click=vincular_click,
                    ),
                    ft.PopupMenuItem(
                        icon=ft.Icons.INVENTORY_2_OUTLINED,
                        text="Arquivo Morto",
                        on_click=ao_abrir_arquivo_morto,
                    ),
                    ft.Divider(),
                    ft.PopupMenuItem(icon=ft.Icons.LOGOUT, text="Sair", on_click=ao_sair),
                ],
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.symmetric(horizontal=20, vertical=12),
    )
    # ── Cards informativos ────────────────────────────────────────────────────
    txt_total      = ft.Text("0", size=28, weight="bold", color=AMARELO_BANANA)
    txt_concluidas = ft.Text("0", size=28, weight="bold", color=COR_SE_DER)
    txt_arquivadas = ft.Text("0", size=28, weight="bold", color="#AAAAAA")
    txt_vencendo   = ft.Text("0", size=28, weight="bold", color=COR_PRA_JA)
    def _info_card(icone, cor_icone, titulo, valor_txt):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icone, color=cor_icone, size=18),
                    ft.Text(titulo, size=11, color="#888888"),
                ], spacing=6),
                valor_txt,
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.START),
            bgcolor=CINZA_CARD,
            border_radius=14,
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            border=ft.border.all(1, COR_BORDA),
            expand=True,
        )
    faixa_info = ft.Row([
        _info_card(ft.Icons.CHECKLIST_ROUNDED,    AMARELO_BANANA, "Total",      txt_total),
        _info_card(ft.Icons.CHECK_CIRCLE_OUTLINE,  COR_SE_DER,    "Concluídas", txt_concluidas),
        _info_card(ft.Icons.INVENTORY_2_OUTLINED,  "#AAAAAA",     "Arquivadas", txt_arquivadas),
        _info_card(ft.Icons.ALARM_OUTLINED,        COR_PRA_JA,    "Vencendo",   txt_vencendo),
    ], spacing=10, expand=True)
    def atualizar_cards_info(tarefas_todas):
        hoje = datetime.today().date()
        txt_total.value      = str(len(tarefas_todas))
        txt_concluidas.value = str(sum(1 for t in tarefas_todas if t.get("fase") in FASES_CONCLUIDAS))
        txt_arquivadas.value = str(sum(1 for t in tarefas_todas if t.get("fase") in FASES_ARQUIVADAS))
        txt_vencendo.value   = str(sum(
            1 for t in tarefas_todas
            if t.get("data_vencimento") and t["data_vencimento"] <= hoje
            and t.get("fase") not in FASES_CONCLUIDAS | FASES_ARQUIVADAS
        ))
    # ── BOTÃO DE NOVA TAREFA ───────────────────────────────────────────────────
    log_debug("Criando botão de nova tarefa")
    def abrir_modal_nova_tarefa(e):
        log_debug("📌 Botão + clicado!")

        # USA CALLBACK EXTERNO SE DISPONÍVEL
        if on_nova_tarefa is not None:
            log_debug("Usando função externa de nova tarefa")

            def apos_criar():
                log_debug("Callback externo - recarregando tarefas")
                carregar_tudo()
                page.update()

            on_nova_tarefa(
                page=page,
                AMARELO_BANANA=AMARELO_BANANA,
                CINZA_FUNDO=CINZA_FUNDO,
                CINZA_CARD=CINZA_CARD,
                user_id=user_id,
                tarefa_model=tarefa_model,
                on_criada=apos_criar
            )
            return

        # CÓDIGO ORIGINAL (FALLBACK)
        log_debug("Usando função interna de nova tarefa (fallback)")

        page.show_snack_bar(
            ft.SnackBar(content=ft.Text("Abrindo formulário..."), bgcolor=ft.colors.BLUE_700, duration=1000)
        )

        campo_titulo = ft.TextField(
            label="Título da tarefa",
            border_color=AMARELO_BANANA,
            focused_border_color=AMARELO_BANANA,
            cursor_color=AMARELO_BANANA,
            color="white",
            border_radius=12,
            autofocus=True,
        )
        dropdown_status_modal = ft.Dropdown(
            label="Status",
            value="pra_ja",
            border_color=AMARELO_BANANA,
            focused_border_color=AMARELO_BANANA,
            color="white",
            bgcolor=CINZA_CARD,
            border_radius=12,
            options=[
                ft.dropdown.Option(key="pra_ja", text="🔴 Pra Já"),
                ft.dropdown.Option(key="depois", text="🟡 Depois"),
                ft.dropdown.Option(key="se_der_tempo", text="🟢 Se Der Tempo"),
            ],
        )
        def criar_tarefa_modal(e):
            titulo = campo_titulo.value.strip()
            if not titulo:
                campo_titulo.error_text = "Digite um título"
                campo_titulo.update()
                return

            status = dropdown_status_modal.value or "pra_ja"

            if not user_id:
                page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Usuário não identificado"), bgcolor=ft.colors.RED_700)
                )
                return

            try:
                try:
                    tarefa_model.criar(user_id, titulo, None, status)
                except TypeError:
                    try:
                        tarefa_model.criar(user_id, titulo, status)
                    except TypeError:
                        tarefa_model.criar(user_id, titulo)

                page.close(modal)
                page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Tarefa criada!"), bgcolor=ft.colors.GREEN_700, duration=1500)
                )
                carregar_tudo()

            except Exception as ex:
                page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(f"Erro: {str(ex)[:50]}"), bgcolor=ft.colors.RED_700)
                )
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nova Tarefa", color=AMARELO_BANANA, weight="bold"),
            content=ft.Container(
                width=300,
                content=ft.Column([
                    campo_titulo,
                    dropdown_status_modal,
                ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.close(modal)),
                ft.ElevatedButton(
                    "Criar",
                    bgcolor=AMARELO_BANANA,
                    color=CINZA_FUNDO,
                    on_click=criar_tarefa_modal,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=CINZA_CARD,
        )
        page.open(modal)
    # Botão de adicionar
    btn_add = ft.IconButton(
        icon=ft.Icons.ADD_CIRCLE_ROUNDED,
        icon_color=AMARELO_BANANA,
        icon_size=36,
        tooltip="Adicionar tarefa",
        on_click=abrir_modal_nova_tarefa,
    )
    barra_nova = ft.Row([btn_add], alignment=ft.MainAxisAlignment.END)
    # ── Kanban ───────────────────────────────────────────────────────────────
    col_pra_ja = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    col_depois = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    col_se_der = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    # Guarda o tarefa_id real durante o arraste (o Flet 0.25.2 não passa
    # o campo 'data' do Draggable no evento on_accept)
    _drag_id_atual = [None]

    def _fase_label(fase: str) -> str:
        for label, valor in FASES_DISPONIVEIS:
            if valor == fase:
                return label
        return ""
    def _vencimento_chip(data_venc):
        if not data_venc:
            return None
        hoje  = datetime.today().date()
        diff  = (data_venc - hoje).days
        texto = data_venc.strftime("%d/%m")
        if diff < 0:
            cor, icone = COR_PRA_JA, ft.Icons.ALARM_OFF_OUTLINED
        elif diff <= 3:
            cor, icone = "#FFA94D", ft.Icons.ALARM_OUTLINED
        else:
            cor, icone = "#6BCB77", ft.Icons.CALENDAR_TODAY_OUTLINED
        return ft.Row([
            ft.Icon(icone, color=cor, size=11),
            ft.Text(texto, size=10, color=cor),
        ], spacing=3)
    def _icone_fase(fase: str):
        if fase in FASES_RESOLVIDAS:
            return ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=COR_SE_DER, size=12)
        if fase in FASES_ARQUIVADAS:
            return ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color="#888888", size=12)
        if fase in {"aguardando", "aguardando_aprovacao", "aguardando_retorno",
                    "parado", "em_pausa", "pendente", "travado"}:
            return ft.Icon(ft.Icons.PAUSE_CIRCLE_OUTLINE, color="#FFA94D", size=12)
        return ft.Icon(ft.Icons.AUTORENEW, color=AMARELO_BANANA, size=12)
    def montar_card(tarefa: dict) -> ft.Draggable:
        t_id       = tarefa["id"]
        titulo     = tarefa["titulo"]
        fase       = tarefa.get("fase") or "em_andamento"
        fase_lb    = _fase_label(fase)
        chip_venc  = _vencimento_chip(tarefa.get("data_vencimento"))
        icone_fase = _icone_fase(fase)
        resp       = tarefa.get("responsavel") or ""
        def ao_excluir(e):
            log_debug(f"Excluindo tarefa {t_id}")
            tarefa_model.excluir(t_id)
            carregar_tudo()
        def ao_clicar_card(e):
            ao_abrir_detalhe(t_id)
        def ao_iniciar_drag(e):
            log_debug(f"Iniciando drag da tarefa {t_id}")
            _drag_id_atual[0] = t_id
        rodape_itens = [
            ft.Row([icone_fase, ft.Text(fase_lb, size=10, color="#AAAAAA")], spacing=3)
        ]
        if chip_venc:
            rodape_itens.append(chip_venc)
        if resp:
            rodape_itens.append(ft.Row([
                ft.Icon(ft.Icons.PERSON_OUTLINE, size=11, color="#666666"),
                ft.Text(resp[:15], size=10, color="#666666"),
            ], spacing=2))
        card_visual = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(titulo, size=13, weight="bold", color="white", expand=True),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color="#444444",
                        icon_size=14,
                        tooltip="Excluir",
                        on_click=ao_excluir,
                    ),
                ], spacing=0),
                ft.Row(rodape_itens, spacing=6, wrap=True),
            ], spacing=6),
            bgcolor=CINZA_CARD,
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            border=ft.border.all(1, COR_BORDA),
        )
        gd = ft.GestureDetector(
            content=card_visual,
            on_tap=ao_clicar_card,
        )
        return ft.Draggable(
            group="tarefas",
            data=str(t_id),
            content=gd,
            on_drag_start=ao_iniciar_drag,
            content_when_dragging=ft.Container(
                height=50,
                border_radius=12,
                bgcolor=f"{CINZA_CARD}66",
                border=ft.border.all(1, f"{AMARELO_BANANA}44"),
            ),
        )
    def _zona_drop(titulo, cor, coluna_alvo, status_key):
        def on_accept(e):
            tarefa_id = _drag_id_atual[0]
            if tarefa_id is None:
                log_debug("on_accept: _drag_id_atual é None, ignorando")
                return
            log_debug(f"Drag and drop: tarefa {tarefa_id} para {status_key}")
            resultado = tarefa_model.atualizar_status(tarefa_id, status_key)
            log_debug(f"atualizar_status retornou: {resultado}")
            _drag_id_atual[0] = None
            carregar_tudo()
        return ft.DragTarget(
            group="tarefas",
            on_accept=on_accept,
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(width=4, height=20, bgcolor=cor, border_radius=2),
                        ft.Text(titulo, size=14, weight="bold", color=cor),
                    ], spacing=8),
                    ft.Divider(height=1, color=COR_BORDA),
                    ft.Container(
                        content=coluna_alvo,
                        expand=True,
                    ),
                ], spacing=10, expand=True),
                bgcolor="#181818",
                padding=16,
                border_radius=16,
                border=ft.border.all(1, COR_BORDA),
                expand=True,
            ),
        )
    zona_pra_ja = _zona_drop("Pra Já",       COR_PRA_JA, col_pra_ja, "pra_ja")
    zona_depois = _zona_drop("Depois",       COR_DEPOIS, col_depois, "depois")
    zona_se_der = _zona_drop("Se Der Tempo", COR_SE_DER, col_se_der, "se_der_tempo")
    def _wrap(z):
        return ft.Container(content=z, expand=True)
    kanban = ft.Row(
        [_wrap(zona_pra_ja), _wrap(zona_depois), _wrap(zona_se_der)],
        spacing=12,
        expand=True,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
    )
    # ── Carregar tudo ─────────────────────────────────────────────────────────
    def carregar_tudo():
        log_debug("Carregando tarefas")
        try:
            tarefas = tarefa_model.listar_por_usuario(user_id)
            log_debug(f"Total de tarefas: {len(tarefas)}")
        except Exception as ex:
            log_debug(f"Erro ao listar tarefas: {ex}")
            tarefas = []
        col_pra_ja.controls.clear()
        col_depois.controls.clear()
        col_se_der.controls.clear()
        tarefas_todas = []
        tarefas_kanban = []
        for t in tarefas:
            d = {
                "id":              t[0],
                "titulo":          t[1],
                "descricao":       t[2],
                "status":          t[3],
                "data_criacao":    t[4],
                "fase":            t[5],
                "data_vencimento": t[6],
                "responsavel":     t[7],
            }
            tarefas_todas.append(d)
            if d["fase"] not in FASES_ARQUIVADAS:
                tarefas_kanban.append(d)
        log_debug(f"Tarefas no kanban: {len(tarefas_kanban)}")
        for d in tarefas_kanban:
            draggable = montar_card(d)
            if d["status"] == "pra_ja":
                col_pra_ja.controls.append(draggable)
            elif d["status"] == "depois":
                col_depois.controls.append(draggable)
            else:
                col_se_der.controls.append(draggable)
        atualizar_cards_info(tarefas_todas)
        page.update()
    carregar_tudo()
    # ── Rodapé ────────────────────────────────────────────────────────────────
    try:
        from utils.rodape import criar_rodape
        rodape = criar_rodape(CINZA_CARD)
    except Exception:
        rodape = ft.Container(
            content=ft.Text("© Tem Tarefas?", size=11, color="#555555"),
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(vertical=8),
        )
    # ── Layout final ─────────────────────────────────────────────────────────
    conteudo = ft.Column([
        header,
        ft.Container(content=faixa_info, padding=ft.padding.symmetric(horizontal=20)),
        ft.Container(height=12),
        ft.Container(content=barra_nova, padding=ft.padding.symmetric(horizontal=20)),
        ft.Container(height=8),
        ft.Container(
            content=kanban,
            padding=ft.padding.symmetric(horizontal=20),
            expand=True,
        ),
        ft.Container(content=rodape, padding=ft.padding.symmetric(horizontal=20)),
    ], expand=True, spacing=0)
    stack_principal.controls.append(conteudo)
    log_debug("Dashboard criado com sucesso")
    return ft.View(
        "/dashboard",
        bgcolor=CINZA_FUNDO,
        padding=0,
        controls=[stack_principal],
    )