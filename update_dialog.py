"""
update_dialog.py
================
Diálogo de atualização para o Flet.
Exibe notificação quando há nova versão disponível,
com barra de progresso durante o download.
"""

import flet as ft
import threading
from updater import baixar_e_instalar


def mostrar_dialogo_atualizacao(
    page: ft.Page,
    info_atualizacao: dict,
    AMARELO_BANANA: str,
    CINZA_FUNDO: str,
    CINZA_CARD: str,
):
    """
    Exibe diálogo perguntando se o usuário quer atualizar.
    info_atualizacao: dict retornado por verificar_atualizacao()
    """

    versao      = info_atualizacao["versao"]
    url         = info_atualizacao["url_download"]
    notas       = info_atualizacao.get("notas", "")

    progresso_bar  = ft.ProgressBar(
        value=0,
        bgcolor="#333333",
        color=AMARELO_BANANA,
        height=6,
        border_radius=3,
        visible=False,
    )
    status_texto = ft.Text("", size=12, color="#AAAAAA")
    btn_atualizar = ft.ElevatedButton(
        text="Atualizar agora",
        bgcolor=AMARELO_BANANA,
        color=CINZA_FUNDO,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )
    btn_depois = ft.TextButton(
        text="Depois",
        style=ft.ButtonStyle(color="#AAAAAA"),
    )

    dialogo = ft.AlertDialog(
        modal=True,
        bgcolor=CINZA_CARD,
        title=ft.Row(
            [
                ft.Icon(ft.Icons.SYSTEM_UPDATE_ROUNDED, color=AMARELO_BANANA, size=22),
                ft.Text(
                    f"Atualização disponível — v{versao}",
                    color="white",
                    size=16,
                    weight=ft.FontWeight.W_500,
                ),
            ],
            spacing=10,
        ),
        content=ft.Column(
            [
                ft.Text(
                    f"Você está usando a versão atual. A versão {versao} já está disponível.",
                    size=13,
                    color="#CCCCCC",
                ),
                ft.Container(
                    content=ft.Text(
                        notas[:300] + ("..." if len(notas) > 300 else "") if notas else "Melhorias e correções.",
                        size=12,
                        color="#888888",
                    ),
                    bgcolor="#2A2A2A",
                    border_radius=8,
                    padding=10,
                    visible=bool(notas),
                ),
                progresso_bar,
                status_texto,
            ],
            spacing=12,
            tight=True,
            width=400,
        ),
        actions=[btn_depois, btn_atualizar],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def fechar(e=None):
        dialogo.open = False
        page.update()

    def iniciar_download(e):
        btn_atualizar.disabled = True
        btn_atualizar.text     = "Baixando..."
        btn_depois.disabled    = True
        progresso_bar.visible  = True
        status_texto.value     = "Preparando download..."
        page.update()

        def progresso(pct):
            progresso_bar.value = pct
            status_texto.value  = f"Baixando... {int(pct * 100)}%"
            page.update()

        def executar():
            ok = baixar_e_instalar(url, versao, callback_progresso=progresso)
            if ok:
                status_texto.value = "✅ Pronto! O app será reiniciado automaticamente."
                progresso_bar.value = 1.0
                page.update()
                import time
                time.sleep(2)
                page.window.close()
            else:
                status_texto.value = "❌ Erro no download. Tente novamente mais tarde."
                btn_atualizar.disabled = False
                btn_atualizar.text     = "Tentar novamente"
                btn_depois.disabled    = False
                page.update()

        threading.Thread(target=executar, daemon=True).start()

    btn_atualizar.on_click = iniciar_download
    btn_depois.on_click    = fechar

    page.overlay.append(dialogo)
    dialogo.open = True
    page.update()