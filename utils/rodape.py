import flet as ft
from datetime import datetime

def criar_rodape(cinza_card=None):
    ano_atual = datetime.now().year
    
    return ft.Container(
        content=ft.Row([
            ft.Image(
                src="https://upload.wikimedia.org/wikipedia/commons/0/05/Flag_of_Brazil.svg",
                width=18,
                height=12,
                fit=ft.ImageFit.CONTAIN,
            ),
            ft.Text(
                f"© {ano_atual} Tem Tarefas? · Todos os direitos reservados",
                size=11,
                color="#555555",
                text_align=ft.TextAlign.CENTER,
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
        margin=ft.margin.only(top=16),
    )