import flet as ft
from datetime import datetime
from models.tarefa import FASES_DISPONIVEIS


def criar_tarefa_detalhe_overlay(
    page: ft.Page,
    tarefa_id: int,
    AMARELO_BANANA,
    CINZA_FUNDO,
    CINZA_CARD,
    tarefa_model,
    on_fechar,
):
    dados = tarefa_model.buscar_por_id(tarefa_id)
    if not dados:
        on_fechar()
        return None

    def mostrar_snack(texto, cor):
        snack = ft.SnackBar(content=ft.Text(texto, color="white"), bgcolor=cor)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # ── Campos ────────────────────────────────────────────────────────────────
    campo_titulo = ft.TextField(
        value=dados["titulo"],
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        color="white",
        text_size=20,
        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
        border_radius=10,
    )

    campo_descricao = ft.TextField(
        label="Descrição",
        value=dados.get("descricao_longa") or "",
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        color="white",
        border_radius=10,
        multiline=True,
        min_lines=3,
        max_lines=6,
    )

    campo_responsavel = ft.TextField(
        label="Responsável",
        value=dados.get("responsavel") or "",
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        color="white",
        border_radius=10,
        prefix_icon=ft.Icons.PERSON_OUTLINE,
    )

    # ── Date Picker nativo ────────────────────────────────────────────────────
    _data = [dados.get("data_vencimento")]  # lista para mutabilidade em closure

    txt_data = ft.Text(
        _data[0].strftime("%d/%m/%Y") if _data[0] else "Sem data",
        size=14,
        color="white" if _data[0] else "#666666",
    )

    def ao_escolher_data(e):
        val = e.control.value  # Flet 0.25.2: e.control.value, não e.value
        if val:
            _data[0] = val.date() if hasattr(val, "date") else val
            txt_data.value = _data[0].strftime("%d/%m/%Y")
            txt_data.color = "white"
        else:
            _data[0] = None
            txt_data.value = "Sem data"
            txt_data.color = "#666666"
        txt_data.update()

    date_picker = ft.DatePicker(
        on_change=ao_escolher_data,
        first_date=datetime(2020, 1, 1),
        last_date=datetime(2030, 12, 31),
        value=datetime.combine(_data[0], datetime.min.time()) if _data[0] else None,
    )
    # Flet 0.25.2: precisa de page.update() após adicionar ao overlay
    if date_picker not in page.overlay:
        page.overlay.append(date_picker)
        page.update()

    linha_vencimento = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.CALENDAR_TODAY, color=AMARELO_BANANA, size=16),
            txt_data,
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.CLEAR,
                icon_color="#555555",
                icon_size=16,
                tooltip="Limpar data",
                on_click=lambda _: (
                    setattr(txt_data, "value", "Sem data"),
                    setattr(txt_data, "color", "#666666"),
                    txt_data.update(),
                    _data.__setitem__(0, None),
                ),
            ),
            ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                icon_color=AMARELO_BANANA,
                icon_size=16,
                tooltip="Abrir calendário",
                on_click=lambda _: date_picker.pick_date(),
            ),
        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="#1A1A1A",
        border_radius=10,
        padding=ft.padding.symmetric(horizontal=10, vertical=6),
        border=ft.border.all(1, f"{AMARELO_BANANA}55"),
    )

    campo_comentarios = ft.TextField(
        label="Comentários / Observações",
        value=dados.get("comentarios") or "",
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        color="white",
        border_radius=10,
        multiline=True,
        min_lines=2,
        max_lines=5,
        prefix_icon=ft.Icons.COMMENT_OUTLINED,
    )

    # ── Dropdown de fase ──────────────────────────────────────────────────────
    dropdown_fase = ft.Dropdown(
        value=dados.get("fase") or "em_andamento",
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        color="white",
        bgcolor=CINZA_CARD,
        border_radius=10,
        options=[
            ft.dropdown.Option(key=valor, text=label)
            for label, valor in FASES_DISPONIVEIS
        ],
        on_change=lambda e: tarefa_model.atualizar_fase(tarefa_id, e.control.value),
    )

    # ── Checklist ─────────────────────────────────────────────────────────────
    progresso_barra = ft.ProgressBar(
        value=0, bgcolor="#333333", color=AMARELO_BANANA, height=6, border_radius=3,
    )
    progresso_texto = ft.Text("0/0", size=12, color=AMARELO_BANANA)
    coluna_checklist = ft.Column(spacing=6)

    def atualizar_progresso(atualizar_tela: bool = False):
        itens = tarefa_model.checklist_listar(tarefa_id)
        total = len(itens)
        concluidos = sum(1 for _, _, c in itens if c)
        progresso_barra.value = concluidos / total if total > 0 else 0
        progresso_texto.value = f"{concluidos}/{total}"
        if atualizar_tela:
            progresso_barra.update()
            progresso_texto.update()

    def montar_item_checklist(item_id, texto, concluido):
        def ao_marcar(e):
            tarefa_model.checklist_marcar(item_id, e.control.value)
            atualizar_progresso(atualizar_tela=True)
        def ao_excluir_item(e):
            tarefa_model.checklist_excluir(item_id)
            carregar_checklist()
            atualizar_progresso(atualizar_tela=True)
            coluna_checklist.update()
        return ft.Row([
            ft.Checkbox(value=concluido, fill_color=AMARELO_BANANA, check_color="black", on_change=ao_marcar),
            ft.Text(texto, expand=True, color="white" if not concluido else "#AAAAAA", size=13,
                    style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH if concluido else None)),
            ft.IconButton(icon=ft.Icons.CLOSE, icon_color="#555555", icon_size=14, on_click=ao_excluir_item),
        ], spacing=4)

    def carregar_checklist():
        coluna_checklist.controls.clear()
        for item_id, texto, concluido in tarefa_model.checklist_listar(tarefa_id):
            coluna_checklist.controls.append(montar_item_checklist(item_id, texto, concluido))
        atualizar_progresso()

    carregar_checklist()

    campo_novo_item = ft.TextField(
        label="Novo item do checklist",
        border_color=AMARELO_BANANA, focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA, color="white", border_radius=10, expand=True,
    )

    def ao_adicionar_item(e):
        texto = campo_novo_item.value.strip()
        if not texto:
            return
        tarefa_model.checklist_adicionar(tarefa_id, texto)
        campo_novo_item.value = ""
        campo_novo_item.update()
        carregar_checklist()
        atualizar_progresso(atualizar_tela=True)
        coluna_checklist.update()

    campo_novo_item.on_submit = ao_adicionar_item

    # ── Botão Salvar ──────────────────────────────────────────────────────────
    btn_salvar = ft.ElevatedButton(
        text="SALVAR",
        bgcolor=AMARELO_BANANA,
        color=CINZA_FUNDO,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
        ),
        width=200,
        height=45,
    )

    def ao_salvar(e):
        btn_salvar.disabled = True
        btn_salvar.text = "Salvando..."
        btn_salvar.update()
        try:
            tarefa_model.atualizar_detalhes(
                tarefa_id=tarefa_id,
                titulo=campo_titulo.value.strip(),
                descricao_longa=campo_descricao.value.strip(),
                fase=dropdown_fase.value,
                data_vencimento=_data[0],
                responsavel=campo_responsavel.value.strip(),
                comentarios=campo_comentarios.value.strip(),
            )
            mostrar_snack("Tarefa salva!", ft.Colors.GREEN_700)
            on_fechar()
        except Exception as ex:
            mostrar_snack(f"Erro ao salvar: {ex}", ft.Colors.RED_900)
            btn_salvar.disabled = False
            btn_salvar.text = "SALVAR"
            btn_salvar.update()

    btn_salvar.on_click = ao_salvar

    # ── Layout ────────────────────────────────────────────────────────────────
    # SOLUÇÃO: Salvar fica FORA do scroll, pregado no rodapé do card.
    # Column externa (expand=True) tem 3 seções:
    #   1. Cabeçalho fixo
    #   2. Área scroll (expand=True) — cresce até ocupar o espaço disponível
    #   3. Rodapé fixo com botão Salvar

    area_scroll = ft.Column(
        [
            campo_titulo,
            ft.Divider(height=8, color="#333333"),
            ft.Text("Fase", size=12, color="#888888", weight="bold"),
            dropdown_fase,
            ft.Divider(height=8, color="#333333"),
            ft.Text("Descrição", size=12, color="#888888", weight="bold"),
            campo_descricao,
            ft.Divider(height=8, color="#333333"),
            ft.Row([
                ft.Column([
                    ft.Text("Responsável", size=12, color="#888888", weight="bold"),
                    campo_responsavel,
                ], expand=True, spacing=4),
                ft.Column([
                    ft.Text("Vencimento", size=12, color="#888888", weight="bold"),
                    linha_vencimento,
                ], expand=True, spacing=4),
            ], spacing=12),
            ft.Divider(height=8, color="#333333"),
            ft.Row([
                ft.Text("Checklist", size=12, color="#888888", weight="bold"),
                progresso_texto,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            progresso_barra,
            coluna_checklist,
            ft.Row([
                campo_novo_item,
                ft.IconButton(
                    icon=ft.Icons.ADD_CIRCLE,
                    icon_color=AMARELO_BANANA,
                    tooltip="Adicionar item",
                    on_click=ao_adicionar_item,
                ),
            ]),
            ft.Divider(height=8, color="#333333"),
            ft.Text("Comentários", size=12, color="#888888", weight="bold"),
            campo_comentarios,
        ],
        spacing=12,
        scroll=ft.ScrollMode.ALWAYS,
        expand=True,
    )

    conteudo_modal = ft.Column(
        [
            # 1. Cabeçalho fixo
            ft.Row([
                ft.Text("Detalhes da Tarefa", size=16, weight="bold", color=AMARELO_BANANA),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color="#AAAAAA",
                    tooltip="Fechar",
                    on_click=lambda _: on_fechar(),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=1, color="#333333"),
            # 2. Scroll (cresce para preencher)
            area_scroll,
            # 3. Rodapé fixo — sempre visível, nunca entra no scroll
            ft.Divider(height=1, color="#333333"),
            ft.Container(
                content=ft.Row([btn_salvar], alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.symmetric(vertical=10),
            ),
        ],
        spacing=8,
        expand=True,
    )

    card_modal = ft.Container(
        content=conteudo_modal,
        bgcolor=CINZA_CARD,
        border_radius=20,
        padding=25,
        border=ft.border.all(1, f"{AMARELO_BANANA}33"),
        width=680,
        height=700,
        shadow=ft.BoxShadow(blur_radius=40, color="#000000AA", offset=ft.Offset(0, 8)),
        on_click=lambda e: None,
    )

    overlay = ft.Stack(
        [
            ft.Container(bgcolor="#000000CC", expand=True, on_click=lambda _: on_fechar()),
            ft.Container(content=card_modal, alignment=ft.alignment.center, expand=True),
        ],
        expand=True,
    )

    return overlay