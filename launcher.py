"""
launcher.py — Cofre
Compilar: pyinstaller --onefile --noconsole --name launcher launcher.py
"""

import hashlib, json, os, sys, threading, time, subprocess
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import quote
import tkinter as tk
from tkinter import ttk, messagebox

MANIFEST_URL = "https://raw.githubusercontent.com/pliskin15/Cofre/updates/updates/latest/version.json"
APP_EXE      = "Cofre.exe"
AUTH_TOKEN   = ""
EXCLUDE      = {"launcher.exe", "updater_config.json", "version.txt"}

def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b: break
            h.update(b)
    return h.hexdigest()

def atomic_replace(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    os.replace(src, dst)

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cofre — Atualizador")
        self.geometry("480x200")
        self.resizable(False, False)
        self._center()
        self.configure(bg="#0d1b2a")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TProgressbar", troughcolor="#1e2e3e", background="#1a8cff", thickness=12)

        tk.Label(self, text="Cofre — Verificando atualizacoes",
                 bg="#0d1b2a", fg="#ffffff",
                 font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=16, pady=(14, 4))

        ttk.Separator(self).pack(fill="x", padx=16)

        self.lbl = tk.Label(self, text="Conectando...", bg="#0d1b2a", fg="#a0b8d0",
                            font=("Segoe UI", 9), anchor="w")
        self.lbl.pack(fill="x", padx=16, pady=(10, 2))

        self.pb_total = ttk.Progressbar(self, orient="horizontal", mode="determinate", length=448)
        self.pb_total.pack(padx=16, pady=(2, 0))
        self.lbl_total = tk.Label(self, text="0%", bg="#0d1b2a", fg="#708090",
                                  font=("Segoe UI", 8), anchor="e")
        self.lbl_total.pack(fill="x", padx=16)

        self.pb_file = ttk.Progressbar(self, orient="horizontal", mode="determinate", length=448)
        self.pb_file.pack(padx=16, pady=(4, 0))
        self.lbl_file = tk.Label(self, text="", bg="#0d1b2a", fg="#708090",
                                 font=("Segoe UI", 8), anchor="w")
        self.lbl_file.pack(fill="x", padx=16)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 480) // 2
        y = (self.winfo_screenheight() - 200) // 2
        self.geometry(f"480x200+{x}+{y}")

    def _on_close(self):
        if self._thread.is_alive():
            messagebox.showinfo("Aguarde", "Atualizacao em andamento.")
        else:
            self.destroy()

    def _status(self, txt):
        self.lbl.config(text=txt)
        self.update_idletasks()

    def _set_total(self, cur, total):
        self.pb_total["maximum"] = max(total, 1)
        self.pb_total["value"]   = cur
        self.lbl_total.config(text=f"{0 if total==0 else int(cur/total*100)}%")
        self.update_idletasks()

    def _set_file(self, cur, total, name=""):
        self.pb_file["maximum"] = max(total, 1)
        self.pb_file["value"]   = cur
        pct = 0 if total == 0 else int(cur / total * 100)
        self.lbl_file.config(text=f"{Path(name).name}  ({pct}%)" if name else "")
        self.update_idletasks()

    def _req(self, url):
        r = Request(url, headers={"User-Agent": "cofre-launcher/1.0"})
        if AUTH_TOKEN:
            r.add_header("Authorization", f"token {AUTH_TOKEN}")
        return r

    def _get_json(self, url):
        with urlopen(self._req(url), timeout=20) as resp:
            return json.loads(resp.read().decode())

    def _download(self, url, dst: Path, size: int) -> Path:
        tmp = dst.with_suffix(dst.suffix + ".tmp")
        dst.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(self._req(url), timeout=90) as resp, tmp.open("wb") as f:
            baixado = 0
            while True:
                chunk = resp.read(256 * 1024)
                if not chunk: break
                f.write(chunk)
                baixado += len(chunk)
                self._set_file(baixado, size, dst.name)
        return tmp

    def _run(self):
        root = app_dir()

        # 1. Baixar manifesto
        self._status("Verificando atualizacoes...")
        try:
            manifest = self._get_json(MANIFEST_URL)
        except Exception as e:
            self._status("Sem conexao — abrindo versao atual.")
            time.sleep(1)
            self._launch()
            return

        base_url = manifest.get("base_url", "")
        files    = manifest.get("files", {})

        # 2. Descobrir o que precisa baixar
        to_update   = []
        total_bytes = 0
        for rel, meta in files.items():
            if Path(rel).name in EXCLUDE:
                continue
            target = root / rel
            need   = True
            if target.exists():
                try:
                    need = sha256_file(target) != meta["sha256"]
                except Exception:
                    need = True
            if need:
                to_update.append((rel, meta))
                total_bytes += int(meta.get("size", 0))

        if not to_update:
            self._status("Tudo atualizado!")
            time.sleep(0.5)
            self._launch()
            return

        # 3. Baixar TODOS para arquivos temporarios primeiro
        self._status(f"Baixando {len(to_update)} arquivo(s)...")
        self._set_total(0, total_bytes)
        baixado_total = 0
        tmps = []  # lista de (tmp_path, dst_path)

        for rel, meta in to_update:
            url  = f"{base_url}/{quote(rel.replace(chr(92), '/'))}"
            dst  = root / rel
            size = int(meta.get("size", 0))
            self._status(f"Baixando: {Path(rel).name}")
            try:
                tmp = self._download(url, dst, size)
                if sha256_file(tmp) != meta["sha256"]:
                    tmp.unlink(missing_ok=True)
                    for t, _ in tmps:
                        try: t.unlink(missing_ok=True)
                        except: pass
                    self.after(0, lambda: messagebox.showerror(
                        "Erro", "Falha na verificacao de integridade.\nTente novamente."))
                    self.after(0, self.destroy)
                    return
                tmps.append((tmp, dst))
            except Exception as e:
                for t, _ in tmps:
                    try: t.unlink(missing_ok=True)
                    except: pass
                self.after(0, lambda err=e: messagebox.showerror(
                    "Erro", f"Falha ao baixar arquivo:\n{err}"))
                self.after(0, self.destroy)
                return

            baixado_total += size
            self._set_total(baixado_total, total_bytes)
            self._set_file(0, 1)

        # 4. Aplicar TODOS os arquivos de uma vez, so entao abrir o app
        self._status("Aplicando atualizacao...")
        for tmp, dst in tmps:
            try:
                atomic_replace(tmp, dst)
            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror(
                    "Erro", f"Falha ao aplicar arquivo:\n{err}"))
                self.after(0, self.destroy)
                return

        self._status("Atualizado! Abrindo o Cofre...")
        time.sleep(0.6)
        self._launch()

    def _launch(self):
        try:
            exe = app_dir() / APP_EXE
            subprocess.Popen([str(exe)], cwd=str(app_dir()))
        except Exception as e:
            messagebox.showerror("Erro", f"Nao foi possivel abrir o programa:\n{e}")
        finally:
            self.destroy()

if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    Launcher().mainloop()