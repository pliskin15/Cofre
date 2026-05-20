
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
from theme import (
    T, aplicar_estilos_ttk, botao_tema,
    registrar_callback, recolorir_widget, tema_atual,
)

# Imports estáticos — necessário para o PyInstaller empacotar os módulos
from Conciliacao_Cartao import Conciliacao_Cartao as _fn_Conciliacao_Cartao
from Conciliacao_PixMaquineta import Conciliacao_PixMaquineta as _fn_Conciliacao_PixMaquineta
from pixqrs import Conciliacao_Pix as _fn_Conciliacao_Pix

_MODULOS = [
    {
        "titulo":    "Conciliação Cartões",
        "subtitulo": "Débito / Crédito — Getnet",
        "icone":     "💳",
        "funcao":    _fn_Conciliacao_Cartao,
        "cor_acento":"AZUL",
    },
    {
        "titulo":    "Conciliação PIX Maquineta",
        "subtitulo": "PIX via terminal Getnet",
        "icone":     "📲",
        "funcao":    _fn_Conciliacao_PixMaquineta,
        "cor_acento":"VERDE",
    },
    {
        "titulo":    "Conciliação PIX QrCode",
        "subtitulo": "PIX via QrCode",
        "icone":     "📲",
        "funcao":    _fn_Conciliacao_Pix,
        "cor_acento":"AMARELO",
    },
]

def _abrir_modulo(mod_info: dict, master: tk.Tk) -> None:
<<<<<<< Updated upstream
    nome_mod  = mod_info["modulo"]
    nome_func = mod_info["funcao"]
    try:
        if nome_mod == "Conciliacao_Cartao":
            from Conciliacao_Cartao import Conciliacao_Cartao as func
        elif nome_mod == "Conciliacao_PixMaquineta":
            from Conciliacao_PixMaquineta import Conciliacao_PixMaquineta as func
        elif nome_mod == "pixqrs":
            from pixqrs import Conciliacao_Pix as func
        else:
            raise ModuleNotFoundError(nome_mod)
        func(master)
    except ModuleNotFoundError:
        messagebox.showerror(
            "Módulo não encontrado",
            f"O arquivo '{nome_mod}.py' não foi encontrado.\n"
            f"Verifique se ele está na mesma pasta que menu.py.",
        )
=======
    """Chama a função de abertura do módulo."""
    try:
        mod_info["funcao"](master)
>>>>>>> Stashed changes
    except Exception:
        messagebox.showerror(
            "Erro ao abrir módulo",
            f"Ocorreu um erro ao abrir '{mod_info['titulo']}':\n\n"
            + traceback.format_exc(),
        )
class CardModulo(tk.Frame):

    def __init__(self, parent, mod_info: dict, master_root: tk.Tk, **kwargs):
        super().__init__(parent, **kwargs)
        self._mod      = mod_info
        self._win_root = master_root
        self._build()
        self._bind_hover()

    def _build(self):
        self.config(
            bg=T("PAINEL"),
            relief="flat",
            bd=0,
            padx=16,
            pady=14,
            cursor="hand2",
        )

        topo = tk.Frame(self, bg=T("PAINEL"))
        topo.pack(fill="x")

        tk.Label(
            topo,
            text=self._mod["icone"],
            font=("Segoe UI", 22),
            bg=T("PAINEL"),
            fg=T(self._mod["cor_acento"]),
        ).pack(side="left", padx=(0, 10))

        titulo_frame = tk.Frame(topo, bg=T("PAINEL"))
        titulo_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            titulo_frame,
            text=self._mod["titulo"],
            font=("Segoe UI", 11, "bold"),
            bg=T("PAINEL"),
            fg=T("ACENTO"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            titulo_frame,
            text=self._mod["subtitulo"],
            font=("Segoe UI", 8),
            bg=T("PAINEL"),
            fg=T("TEXTO_SEC"),
            anchor="w",
        ).pack(fill="x")

        sep = tk.Frame(self, bg=T(self._mod["cor_acento"]), height=2)
        sep.pack(fill="x", pady=(10, 0))

        self._todos = [self, topo, titulo_frame, sep] + list(topo.winfo_children()) + list(titulo_frame.winfo_children())

    def _bind_hover(self):
        for w in self._todos:
            w.bind("<Enter>",   self._on_enter)
            w.bind("<Leave>",   self._on_leave)
            w.bind("<Button-1>",self._on_click)

    def _on_enter(self, _e=None):
        for w in self._todos:
            try:
                w.config(bg=T("BORDA"))
            except Exception:
                pass

    def _on_leave(self, _e=None):
        for w in self._todos:
            try:
                w.config(bg=T("PAINEL"))
            except Exception:
                pass

    def _on_click(self, _e=None):
        _abrir_modulo(self._mod, self._win_root)

    def reaplicar_tema(self):
        for child in self.winfo_children():
            child.destroy()
        self._build()
        self._bind_hover()
        self.config(bg=T("PAINEL"))

