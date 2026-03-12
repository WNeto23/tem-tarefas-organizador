from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importa as rotas
from routes.tarefas import router as tarefas_router
from routes.auth_routes import router as auth_router  # NOVA ROTA

app = FastAPI(title="UNIMED RV", version="2.0.0")

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas
app.include_router(auth_router)      # NOVO: rotas de autenticação
app.include_router(tarefas_router)   # rotas existentes

@app.get("/")
async def root():
    return {
        "api": "UNIMED RV",
        "versao": "2.0.0",
        "status": "online",
        "sistemas": [
            {
                "sistema": "Calendário / Notificações",
                "token_header": "x-token  →  API_TOKEN",
                "rotas": ["/prestadores", "/datas", "/log"]
            },
            {
                "sistema": "Tarefas",
                "token_header": "x-token  →  API_TOKEN_TAREFAS",
                "rotas": [
                    "/tarefas-app/usuarios",
                    "/tarefas-app/tarefas",
                    "/tarefas-app/auth"  # NOVA ROTA
                ]
            }
        ]
    }

@app.get("/health")
async def health():
    return {"status": "ok", "auth": "configured"}