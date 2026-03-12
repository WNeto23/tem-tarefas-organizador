import flet as ft
import base64
import os

def criar_cadastro_card(page: ft.Page, AMARELO_BANANA, CINZA_FUNDO, CINZA_CARD, on_voltar, on_cadastrar):
    caminho_foto = {"valor": ""}

    def ao_selecionar_arquivo(e: ft.FilePickerResultEvent):
        if e.files:
            caminho = e.files[0].path
            try:
                with open(caminho, "rb") as f:
                    dados = f.read()
                b64  = base64.b64encode(dados).decode("utf-8")
                ext  = os.path.splitext(caminho)[1].lower().replace(".", "")
                mime = "jpeg" if ext in ("jpg", "jpeg") else ext
                caminho_foto["valor"] = f"data:image/{mime};base64,{b64}"
                foto_perfil.foreground_image_src = caminho_foto["valor"]
                foto_perfil.content = None
                foto_perfil.update()
            except Exception as ex:
                print(f"Erro ao carregar foto: {ex}")

    selecionador_arquivos = ft.FilePicker(on_result=ao_selecionar_arquivo)
    if selecionador_arquivos not in page.overlay:
        page.overlay.append(selecionador_arquivos)

    nome_input = ft.TextField(
        label="Nome Completo",
        border_color=AMARELO_BANANA,
        border_radius=15,
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        cursor_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        color="white",
        text_size=14,
        on_submit=lambda e: usuario_cadastro.focus(),
    )
    usuario_cadastro = ft.TextField(
        label="Escolha um Nome de Usuário",
        border_color=AMARELO_BANANA,
        border_radius=15,
        prefix_icon=ft.Icons.ALTERNATE_EMAIL,
        cursor_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        color="white",
        text_size=14,
        on_submit=lambda e: email_input.focus(),
        on_change=lambda e: (
            setattr(usuario_cadastro, "value", e.data.lower()),
            usuario_cadastro.update(),
        ),
    )
    email_input = ft.TextField(
        label="E-mail",
        border_color=AMARELO_BANANA,
        border_radius=15,
        prefix_icon=ft.Icons.EMAIL_OUTLINED,
        cursor_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        color="white",
        text_size=14,
        keyboard_type=ft.KeyboardType.EMAIL,
        on_submit=lambda e: senha_cadastro.focus(),
    )
    senha_cadastro = ft.TextField(
        label="Crie uma senha",
        password=True,
        can_reveal_password=True,
        border_color=AMARELO_BANANA,
        border_radius=15,
        prefix_icon=ft.Icons.LOCK_OUTLINED,
        cursor_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        color="white",
        text_size=14,
        on_submit=lambda e: ao_clicar_cadastro(e),
    )
    foto_perfil = ft.CircleAvatar(
        content=ft.Icon(ft.Icons.PERSON, size=40, color=AMARELO_BANANA),
        radius=50,
        bgcolor=ft.Colors.GREEN_900,
    )
    btn_cadastrar = ft.ElevatedButton(
        text="FINALIZAR CADASTRO",
        width=400,
        height=50,
        bgcolor=AMARELO_BANANA,
        color=CINZA_FUNDO,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=15),
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
        ),
    )

    def ao_clicar_cadastro(e):
        btn_cadastrar.disabled = True
        btn_cadastrar.text     = "Cadastrando..."
        btn_cadastrar.update()
        try:
            on_cadastrar(
                e,
                nome_input,
                usuario_cadastro,
                email_input,
                senha_cadastro,
                caminho_foto["valor"],
            )
        finally:
            try:
                btn_cadastrar.disabled = False
                btn_cadastrar.text     = "FINALIZAR CADASTRO"
                btn_cadastrar.update()
            except Exception:
                pass

    btn_cadastrar.on_click = ao_clicar_cadastro

    container = ft.Container(
        content=ft.Column(
            [
                ft.Text("Nova Conta", size=36, weight="bold", color=AMARELO_BANANA),
                ft.Stack([
                    foto_perfil,
                    ft.IconButton(
                        icon=ft.Icons.ADD_A_PHOTO,
                        icon_color=CINZA_FUNDO,
                        bgcolor=AMARELO_BANANA,
                        bottom=0,
                        right=0,
                        scale=0.8,
                        tooltip="Escolher foto de perfil",
                        on_click=lambda _: selecionador_arquivos.pick_files(
                            allow_multiple=False,
                            file_type=ft.FilePickerFileType.IMAGE,
                            dialog_title="Selecione sua foto de perfil",
                        ),
                    ),
                ]),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                nome_input,
                usuario_cadastro,
                email_input,
                senha_cadastro,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                btn_cadastrar,
                ft.TextButton(
                    "Já tem conta? Entrar",
                    on_click=on_voltar,
                    style=ft.ButtonStyle(color=AMARELO_BANANA),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
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