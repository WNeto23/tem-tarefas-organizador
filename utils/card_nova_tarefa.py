import flet as ft


def abrir_modal_nova_tarefa(
    page: ft.Page,
    AMARELO_BANANA: str,
    CINZA_FUNDO: str,
    CINZA_CARD: str,
    user_id: int,
    tarefa_model,
    on_criada,
):
    """
    Abre o modal de nova tarefa.
    on_criada: callback chamado após tarefa criada com sucesso (ex: carregar_tudo).
    """

    campo_titulo = ft.TextField(
        label="Título da tarefa",
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        color="white",
        border_radius=12,
        autofocus=True,
    )

    dropdown_status = ft.Dropdown(
        label="Status",
        value="pra_ja",
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        color="white",
        bgcolor=CINZA_CARD,
        border_radius=12,
        options=[
            ft.dropdown.Option(key="pra_ja",        text="🔴 Pra Já"),
            ft.dropdown.Option(key="depois",        text="🟡 Depois"),
            ft.dropdown.Option(key="se_der_tempo",  text="🟢 Se Der Tempo"),
        ],
    )

    def criar(e):
        titulo = (campo_titulo.value or "").strip()
        if not titulo:
            campo_titulo.error_text = "Digite um título"
            campo_titulo.update()
            return

        status = dropdown_status.value or "pra_ja"

        try:
            try:
                tarefa_model.criar(user_id, titulo, None, status)
            except TypeError:
                try:
                    tarefa_model.criar(user_id, titulo, status)
                except TypeError:
                    tarefa_model.criar(user_id, titulo)

            page.close(dlg)
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Tarefa criada!"),
                    bgcolor=ft.Colors.GREEN_700,
                    duration=1500,
                )
            )
            on_criada()

        except Exception as ex:
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro: {str(ex)[:60]}"),
                    bgcolor=ft.Colors.RED_700,
                )
            )

    # ✅ VERSÃO CORRIGIDA - sem Container extra, com tight=True
    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=CINZA_CARD,
        title=ft.Text("Nova Tarefa", color=AMARELO_BANANA, weight="bold"),
        content=ft.Column(
            controls=[campo_titulo, dropdown_status],
            spacing=14,
            tight=True,  # 👈 IMPEDE EXPANSÃO DESNECESSÁRIA
            width=340,   # 👈 LARGURA FIXA
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: page.close(dlg)),
            ft.ElevatedButton(
                "Criar",
                bgcolor=AMARELO_BANANA,
                color=CINZA_FUNDO,
                on_click=criar,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.open(dlg)