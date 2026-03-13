import flet as ft


def criar_redefinir_card(AMARELO_BANANA, CINZA_FUNDO, CINZA_CARD, ao_salvar_callback):

    forca_barra = ft.ProgressBar(
        value=0,
        bgcolor="#2A2A2A",
        color=ft.Colors.RED_400,
        height=4,
        border_radius=2,
        expand=True,
    )
    forca_texto = ft.Text("", size=11, color=ft.Colors.RED_400)
    match_texto = ft.Text("", size=11)

    def calcular_forca(senha: str):
        if not senha:
            return 0, "", ft.Colors.RED_400
        pontos = 0
        if len(senha) >= 6:  pontos += 1
        if len(senha) >= 10: pontos += 1
        if any(c.isupper() for c in senha): pontos += 1
        if any(c.isdigit() for c in senha): pontos += 1
        if any(c in "!@#$%^&*" for c in senha): pontos += 1
        if pontos <= 1: return 0.2, "Muito fraca",    ft.Colors.RED_400
        if pontos == 2: return 0.4, "Fraca",          ft.Colors.ORANGE_400
        if pontos == 3: return 0.6, "Razoável",       ft.Colors.YELLOW_400
        if pontos == 4: return 0.8, "Forte",          ft.Colors.LIGHT_GREEN_400
        return          1.0, "Muito forte",           ft.Colors.GREEN_400

    def atualizar_match():
        v1 = nova_senha.value or ""
        v2 = confirmar_senha.value or ""
        if not v2:
            match_texto.value = ""
        elif v1 != v2:
            match_texto.value = "As senhas não coincidem"
            match_texto.color = ft.Colors.RED_400
        else:
            match_texto.value = "✓ Senhas coincidem"
            match_texto.color = ft.Colors.GREEN_400
        match_texto.update()

    def ao_digitar_senha(e):
        valor, label, cor = calcular_forca(e.data)
        forca_barra.value = valor
        forca_barra.color = cor
        forca_texto.value = label
        forca_texto.color = cor
        forca_barra.update()
        forca_texto.update()
        if confirmar_senha.value:
            atualizar_match()

    def ao_digitar_confirmacao(e):
        atualizar_match()

    nova_senha = ft.TextField(
        hint_text="Mínimo 6 caracteres",
        password=True,
        can_reveal_password=True,
        border_color="#3A3A3A",
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        bgcolor="#2A2A2A",
        color="white",
        hint_style=ft.TextStyle(color="#555555"),
        border_radius=10,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=12),
        on_change=ao_digitar_senha,
        on_submit=lambda e: confirmar_senha.focus(),
    )

    confirmar_senha = ft.TextField(
        hint_text="Repita a nova senha",
        password=True,
        can_reveal_password=True,
        border_color="#3A3A3A",
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        bgcolor="#2A2A2A",
        color="white",
        hint_style=ft.TextStyle(color="#555555"),
        border_radius=10,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=12),
        on_change=ao_digitar_confirmacao,
        on_submit=lambda e: ao_clicar_salvar(e),
    )

    btn_salvar = ft.ElevatedButton(
        text="SALVAR E ACESSAR",
        bgcolor=AMARELO_BANANA,
        color=CINZA_FUNDO,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=14),
        ),
        height=52,
        expand=True,
    )

    def ao_clicar_salvar(e):
        btn_salvar.disabled = True
        btn_salvar.text     = "Salvando..."
        btn_salvar.update()
        try:
            ao_salvar_callback(e, nova_senha, confirmar_senha)
        finally:
            try:
                btn_salvar.disabled = False
                btn_salvar.text     = "SALVAR E ACESSAR"
                btn_salvar.update()
            except Exception:
                pass

    btn_salvar.on_click = ao_clicar_salvar

    def label(texto):
        return ft.Text(texto, size=11, color="#888888", weight=ft.FontWeight.W_500)

    card = ft.Container(
        content=ft.Column(
            [
                # Ícone + título
                ft.Column(
                    [
                        ft.Container(
                            content=ft.Icon(ft.Icons.LOCK_RESET_ROUNDED, color=AMARELO_BANANA, size=28),
                            width=64,
                            height=64,
                            border_radius=32,
                            bgcolor=f"{AMARELO_BANANA}1A",
                            border=ft.border.all(1.5, f"{AMARELO_BANANA}4D"),
                            alignment=ft.alignment.center,
                        ),
                        ft.Text("Definir nova senha", size=22, weight=ft.FontWeight.W_500, color="white"),
                        ft.Text(
                            "Sua senha atual é temporária. Escolha uma senha definitiva para continuar.",
                            size=13,
                            color="#888888",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),

                ft.Divider(height=6, color="transparent"),

                # Nova senha
                ft.Column(
                    [
                        label("NOVA SENHA"),
                        nova_senha,
                        ft.Row(
                            [forca_barra, forca_texto],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=6,
                ),

                ft.Divider(height=2, color="transparent"),

                # Confirmar senha
                ft.Column(
                    [
                        label("CONFIRMAR SENHA"),
                        confirmar_senha,
                        match_texto,
                    ],
                    spacing=6,
                ),

                ft.Divider(height=6, color="transparent"),

                ft.Row([btn_salvar]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            tight=True,
        ),
        bgcolor=CINZA_CARD,
        padding=48,
        border_radius=24,
        border=ft.border.all(1, f"{AMARELO_BANANA}33"),
        width=500,
        animate=ft.animation.Animation(600, ft.AnimationCurve.DECELERATE),
    )

    # Wrapper que centraliza o card vertical e horizontalmente
    return ft.Container(
        content=card,
        alignment=ft.alignment.center,
        expand=True,
    )