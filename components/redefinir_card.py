import flet as ft


def criar_redefinir_card(AMARELO_BANANA, CINZA_FUNDO, CINZA_CARD, ao_salvar_callback):
    forca_barra = ft.ProgressBar(
        value=0,
        bgcolor="#333333",
        color=ft.Colors.RED_400,
        height=4,
        border_radius=2,
    )
    forca_texto = ft.Text("", size=11, color=ft.Colors.RED_400)

    def calcular_forca(senha: str):
        if not senha:
            return 0, "", ft.Colors.RED_400
        pontos = 0
        if len(senha) >= 6:  pontos += 1
        if len(senha) >= 10: pontos += 1
        if any(c.isupper() for c in senha): pontos += 1
        if any(c.isdigit() for c in senha): pontos += 1
        if any(c in "!@#$%^&*" for c in senha): pontos += 1
        if pontos <= 1: return 0.2, "Muito fraca",  ft.Colors.RED_400
        if pontos == 2: return 0.4, "Fraca",        ft.Colors.ORANGE_400
        if pontos == 3: return 0.6, "Razoável",     ft.Colors.YELLOW_400
        if pontos == 4: return 0.8, "Forte",        ft.Colors.LIGHT_GREEN_400
        return 1.0, "Muito forte", ft.Colors.GREEN_400

    def ao_digitar_senha(e):
        valor, label, cor = calcular_forca(e.data)
        forca_barra.value = valor
        forca_barra.color = cor
        forca_texto.value = label
        forca_texto.color = cor
        forca_barra.update()
        forca_texto.update()
        if confirmar_senha.value:
            confirmar_senha.error_text = (
                "As senhas não coincidem"
                if nova_senha.value != confirmar_senha.value
                else None
            )
            confirmar_senha.update()

    def ao_digitar_confirmacao(e):
        confirmar_senha.error_text = (
            "As senhas não coincidem"
            if nova_senha.value and e.data != nova_senha.value
            else None
        )
        confirmar_senha.update()

    nova_senha = ft.TextField(
        label="Nova Senha Definitiva",
        password=True,
        can_reveal_password=True,
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        color="white",
        on_change=ao_digitar_senha,
        on_submit=lambda e: confirmar_senha.focus(),
    )
    confirmar_senha = ft.TextField(
        label="Confirme a Nova Senha",
        password=True,
        can_reveal_password=True,
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        color="white",
        on_change=ao_digitar_confirmacao,
        on_submit=lambda e: ao_clicar_salvar(e),
    )

    btn_salvar = ft.ElevatedButton(
        text="SALVAR E ACESSAR",
        bgcolor=AMARELO_BANANA,
        color=CINZA_FUNDO,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
        ),
        width=520,
        height=50,
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

    container = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.LOCK_RESET_ROUNDED, color=AMARELO_BANANA, size=50),
            ft.Text("Definir Nova Senha", size=26, weight="bold", color="white"),
            ft.Text(
                "Sua senha atual é temporária. Por segurança, escolha uma nova senha definitiva.",
                text_align=ft.TextAlign.CENTER,
                color="#AAAAAA",
                size=13,
            ),
            ft.Divider(height=10, color="transparent"),
            # Dois campos lado a lado
            ft.Row([
                ft.Column([nova_senha,     forca_barra, forca_texto], expand=True, spacing=4),
                ft.Column([confirmar_senha], expand=True, spacing=4),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Divider(height=10, color="transparent"),
            btn_salvar,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
        bgcolor=CINZA_CARD,
        padding=40,
        border_radius=30,
        border=ft.border.all(1, f"{AMARELO_BANANA}33"),
        width=600,
        animate=ft.animation.Animation(600, ft.AnimationCurve.DECELERATE),
    )
    return container