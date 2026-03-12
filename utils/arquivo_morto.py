import flet as ft
from datetime import datetime


def criar_arquivo_morto(
    page: ft.Page,
    AMARELO_BANANA,
    CINZA_FUNDO,
    CINZA_CARD,
    tarefa_model=None,
    user_id=None,
):
    def mostrar_snack(texto, cor):
        snack = ft.SnackBar(content=ft.Text(texto, color="white"), bgcolor=cor)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def carregar_tarefas_arquivadas():
        if not tarefa_model or not user_id:
            return []
        return tarefa_model.listar_arquivadas(user_id)

    def restaurar_tarefa(e, tarefa_id):
        if tarefa_model and tarefa_model.restaurar_do_arquivo(tarefa_id):
            mostrar_snack("Tarefa restaurada com sucesso!", ft.Colors.GREEN_700)
            atualizar_lista()

    def excluir_permanentemente(e, tarefa_id):
        if not tarefa_model:
            return

        def confirmar_exclusao(e):
            if tarefa_model.excluir_permanentemente(tarefa_id):
                dialog.open = False
                page.update()
                mostrar_snack("Tarefa excluída permanentemente!", ft.Colors.RED_700)
                atualizar_lista()

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=CINZA_CARD,
            title=ft.Text("Confirmar exclusão", color=AMARELO_BANANA, weight="bold"),
            content=ft.Text(
                "Esta ação não pode ser desfeita. Deseja continuar?",
                color="white",
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color="#888888"),
                    on_click=lambda _: (setattr(dialog, "open", False), page.update()),
                ),
                ft.ElevatedButton(
                    "Excluir Permanentemente",
                    bgcolor=ft.Colors.RED_700,
                    color="white",
                    on_click=confirmar_exclusao,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    lista_tarefas = ft.ListView(spacing=10, padding=20, expand=True)

    def criar_card_arquivado(tarefa):
        tid, titulo, descricao, status, data_criacao, fase, data_venc, responsavel, data_conclusao = tarefa

        data_texto = ""
        if data_conclusao:
            if isinstance(data_conclusao, datetime):
                data_texto = data_conclusao.strftime("%d/%m/%Y")
            else:
                data_texto = str(data_conclusao)

        LABELS_STATUS = {
            "pra_ja":       "🔥 Pra Já",
            "depois":       "📋 Depois",
            "se_der_tempo": "🕐 Se Der Tempo",
            "em_andamento": "🔄 Em análise",
            "resolvido":    "✅ Resolvido",
            "parado":       "⏸️ Parado",
            "cancelado":    "🚫 Cancelado",
            "suspenso":     "⚠️ Suspenso",
        }

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ARCHIVE, color=AMARELO_BANANA, size=20),
                    ft.Text(
                        titulo,
                        size=15,
                        weight="bold",
                        color="white",
                        expand=True,
                    ),
                    ft.PopupMenuButton(
                        icon_color="#888888",
                        items=[
                            ft.PopupMenuItem(
                                icon=ft.Icons.RESTORE,
                                text="Restaurar",
                                on_click=lambda e, tid=tid: restaurar_tarefa(e, tid),
                            ),
                            ft.PopupMenuItem(
                                icon=ft.Icons.DELETE_FOREVER,
                                text="Excluir Permanentemente",
                                on_click=lambda e, tid=tid: excluir_permanentemente(e, tid),
                            ),
                        ],
                    ),
                ], spacing=8),
                ft.Row([
                    ft.Container(
                        content=ft.Text(
                            LABELS_STATUS.get(status, status),
                            size=10,
                            color="#AAAAAA",
                        ),
                        bgcolor="#2A2A2A",
                        border_radius=6,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    ),
                    ft.Container(
                        content=ft.Text(fase or "", size=10, color="#AAAAAA"),
                        bgcolor="#2A2A2A",
                        border_radius=6,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        visible=bool(fase),
                    ),
                ], spacing=6),
                ft.Text(
                    descricao or "Sem descrição",
                    size=12,
                    color="#888888",
                    max_lines=2,
                ),
                ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=11, color="#666666"),
                    ft.Text(
                        f"Concluída em: {data_texto}" if data_texto else "Sem data de conclusão",
                        size=11,
                        color="#666666",
                    ),
                ], spacing=4),
            ], spacing=6),
            bgcolor=CINZA_CARD,
            border_radius=10,
            padding=15,
            border=ft.border.all(1, "#333333"),
            margin=ft.margin.only(bottom=4),
        )

    def atualizar_lista():
        lista_tarefas.controls.clear()
        tarefas = carregar_tarefas_arquivadas()

        if not tarefas:
            lista_tarefas.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ARCHIVE, size=50, color="#444444"),
                        ft.Text(
                            "Nenhuma tarefa arquivada",
                            size=16,
                            color="#888888",
                        ),
                        ft.Text(
                            "Tarefas resolvidas há mais de 10 dias aparecerão aqui",
                            size=12,
                            color="#666666",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                    padding=50,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for tarefa in tarefas:
                lista_tarefas.controls.append(criar_card_arquivado(tarefa))

        page.update()

    atualizar_lista()

    return ft.View(
        "/arquivo_morto",
        bgcolor=CINZA_FUNDO,
        controls=[
            ft.AppBar(
                title=ft.Text("Arquivo Morto", color=CINZA_FUNDO, weight="bold"),
                bgcolor=AMARELO_BANANA,
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=CINZA_FUNDO,
                    tooltip="Voltar",
                    on_click=lambda _: page.go("/dashboard"),
                ),
            ),
            ft.Column([
                lista_tarefas,
            ], expand=True),
        ],
    )