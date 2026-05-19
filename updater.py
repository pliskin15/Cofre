"""
updater.py
──────────
Executável auxiliar de atualização automática.

Fluxo:
  1. Recebe como argumento o caminho do .zip baixado e o diretório de instalação.
  2. Aguarda o menu_principal.exe fechar (PID opcional como 3º argumento).
  3. Extrai o .zip por cima dos arquivos existentes.
  4. Apaga o .zip temporário.
  5. Relança o menu_principal.exe.
  6. Fecha.

Uso interno (chamado pelo menu_principal.py):
  updater.exe <zip_path> <install_dir> [pid_a_aguardar]

Compilar:
  pyinstaller --onefile --noconsole updater.py
"""

import sys
import os
import zipfile
import shutil
import time
import subprocess


def main():
    if len(sys.argv) < 3:
        print("Uso: updater.exe <zip_path> <install_dir> [pid]")
        sys.exit(1)

    zip_path    = sys.argv[1]
    install_dir = sys.argv[2]
    pid         = int(sys.argv[3]) if len(sys.argv) >= 4 else None

    # ── 1. Aguarda o processo principal fechar ──────────────────────────────── #
    if pid:
        _wait_pid(pid, timeout=30)

    # ── 2. Pequena pausa extra para o SO liberar arquivos ──────────────────── #
    time.sleep(1.5)

    # ── 3. Extrai o zip por cima do diretório de instalação ─────────────────── #
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(install_dir)
    except Exception as e:
        _msgbox_erro(f"Falha ao extrair atualização:\n{e}")
        sys.exit(1)

    # ── 4. Remove o zip temporário ──────────────────────────────────────────── #
    try:
        os.remove(zip_path)
    except Exception:
        pass  # não crítico

    # ── 5. Relança o menu_principal.exe ─────────────────────────────────────── #
    exe = os.path.join(install_dir, "menu_principal.exe")
    if not os.path.exists(exe):
        _msgbox_erro(f"Não foi possível encontrar:\n{exe}\n\nAbra o programa manualmente.")
        sys.exit(1)

    subprocess.Popen([exe], cwd=install_dir)
    sys.exit(0)


# ── Utilitários ─────────────────────────────────────────────────────────────── #

def _wait_pid(pid: int, timeout: int = 30):
    """Aguarda um processo terminar (Windows)."""
    try:
        import ctypes
        SYNCHRONIZE    = 0x00100000
        WAIT_TIMEOUT   = 0x00000102
        handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if handle:
            ctypes.windll.kernel32.WaitForSingleObject(handle, timeout * 1000)
            ctypes.windll.kernel32.CloseHandle(handle)
    except Exception:
        # Fallback: polling simples
        _wait_pid_polling(pid, timeout)


def _wait_pid_polling(pid: int, timeout: int):
    """Fallback: verifica a cada 500 ms se o PID ainda existe."""
    import ctypes
    deadline = time.time() + timeout
    while time.time() < deadline:
        handle = ctypes.windll.kernel32.OpenProcess(1, False, pid)
        if not handle:
            break
        ctypes.windll.kernel32.CloseHandle(handle)
        time.sleep(0.5)


def _msgbox_erro(msg: str):
    """Exibe um messagebox de erro sem depender de tkinter."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, "Erro na atualização", 0x10)
    except Exception:
        print(msg)


if __name__ == "__main__":
    main()