import flet as ft
import base64
import os


def criar_perfil_dialog(page: ft.Page, AMARELO_BANANA, CINZA_FUNDO, CINZA_CARD, user_model):

    user_id   = page.session.get("user_id")
    user_name = page.session.get("user_name") or "Usuário"
    user_foto = page.session.get("user_foto")
    telegram  = page.session.get("user_telegram")
    iniciais  = "".join([n[0] for n in user_name.split()[:2]]).upper()

    nova_foto = {"valor": user_foto}

    avatar = ft.CircleAvatar(
        foreground_image_src=user_foto,
        content=ft.Text(iniciais, color="black", weight="bold"),
        bgcolor=AMARELO_BANANA,
        radius=45,
    )

    def ao_selecionar_foto(e: ft.FilePickerResultEvent):
        if e.files:
            caminho = e.files[0].path
            try:
                with open(caminho, "rb") as f:
                    dados = f.read()
                b64  = base64.b64encode(dados).decode("utf-8")
                ext  = os.path.splitext(caminho)[1].lower().replace(".", "")
                mime = "jpeg" if ext in ("jpg", "jpeg") else ext
                nova_foto["valor"] = f"data:image/{mime};base64,{b64}"
                avatar.foreground_image_src = nova_foto["valor"]
                avatar.content = None
                avatar.update()
            except Exception as ex:
                print(f"Erro ao carregar foto: {ex}")

    selecionador = ft.FilePicker(on_result=ao_selecionar_foto)
    if selecionador not in page.overlay:
        page.overlay.append(selecionador)

    campo_nome = ft.TextField(
        label="Nome Completo",
        value=user_name,
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        border_radius=12,
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        color="white",
    )

    dados_atuais = user_model.buscar_dados_por_email_ou_id(user_id)
    email_atual  = dados_atuais.get("email", "") if dados_atuais else ""

    campo_email = ft.TextField(
        label="E-mail",
        value=email_atual,
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        border_radius=12,
        prefix_icon=ft.Icons.EMAIL_OUTLINED,
        keyboard_type=ft.KeyboardType.EMAIL,
        color="white",
    )

    campo_nova_senha = ft.TextField(
        label="Nova Senha (deixe vazio para não alterar)",
        password=True,
        can_reveal_password=True,
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        border_radius=12,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        color="white",
        on_submit=lambda e: campo_confirmar_senha.focus(),
    )

    campo_confirmar_senha = ft.TextField(
        label="Confirme a Nova Senha",
        password=True,
        can_reveal_password=True,
        border_color=AMARELO_BANANA,
        focused_border_color=AMARELO_BANANA,
        cursor_color=AMARELO_BANANA,
        border_radius=12,
        prefix_icon=ft.Icons.LOCK_RESET_ROUNDED,
        color="white",
    )

    def ao_digitar_confirmacao(e):
        campo_confirmar_senha.error_text = (
            "As senhas não coincidem"
            if campo_nova_senha.value and e.data != campo_nova_senha.value
            else None
        )
        campo_confirmar_senha.update()

    campo_confirmar_senha.on_change = ao_digitar_confirmacao

    def mostrar_snack(texto, cor):
        snack = ft.SnackBar(content=ft.Text(texto, color="white"), bgcolor=cor)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- Seção Telegram ---
    secao_telegram = ft.Container(border_radius=10)

    def atualizar_secao_telegram(vinculado: bool):
        if vinculado:
            secao_telegram.content = ft.Row([
                ft.Icon(ft.Icons.SEND, color=ft.Colors.BLUE_400, size=20),
                ft.Text("Telegram vinculado ✅", color=ft.Colors.BLUE_400, size=13, expand=True),
                ft.TextButton(
                    "Desvincular",
                    style=ft.ButtonStyle(color=ft.Colors.RED_400),
                    on_click=lambda e: desvincular_telegram(),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            secao_telegram.bgcolor = f"{ft.Colors.BLUE_900}44"
            secao_telegram.padding = ft.padding.symmetric(horizontal=12, vertical=8)
        else:
            secao_telegram.content = ft.Row([
                ft.Icon(ft.Icons.SEND_OUTLINED, color="#555555", size=20),
                ft.Text("Telegram não vinculado", color="#555555", size=13),
            ], spacing=8)
            secao_telegram.bgcolor = "#1A1A1A"
            secao_telegram.padding = ft.padding.symmetric(horizontal=12, vertical=8)

    atualizar_secao_telegram(bool(telegram))

    def desvincular_telegram():
        if user_model.vincular_telegram(user_id, None):
            page.session.set("user_telegram", None)
            mostrar_snack("Telegram desvinculado.", ft.Colors.ORANGE_700)
            atualizar_secao_telegram(False)
            secao_telegram.update()

    # --- Botão Salvar ---
    btn_salvar = ft.ElevatedButton(
        text="SALVAR ALTERAÇÕES",
        width=320,
        height=50,
        bgcolor=AMARELO_BANANA,
        color=CINZA_FUNDO,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
        ),
    )

    # CORREÇÃO: síncrono — remove async/await
    def ao_salvar(e):
        if not campo_nome.value.strip():
            campo_nome.error_text = "O nome não pode ficar vazio"
            campo_nome.update()
            return

        if not campo_email.value.strip():
            campo_email.error_text = "O e-mail não pode ficar vazio"
            campo_email.update()
            return

        if campo_nova_senha.value:
            if len(campo_nova_senha.value) < 6:
                mostrar_snack("A senha deve ter no mínimo 6 caracteres.", ft.Colors.ORANGE_700)
                return
            if campo_nova_senha.value != campo_confirmar_senha.value:
                campo_confirmar_senha.error_text = "As senhas não coincidem"
                campo_confirmar_senha.update()
                return

        btn_salvar.disabled = True
        btn_salvar.text     = "Salvando..."
        btn_salvar.update()

        try:
            user_model.atualizar_perfil(
                user_id=user_id,
                nome_completo=campo_nome.value.strip(),
                email=campo_email.value.strip(),
                foto=nova_foto["valor"],
            )

            page.session.set("user_name", campo_nome.value.strip())
            page.session.set("user_foto", nova_foto["valor"])

            if campo_nova_senha.value:
                user_model.atualizar_senha_definitiva(user_id, campo_nova_senha.value)
                campo_nova_senha.value      = ""
                campo_confirmar_senha.value = ""
                campo_nova_senha.update()
                campo_confirmar_senha.update()

            mostrar_snack("Perfil atualizado com sucesso!", ft.Colors.GREEN_700)
            dialog.open = False
            page.update()

        except Exception as ex:
            mostrar_snack(f"Erro ao salvar: {ex}", ft.Colors.RED_900)
        finally:
            try:
                btn_salvar.disabled = False
                btn_salvar.text     = "SALVAR ALTERAÇÕES"
                btn_salvar.update()
            except Exception:
                pass

    btn_salvar.on_click = ao_salvar

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=CINZA_CARD,
        title=ft.Row([
            ft.Icon(ft.Icons.MANAGE_ACCOUNTS_ROUNDED, color=AMARELO_BANANA),
            ft.Text("Meu Perfil", color=AMARELO_BANANA, weight="bold"),
        ], spacing=8),
        content=ft.Container(
            width=340,
            content=ft.Column([
                ft.Stack([
                    avatar,
                    ft.IconButton(
                        icon=ft.Icons.ADD_A_PHOTO,
                        icon_color=CINZA_FUNDO,
                        bgcolor=AMARELO_BANANA,
                        bottom=0,
                        right=0,
                        scale=0.8,
                        tooltip="Trocar foto",
                        on_click=lambda _: selecionador.pick_files(
                            allow_multiple=False,
                            file_type=ft.FilePickerFileType.IMAGE,
                            dialog_title="Escolha sua nova foto",
                        ),
                    ),
                ], alignment=ft.alignment.center),
                ft.Divider(height=8, color="transparent"),
                ft.Text("Dados Pessoais", size=12, color="#888888", weight="bold"),
                campo_nome,
                campo_email,
                ft.Divider(height=4, color="#333333"),
                ft.Text("Alterar Senha", size=12, color="#888888", weight="bold"),
                campo_nova_senha,
                campo_confirmar_senha,
                ft.Divider(height=4, color="#333333"),
                ft.Text("Integrações", size=12, color="#888888", weight="bold"),
                secao_telegram,
                ft.Divider(height=8, color="transparent"),
                btn_salvar,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            ),
        ),
        actions=[
            ft.TextButton(
                "Fechar",
                style=ft.ButtonStyle(color="#888888"),
                on_click=lambda _: (setattr(dialog, "open", False), page.update()),
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    return dialog