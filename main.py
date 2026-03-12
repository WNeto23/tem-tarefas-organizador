import flet as ft
import asyncio
import secrets
import string
from datetime import datetime
from dotenv import load_dotenv
import os

# ── IMPORTS CORRIGIDOS ───────────────────────────────────────────────
from tarefas_api_client import UsuarioModel, TarefaModel
# ─────────────────────────────────────────────────────────────────────

from components.login_card import criar_login_card
from components.cadastro_card import criar_cadastro_card
from components.esqueci_senha_card import criar_esqueci_senha_card
from components.redefinir_card import criar_redefinir_card
from utils.email_service import enviar_email_recuperacao
from dashboard import criar_dashboard
from utils.telegram_service import TelegramService
from utils.rodape import criar_rodape
from utils.notificacao_service import NotificacaoService
from utils.card_nova_tarefa import abrir_modal_nova_tarefa

load_dotenv()


def main(page: ft.Page):
    page.theme_mode        = ft.ThemeMode.DARK
    page.window.width      = 1280
    page.window.height     = 800
    page.window.min_width  = 900
    page.window.min_height = 600
    page.window.resizable  = True
    page.title             = "Tem Tarefas? - Organizador"
    page.bgcolor           = "#121212"
    page.padding           = 0

    AMARELO_BANANA = "#F2C94C"
    CINZA_FUNDO    = "#121212"
    CINZA_CARD     = "#1E1E1E"

    # --- Loading overlay ---
    loading_overlay = ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(width=50, height=50, stroke_width=6, color=AMARELO_BANANA),
                ft.Text("Carregando...", color="white", size=16, weight="bold"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        bgcolor=ft.Colors.with_opacity(0.9, CINZA_FUNDO),
        expand=True,
        alignment=ft.alignment.center,
        visible=False,
    )
    page.overlay.append(loading_overlay)

    # ── INICIALIZA OS MODELS DA API ───────────────────────────────────
    user_model   = UsuarioModel()
    tarefa_model = TarefaModel()
    # ─────────────────────────────────────────────────────────────────

    TOKEN        = os.getenv("TOKEN_TELEGRAM")
    bot_telegram = TelegramService(TOKEN)

    notificacao_service = NotificacaoService(
        tarefa_model=tarefa_model,
        usuario_model=user_model,
        bot_telegram=bot_telegram,
    )
    notificacao_service.iniciar()

    def ao_fechar_app(e):
        notificacao_service.parar()
        # Não precisa fechar conexão de banco, apenas para o scheduler

    page.on_close = ao_fechar_app

    def mostrar_snack(texto, cor):
        snack = ft.SnackBar(
            content=ft.Text(texto, color="white"),
            bgcolor=cor,
            duration=3000,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def mostrar_loading(mostrar: bool = True):
        loading_overlay.visible = mostrar
        page.update()

    def view_auth(rota: str, card) -> ft.View:
        return ft.View(
            rota,
            bgcolor=CINZA_FUNDO,
            padding=0,
            controls=[
                ft.Stack(
                    [
                        ft.Container(
                            content=card,
                            alignment=ft.alignment.center,
                            expand=True,
                        ),
                        ft.Container(
                            content=criar_rodape(),
                            alignment=ft.alignment.bottom_center,
                            bottom=0,
                            left=0,
                            right=0,
                        ),
                    ],
                    expand=True,
                )
            ],
        )

    def ir_para_cadastro(e):
        page.go("/cadastro")

    def ir_para_login(e=None):
        page.go("/login")

    def ir_para_esqueci_senha(e):
        page.go("/esqueci_senha")

    # ── FUNÇÃO DE LOGIN CORRIGIDA ─────────────────────────────────────
    async def realizar_login(e, usuario_input, senha_input, container_login):
        if not usuario_input.value or not senha_input.value:
            mostrar_snack("Preencha os campos para entrar!", ft.Colors.ORANGE_700)
            return
        
        mostrar_loading(True)
        try:
            # Chama o método do proxy que usa a API
            usuario_logado = user_model.verificar_login(
                usuario_input.value, senha_input.value
            )
            
            if usuario_logado:
                page.session.set("user_id",   usuario_logado["id"])
                page.session.set("user_name", usuario_logado["nome_completo"])
                page.session.set("user_foto", usuario_logado.get("foto"))
                
                # Arquiva tarefas antigas em background (agora via API)
                asyncio.create_task(
                    asyncio.to_thread(
                        tarefa_model.arquivar_tarefas_antigas, usuario_logado["id"]
                    )
                )
                
                id_telegram_db = usuario_logado.get("telegram_chat_id")
                page.session.set("user_telegram", id_telegram_db)
                
                if id_telegram_db:
                    agora = datetime.now().strftime("%H:%M - %d/%m/%Y")
                    bot_telegram.enviar_mensagem(
                        id_telegram_db,
                        f"🔐 *ACESSO CONFIRMADO*\n"
                        f"`------------------------------`\n\n"
                        f"Olá *{usuario_logado['nome_completo']}*,\n"
                        f"Seu painel de tarefas foi acessado agora.\n\n"
                        f"🕒 *Horário:* {agora}\n"
                        f"🖥️ *Plataforma:* Organizador Desktop\n\n"
                        f"🟡 _Se não reconhece este acesso, revise suas credenciais._"
                    )
                
                container_login.opacity = 0
                container_login.scale   = 0.9
                page.update()
                await asyncio.sleep(0.3)
                
                if usuario_logado.get("trocar_senha"):
                    exibir_tela_redefinir()
                else:
                    page.go("/dashboard")
            else:
                mostrar_snack("Usuário ou senha incorretos!", ft.Colors.RED_700)
                mostrar_loading(False)
                
        except Exception as ex:
            print(f"Erro detalhado: {ex}")  # Log para debug
            mostrar_snack(f"Erro ao conectar com o servidor: {str(ex)}", ft.Colors.RED_900)
            mostrar_loading(False)

    def realizar_login_handler(e, usuario_input, senha_input, container_login):
        page.run_task(realizar_login, e, usuario_input, senha_input, container_login)

    # ── FUNÇÃO DE RECUPERAÇÃO CORRIGIDA ───────────────────────────────
    async def processar_recuperacao_temporaria(e, email_campo, canal):
        email = email_campo.value
        
        try:
            # Busca dados do usuário via API
            dados_user = user_model.buscar_dados_por_email(email)
            
            if dados_user:
                caracteres = string.ascii_letters + string.digits
                senha_temp = "".join(secrets.choice(caracteres) for _ in range(8))
                
                # Define senha temporária via API
                if user_model.definir_senha_temporaria(email, senha_temp):
                    chat_id, nome_user = dados_user
                    
                    enviou_email = False
                    enviou_telegram = False
                    
                    if canal in ("email", "ambos"):
                        enviou_email = enviar_email_recuperacao(email, senha_temp)
                    
                    if canal in ("telegram", "ambos"):
                        if chat_id:
                            bot_telegram.enviar_mensagem(
                                chat_id,
                                f"🔑 *RECUPERAÇÃO DE ACESSO*\n"
                                f"`------------------------------`\n\n"
                                f"Olá *{nome_user}*,\n"
                                f"Sua senha temporária é:\n\n"
                                f"👉 `{senha_temp}`\n\n"
                                f"🟡 Defina uma nova senha ao entrar."
                            )
                            enviou_telegram = True
                        else:
                            mostrar_snack(
                                "Telegram não vinculado. Enviando só por e-mail.",
                                ft.Colors.ORANGE_700,
                            )
                            enviar_email_recuperacao(email, senha_temp)
                            enviou_email = True
                    
                    if enviou_email and enviou_telegram:
                        mostrar_snack("Senha enviada por E-mail e Telegram!", ft.Colors.GREEN_700)
                    elif enviou_telegram:
                        mostrar_snack("Senha enviada pelo Telegram!", ft.Colors.GREEN_700)
                    elif enviou_email:
                        mostrar_snack(f"Senha enviada para {email}!", ft.Colors.GREEN_700)
                    
                    ir_para_login()
                else:
                    mostrar_snack("Erro ao gerar senha temporária.", ft.Colors.RED_700)
            else:
                email_campo.error_text = "E-mail não encontrado."
                email_campo.update()
                
        except Exception as ex:
            mostrar_snack(f"Erro na recuperação: {str(ex)}", ft.Colors.RED_900)

    # ── REDEFINIR SENHA ───────────────────────────────────────────────
    def exibir_tela_redefinir():
        def salvar_nova_senha(e, nova_input, confirma_input):
            if not nova_input.value or len(nova_input.value) < 6:
                mostrar_snack("A senha deve ter no mínimo 6 caracteres!", ft.Colors.ORANGE_700)
                return
            if nova_input.value != confirma_input.value:
                confirma_input.error_text = "As senhas não coincidem"
                page.update()
                return
            
            user_id = page.session.get("user_id")
            
            # Atualiza senha via API
            if user_model.atualizar_senha_definitiva(user_id, nova_input.value):
                mostrar_snack("Senha atualizada! Bem-vindo.", ft.Colors.GREEN_700)
                mostrar_loading(True)
                page.go("/dashboard")
            else:
                mostrar_snack("Erro ao atualizar senha.", ft.Colors.RED_700)
            
            page.update()

        redefinir_card = criar_redefinir_card(
            AMARELO_BANANA, CINZA_FUNDO, CINZA_CARD, salvar_nova_senha
        )
        page.views.clear()
        page.views.append(view_auth("/redefinir", redefinir_card))
        page.update()

    # ── CADASTRO ──────────────────────────────────────────────────────
    def finalizar_cadastro(e, nome_completo, usuario, email, senha, foto):
        if not all([nome_completo.value, usuario.value, email.value, senha.value]):
            mostrar_snack("Por favor, preencha todos os campos!", ft.Colors.ORANGE_700)
            return
        
        try:
            # Verificações via API
            if user_model.verificar_usuario_existe(usuario.value):
                mostrar_snack("Este nome de usuário já está em uso.", ft.Colors.RED_700)
                return
            
            if user_model.verificar_email_existe(email.value):
                mostrar_snack("Este e-mail já está cadastrado.", ft.Colors.RED_700)
                return
            
            # Cadastro via API
            user_id = user_model.cadastrar(
                nome_completo.value, usuario.value, email.value, senha.value, foto
            )
            
            if user_id:
                mostrar_snack("Conta criada com sucesso!", ft.Colors.GREEN_700)
                ir_para_login()
            else:
                mostrar_snack("Erro ao criar conta.", ft.Colors.RED_700)
                
        except Exception as ex:
            mostrar_snack(f"Erro ao cadastrar: {ex}", ft.Colors.RED_900)

    # ── VINCULAR TELEGRAM ─────────────────────────────────────────────
    def vincular_telegram_automatico(e):
        codigo = "".join(secrets.choice(string.digits) for _ in range(6))
        page.session.set("codigo_vinculo_telegram", codigo)
        
        # LOG PARA DEBUG
        print(f"🔵 Código gerado: {codigo}")

        def ao_confirmar_codigo(e):
            codigo_digitado = campo_codigo.value.strip()
            codigo_esperado = page.session.get("codigo_vinculo_telegram")
            
            print(f"🔵 Comparando: '{codigo_digitado}' vs '{codigo_esperado}'")
            
            if codigo_digitado != codigo_esperado:
                mostrar_snack("Código inválido. Tente novamente.", ft.Colors.RED_700)
                return
            
            # Mostra mensagem de aguarde
            mostrar_snack("Verificando mensagens no Telegram...", ft.Colors.BLUE_700)
            
            # 👇 MUDANÇA: Passa o código esperado para o método
            chat_id, nome_telegram = bot_telegram.capturar_id_automatico(codigo_esperado)
            print(f"🔵 Resultado: chat_id={chat_id}, nome={nome_telegram}")
            
            if chat_id:
                user_id = page.session.get("user_id")
                
                # Vincula via API
                if user_model.vincular_telegram(user_id, str(chat_id)):
                    page.session.set("user_telegram", str(chat_id))
                    page.session.remove("codigo_vinculo_telegram")
                    
                    # Envia mensagem de confirmação
                    bot_telegram.enviar_mensagem(
                        chat_id,
                        f"✅ *Vínculo Confirmado!*\n\n"
                        f"Olá {nome_telegram}, seu Telegram agora está conectado ao "
                        f"*Tem Tarefas?*. Você receberá alertas de tarefas por aqui.",
                    )
                    
                    dialogo.open = False
                    page.update()
                    mostrar_snack(
                        f"Vinculado ao Telegram de {nome_telegram}!",
                        ft.Colors.GREEN_700,
                    )
                else:
                    mostrar_snack("Erro ao vincular no servidor.", ft.Colors.RED_700)
            else:
                mostrar_snack(
                    "Código não encontrado. Envie o código exato para o bot!",
                    ft.Colors.ORANGE_700,
                )

        campo_codigo = ft.TextField(
            label="Código enviado para o bot",
            border_color=AMARELO_BANANA,
            border_radius=10,
            color="white",
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=6,
        )
        
        dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=CINZA_CARD,
            title=ft.Text("Vincular Telegram", color=AMARELO_BANANA, weight="bold"),
            content=ft.Column(
                [
                    ft.Text(
                        "1. Abra o Telegram e mande esta mensagem para o bot:",
                        size=13,
                        color="white",
                    ),
                    ft.Container(
                        content=ft.Text(codigo, size=32, weight="bold", color=AMARELO_BANANA),
                        alignment=ft.alignment.center,
                        bgcolor=CINZA_FUNDO,
                        border_radius=10,
                        padding=15,
                    ),
                    ft.Text("2. Depois confirme abaixo:", size=13, color="white"),
                    campo_codigo,
                ],
                tight=True,
                spacing=8,
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=lambda _: (setattr(dialogo, "open", False), page.update()),
                ),
                ft.ElevatedButton(
                    "Confirmar",
                    bgcolor=AMARELO_BANANA,
                    color=CINZA_FUNDO,
                    on_click=ao_confirmar_codigo,
                ),
            ],
        )
        
        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()

    # ── ROTEAMENTO ────────────────────────────────────────────────────
    def route_change(e):
        rota = page.route
        
        if rota == "/dashboard":
            if page.views and page.views[-1].route == "/dashboard":
                mostrar_loading(False)
                return
            
            page.views.clear()
            page.on_vincular_telegram = vincular_telegram_automatico
            
            dash = criar_dashboard(
                page=page,
                AMARELO_BANANA=AMARELO_BANANA,
                CINZA_FUNDO=CINZA_FUNDO,
                CINZA_CARD=CINZA_CARD,
                user_model=user_model,
                on_nova_tarefa=abrir_modal_nova_tarefa,
            )
            page.views.append(dash)
            mostrar_loading(False)
            
        elif rota == "/arquivo_morto":
            # Implementar se necessário
            pass
            
        else:
            page.views.clear()
            
            if rota == "/login":
                page.views.append(
                    view_auth(
                        "/login",
                        criar_login_card(
                            AMARELO_BANANA,
                            CINZA_FUNDO,
                            CINZA_CARD,
                            realizar_login_handler,
                            ir_para_cadastro,
                            ir_para_esqueci_senha,
                        ),
                    )
                )
            elif rota == "/cadastro":
                page.views.append(
                    view_auth(
                        "/cadastro",
                        criar_cadastro_card(
                            page,
                            AMARELO_BANANA,
                            CINZA_FUNDO,
                            CINZA_CARD,
                            ir_para_login,
                            finalizar_cadastro,
                        ),
                    )
                )
            elif rota == "/esqueci_senha":
                page.views.append(
                    view_auth(
                        "/esqueci_senha",
                        criar_esqueci_senha_card(
                            AMARELO_BANANA,
                            CINZA_FUNDO,
                            CINZA_CARD,
                            ir_para_login,
                            processar_recuperacao_temporaria,
                            page,
                        ),
                    )
                )
        
        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top = page.views[-1]
            page.go(top.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")


if __name__ == "__main__":
    ft.app(target=main)