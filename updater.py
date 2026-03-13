"""
updater.py
==========
Sistema de auto-atualização via API própria no Railway.

Fluxo:
  1. Consulta GET /tarefas-app/versao na sua API
  2. Compara com a versão local (version.py)
  3. Se houver versão mais nova, baixa o novo .exe da URL retornada
  4. Substitui o executável atual e reinicia o app

A API retorna:
  { "versao": "1.0.1", "url_download": "https://...", "notas": "..." }
"""

import os
import sys
import subprocess
import tempfile
import requests
from pathlib import Path
from dotenv import load_dotenv
from version import VERSION

load_dotenv()

_API_URL   = os.getenv("API_URL_TAREFAS", "https://web-apitarefas.up.railway.app")
_TOKEN     = os.getenv("API_TOKEN_TAREFAS", "")
_HEADERS   = {"x-token": _TOKEN}
_TIMEOUT   = 8
_ENDPOINT  = f"{_API_URL}/tarefas-app/versao"


def _executavel_atual() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path(__file__)


def _versao_para_tupla(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except:
        return (0, 0, 0)


def verificar_atualizacao() -> dict | None:
    """
    Consulta a API para verificar se há versão mais nova.
    Retorna dict com {versao, url_download, notas} ou None.
    """
    try:
        resp = requests.get(_ENDPOINT, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        dados = resp.json()

        versao_remota = dados.get("versao", "0.0.0")
        url_download  = dados.get("url_download", "")
        notas         = dados.get("notas", "")

        if not url_download:
            print("⚠️  API não retornou url_download — atualização ignorada")
            return None

        if _versao_para_tupla(versao_remota) <= _versao_para_tupla(VERSION):
            print(f"✅ App atualizado — versão {VERSION}")
            return None

        print(f"🆕 Nova versão disponível: {versao_remota} (atual: {VERSION})")
        return {
            "versao":       versao_remota,
            "url_download": url_download,
            "notas":        notas,
        }

    except requests.ConnectionError:
        print("⚠️  Sem conexão — verificação de atualização ignorada")
        return None
    except Exception as e:
        print(f"⚠️  Erro ao verificar atualização: {e}")
        return None


def baixar_e_instalar(url_download: str, nova_versao: str, callback_progresso=None) -> bool:
    """
    Baixa o novo .exe e cria um .bat que substitui e reinicia o app.
    """
    exe_atual = _executavel_atual()
    tmp_path  = None

    try:
        print(f"⬇️  Baixando versão {nova_versao}...")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as tmp:
            tmp_path = Path(tmp.name)

        resp = requests.get(url_download, stream=True, timeout=120)
        resp.raise_for_status()

        total   = int(resp.headers.get("content-length", 0))
        baixado = 0

        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                baixado += len(chunk)
                if callback_progresso and total:
                    callback_progresso(baixado / total)

        print(f"✅ Download concluído: {tmp_path}")

        bat_path    = exe_atual.parent / "_update.bat"
        bat_content = f"""@echo off
echo Atualizando {exe_atual.name}...
timeout /t 2 /nobreak >nul
move /y "{tmp_path}" "{exe_atual}"
echo Iniciando nova versao...
start "" "{exe_atual}"
del "%~f0"
"""
        bat_path.write_text(bat_content, encoding="utf-8")

        subprocess.Popen(
            str(bat_path),
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        print("🔄 Atualização em andamento — o app será reiniciado automaticamente")
        return True

    except Exception as e:
        print(f"🔴 Erro ao baixar atualização: {e}")
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        return False