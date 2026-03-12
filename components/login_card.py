import flet as ft


def criar_login_card(
    AMARELO_BANANA,
    CINZA_FUNDO,
    CINZA_CARD,
    on_login,
    on_ir_para_cadastro,
    on_ir_esqueci,
):
    usuario_input = ft.TextField(
        label="Usuário",
        border_color=AMARELO_BANANA,
        border_radius=15,
        prefix_icon=ft.Icons.PERSON_ROUNDED,
        cursor_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        color="white",
        on_submit=lambda e: senha_input.focus(),
    )

    senha_input = ft.TextField(
        label="Senha",
        password=True,
        can_reveal_password=True,
        border_color=AMARELO_BANANA,
        border_radius=15,
        prefix_icon=ft.Icons.LOCK_CLOCK_OUTLINED,
        cursor_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        color="white",
        on_submit=lambda e: ao_clicar_login(e),
    )

    lembrar_me = ft.Checkbox(
        label="Lembrar de mim",
        fill_color=AMARELO_BANANA,
        label_style=ft.TextStyle(size=12, color=ft.Colors.GREEN_400),
    )

    btn_entrar = ft.ElevatedButton(
        text="ENTRAR AGORA",
        width=400,
        height=50,
        bgcolor=AMARELO_BANANA,
        color=CINZA_FUNDO,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=15),
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
        ),
    )

    def ao_clicar_login(e):
        btn_entrar.disabled = True
        btn_entrar.text     = "Entrando..."
        btn_entrar.update()

        try:
            on_login(e, usuario_input, senha_input, container)
        finally:
            # CORREÇÃO: reativa o botão sempre que o handler terminar
            # (seja por sucesso, erro ou navegação)
            # O asyncio do realizar_login pode ter ido para outra view,
            # mas se ainda estiver aqui, o botão volta ao normal
            try:
                btn_entrar.disabled = False
                btn_entrar.text     = "ENTRAR AGORA"
                btn_entrar.update()
            except Exception:
                pass  # ignora se a view já foi destruída

    btn_entrar.on_click = ao_clicar_login

    links_ajuda = ft.Row(
        [
            ft.TextButton(
                "Esqueci meu acesso",
                on_click=on_ir_esqueci,
                style=ft.ButtonStyle(
                    color=ft.Colors.GREEN_500,
                    text_style=ft.TextStyle(size=11),
                ),
            ),
            ft.TextButton(
                "Criar conta",
                on_click=on_ir_para_cadastro,
                style=ft.ButtonStyle(
                    color=AMARELO_BANANA,
                    text_style=ft.TextStyle(size=11),
                ),
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    container = ft.Container(
        content=ft.Column(
            [
                ft.Icon(
                    name=ft.Icons.CHECK_CIRCLE_ROUNDED,
                    color=AMARELO_BANANA,
                    size=80,
                ),
                ft.Text("Tem Tarefas?", size=36, weight="bold", color=AMARELO_BANANA),
                ft.Text(
                    "Organize o seu dia, do seu jeito.",
                    color=ft.Colors.GREEN_400,
                ),
                ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                usuario_input,
                senha_input,
                ft.Row([lembrar_me], alignment=ft.MainAxisAlignment.START),
                links_ajuda,
                btn_entrar,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        ),
        width=380,
        border=ft.border.all(1, f"{AMARELO_BANANA}22"),
        bgcolor=CINZA_CARD,
        padding=35,
        border_radius=30,
        animate=ft.animation.Animation(600, ft.AnimationCurve.DECELERATE),
    )

    container.max_width = 380
    return container