class MenuPrincipal:

    def __init__(self, root: tk.Tk):
        self._win   = root
        self._cards: list[CardModulo] = []
        self._style = ttk.Style(root)

        self._configurar_janela()
        self._build()
        registrar_callback(self._reaplicar_tema)
        aplicar_estilos_ttk(self._style)

    def _configurar_janela(self):
        self._win.title("")
        self._win.geometry("560x440")
        self._win.resizable(False, False)
        self._win.configure(bg=T("BG"))

        self._win.update_idletasks()
        w = self._win.winfo_width()
        h = self._win.winfo_height()
        x = (self._win.winfo_screenwidth()  - w) // 2
        y = (self._win.winfo_screenheight() - h) // 2
        self._win.geometry(f"+{x}+{y}")

    def _build(self):
        self._topbar = tk.Frame(self._win, bg=T("PAINEL"), pady=10)
        self._topbar.pack(fill="x")

        tk.Label(
            self._topbar,
            text="Conciliador",
            font=("Segoe UI", 13, "bold"),
            bg=T("PAINEL"),
            fg=T("ACENTO"),
        ).pack(side="left", padx=16)

        self._btn_tema = botao_tema(self._topbar)
        self._btn_tema.pack(side="right", padx=12)

        self._lbl_sub = tk.Label(
            self._win,
            text="Selecione uma conciliação para abrir",
            font=("Segoe UI", 9),
            bg=T("BG"),
            fg=T("TEXTO_SEC"),
        )
        self._lbl_sub.pack(pady=(14, 6))

        self._frame_cards = tk.Frame(self._win, bg=T("BG"))
        self._frame_cards.pack(fill="both", expand=True, padx=24, pady=6)

        self._montar_cards()

        self._rodape = tk.Frame(self._win, bg=T("PAINEL"), pady=6)
        self._rodape.pack(fill="x", side="bottom")

        self._lbl_rodape = tk.Label(
            self._rodape,
            text="v.1.0",
            font=("Segoe UI", 7),
            bg=T("PAINEL"),
            fg=T("TEXTO_SEC"),
        )
        self._lbl_rodape.pack()

    def _montar_cards(self):
        for child in self._frame_cards.winfo_children():
            child.destroy()
        self._cards.clear()

        for i, mod in enumerate(_MODULOS):
            card = CardModulo(
                self._frame_cards,
                mod_info=mod,
                master_root=self._win,
            )
            card.pack(fill="x", pady=5)
            self._cards.append(card)

    def _reaplicar_tema(self):
        aplicar_estilos_ttk(self._style)
        self._win.configure(bg=T("BG"))

        self._topbar.config(bg=T("PAINEL"))
        for w in self._topbar.winfo_children():
            try:
                w.config(bg=T("PAINEL"), fg=T("ACENTO"))
            except Exception:
                pass

        try:
            self._btn_tema.config(bg=T("BORDA"), fg=T("TEXTO"))
        except Exception:
            pass

        self._lbl_sub.config(bg=T("BG"), fg=T("TEXTO_SEC"))
        self._frame_cards.config(bg=T("BG"))

        self._rodape.config(bg=T("PAINEL"))
        self._lbl_rodape.config(bg=T("PAINEL"), fg=T("TEXTO_SEC"))

        for card in self._cards:
            card.reaplicar_tema()

def main():
    root = tk.Tk()
    MenuPrincipal(root)
    root.mainloop()

if __name__ == "__main__":
    main()
