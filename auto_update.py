"""
auto_update.py
──────────────
Módulo de atualização automática via GitHub Releases.

Como usar no menu_principal.py:
    from auto_update import verificar_update
    ...
    # No __init__ do MenuPrincipal, após a janela estar pronta:
    self.after(1500, lambda: verificar_update(self))

Configuração necessária (apenas aqui neste arquivo):
    GITHUB_USER  → seu usuário do GitHub
    GITHUB_REPO  → nome do repositório
    VERSAO_ATUAL → versão atual do programa (atualize a cada release)

Como publicar uma nova versão:
    1. Atualize VERSAO_ATUAL aqui e nos outros arquivos.
    2. Gere os .exe com PyInstaller.
    3. Compacte todos os arquivos em update.zip (sem subpastas).
    4. Crie uma Release no GitHub com a tag "v1.1" (ou a versão nova).
    5. Faça upload do update.zip e de um version.json como assets da release.
       version.json deve conter: {"version": "1.1", "notes": "O que mudou"}
    6. Publique. As outras máquinas verão a novidade na próxima abertura.
"""

import os
import sys
import json
import threading
import subprocess
import tempfile
import urllib.request
import urllib.error
from tkinter import messagebox

# ══════════════════════════════════════════════════════════════════════════════ #
#   ▶  CONFIGURE AQUI                                                           #
# ══════════════════════════════════════════════════════════════════════════════ #

GITHUB_USER  = "pliskin15"       # ← troque pelo seu usuário GitHub
GITHUB_REPO  = "contab"      # ← troque pelo nome do repositório
VERSAO_ATUAL = "1.0"               # ← atualize a cada release

# ══════════════════════════════════════════════════════════════════════════════ #

_API_LATEST  = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
_TIMEOUT     = 8   # segundos para requisições HTTP


def verificar_update(root_window):
    """
    Ponto de entrada principal. Chame com root_window = sua janela tk.Tk.
    Roda em thread separada para não travar a UI.
    """
    t = threading.Thread(target=_checar, args=(root_window,), daemon=True)
    t.start()


# ── Lógica interna ────────────────────────────────────────────────────────── #

def _checar(root):
    """Consulta a API do GitHub e decide se há update."""
    try:
        info = _buscar_release_info()
    except Exception:
        return  # sem internet ou erro de rede — ignora silenciosamente

    versao_remota = info.get("version", "")
    notes         = info.get("notes", "")
    zip_url       = info.get("zip_url", "")

    if not versao_remota or not zip_url:
        return

    if not _versao_maior(versao_remota, VERSAO_ATUAL):
        return  # já está na versão mais recente

    # Pergunta ao usuário na thread principal (tkinter não é thread-safe)
    root.after(0, lambda: _perguntar_update(root, versao_remota, notes, zip_url))


def _buscar_release_info() -> dict:
    """
    Consulta a release mais recente no GitHub e retorna:
      {"version": "x.y", "notes": "...", "zip_url": "https://..."}
    """
    req = urllib.request.Request(
        _API_LATEST,
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": "auto-updater/1.0"}
    )
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        data = json.loads(resp.read().decode())

    tag     = data.get("tag_name", "").lstrip("v")
    notes   = data.get("body", "")
    assets  = data.get("assets", [])

    zip_url = ""
    for asset in assets:
        if asset.get("name", "").lower() == "update.zip":
            zip_url = asset["browser_download_url"]
            break

    return {"version": tag, "notes": notes, "zip_url": zip_url}


def _perguntar_update(root, versao_nova: str, notes: str, zip_url: str):
    """Exibe diálogo de confirmação e, se aceito, inicia o download."""
    msg = (
        f"Nova versão disponível: v{versao_nova}\n"
        f"Versão atual: v{VERSAO_ATUAL}\n"
    )
    if notes:
        msg += f"\nO que há de novo:\n{notes}\n"
    msg += "\nDeseja atualizar agora?"

    resposta = messagebox.askyesno("Atualização disponível", msg, parent=root)
    if not resposta:
        return

    # Mostra janela de progresso e baixa em thread
    _janela_progresso(root, versao_nova, zip_url)


def _janela_progresso(root, versao_nova: str, zip_url: str):
    """Janela modal simples de progresso durante o download."""
    import tkinter as tk
    from tkinter import ttk

    win = tk.Toplevel(root)
    win.title("Atualizando…")
    win.geometry("360x110")
    win.resizable(False, False)
    win.grab_set()
    win.protocol("WM_DELETE_WINDOW", lambda: None)  # impede fechar durante download

    try:
        import ui_theme as theme
        win.configure(bg=theme.BG_APP)
    except Exception:
        pass

    tk.Label(win, text=f"Baixando v{versao_nova}…",
             font=("Segoe UI", 11)).pack(pady=(18, 6))

    bar = ttk.Progressbar(win, mode="indeterminate", length=300)
    bar.pack()
    bar.start(12)

    lbl_status = tk.Label(win, text="Conectando…", font=("Segoe UI", 9))
    lbl_status.pack(pady=(6, 0))

    def _atualizar_status(txt):
        try:
            lbl_status.config(text=txt)
        except Exception:
            pass

    def _thread_download():
        try:
            zip_path = _baixar_zip(zip_url, lambda t: root.after(0, lambda: _atualizar_status(t)))
        except Exception as e:
            root.after(0, lambda: _erro_download(win, str(e)))
            return
        root.after(0, lambda: _aplicar_update(root, win, zip_path))

    threading.Thread(target=_thread_download, daemon=True).start()


def _baixar_zip(url: str, on_status) -> str:
    """Baixa o update.zip para um arquivo temporário e retorna o caminho."""
    on_status("Baixando atualização…")
    tmp = tempfile.mktemp(suffix=".zip", prefix="update_")

    req = urllib.request.Request(url, headers={"User-Agent": "auto-updater/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(tmp, "wb") as f:
        total = int(resp.headers.get("Content-Length", 0))
        baixado = 0
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
            baixado += len(chunk)
            if total:
                pct = int(baixado / total * 100)
                on_status(f"Baixando… {pct}%")

    on_status("Download concluído.")
    return tmp


def _aplicar_update(root, progress_win, zip_path: str):
    """Fecha o programa e chama o updater.exe para aplicar o update."""
    progress_win.destroy()

    install_dir = _diretorio_instalacao()
    updater_exe = os.path.join(install_dir, "updater.exe")

    if not os.path.exists(updater_exe):
        messagebox.showerror(
            "Updater não encontrado",
            f"O arquivo 'updater.exe' não foi encontrado em:\n{install_dir}\n\n"
            "Certifique-se de que 'updater.exe' está na mesma pasta que 'menu_principal.exe'.",
            parent=root,
        )
        return

    pid = os.getpid()
    subprocess.Popen(
        [updater_exe, zip_path, install_dir, str(pid)],
        cwd=install_dir,
        creationflags=0x00000008,  # DETACHED_PROCESS — continua após fechar o pai
    )
    root.destroy()


def _erro_download(progress_win, erro: str):
    progress_win.destroy()
    messagebox.showerror("Erro no download",
                         f"Não foi possível baixar a atualização:\n{erro}")


def _diretorio_instalacao() -> str:
    """Retorna o diretório onde o .exe (ou .py) está rodando."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _versao_maior(remota: str, local: str) -> bool:
    """Compara versões no formato 'X.Y.Z'. Retorna True se remota > local."""
    def _parse(v):
        try:
            return tuple(int(x) for x in str(v).strip().split("."))
        except Exception:
            return (0,)
    return _parse(remota) > _parse(local)