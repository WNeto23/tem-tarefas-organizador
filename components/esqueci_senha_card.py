import flet as ft

def criar_esqueci_senha_card(AMARELO_BANANA, CINZA_FUNDO, CINZA_CARD, on_voltar, on_enviar_link, page):
    email_recuperacao = ft.TextField(
        label="E-mail cadastrado",
        border_color=AMARELO_BANANA,
        border_radius=15,
        prefix_icon=ft.Icons.MARK_EMAIL_READ_OUTLINED,
        cursor_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        keyboard_type=ft.KeyboardType.EMAIL,
        color="white",
        text_size=14,
        on_submit=lambda e: page.run_task(processo_recuperacao, e),
    )
    canal_escolhido = {"valor": "email"}

    def ao_mudar_canal(e):
        canal_escolhido["valor"] = e.control.value
        aviso_telegram.visible = e.control.value in ("telegram", "ambos")
        aviso_telegram.update()

    selector_canal = ft.RadioGroup(
        value="email",
        on_change=ao_mudar_canal,
        content=ft.Row([
            ft.Radio(
                value="email",
                label="E-mail",
                fill_color=AMARELO_BANANA,
                label_style=ft.TextStyle(color="white", size=13),
            ),
            ft.Radio(
                value="telegram",
                label="Telegram",
                fill_color=AMARELO_BANANA,
                label_style=ft.TextStyle(color="white", size=13),
            ),
            ft.Radio(
                value="ambos",
                label="Ambos",
                fill_color=AMARELO_BANANA,
                label_style=ft.TextStyle(color="white", size=13),
            ),
        ], alignment=ft.MainAxisAlignment.CENTER),
    )
    aviso_telegram = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_300, size=16),
            ft.Text(
                "Você precisa ter o Telegram vinculado à conta.",
                size=11,
                color=ft.Colors.BLUE_300,
            ),
        ], spacing=6),
        visible=False,
        bgcolor=f"{ft.Colors.BLUE_900}55",
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
    )
    btn_enviar = ft.ElevatedButton(
        text="ENVIAR SENHA",
        width=400,
        height=50,
        bgcolor=AMARELO_BANANA,
        color=CINZA_FUNDO,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=15),
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
        ),
    )

    async def processo_recuperacao(e):
        if not email_recuperacao.value:
            email_recuperacao.error_text = "Por favor, digite seu e-mail"
            email_recuperacao.update()
            return
        email_recuperacao.error_text = None
        email_recuperacao.update()
        btn_enviar.disabled = True
        btn_enviar.text     = "Enviando..."
        btn_enviar.update()
        try:
            await on_enviar_link(e, email_recuperacao, canal_escolhido["valor"])
        finally:
            try:
                btn_enviar.disabled = False
                btn_enviar.text     = "ENVIAR SENHA"
                btn_enviar.update()
            except Exception:
                pass

    btn_enviar.on_click = lambda e: page.run_task(processo_recuperacao, e)

    container = ft.Container(
        content=ft.Column(
            [
                ft.Icon(name=ft.Icons.LOCK_RESET_ROUNDED, color=AMARELO_BANANA, size=80),
                ft.Text("Recuperar Senha", size=36, weight="bold", color=AMARELO_BANANA),
                ft.Text(
                    "Escolha como deseja receber sua senha temporária.",
                    color=ft.Colors.GREEN_400,
                    text_align=ft.TextAlign.CENTER,
                    size=13,
                ),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                email_recuperacao,
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                ft.Text("Receber por:", size=12, color="#888888"),
                selector_canal,
                aviso_telegram,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                btn_enviar,
                ft.TextButton(
                    "Voltar para o Login",
                    on_click=on_voltar,
                    style=ft.ButtonStyle(color=AMARELO_BANANA),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            tight=True,
        ),
        width=380,
        bgcolor=CINZA_CARD,
        padding=35,
        border_radius=30,
        border=ft.border.all(1, f"{AMARELO_BANANA}22"),
        animate=ft.animation.Animation(600, ft.AnimationCurve.DECELERATE),
    )
    container.max_width = 380
    return container