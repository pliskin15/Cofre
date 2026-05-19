"""
menu_principal.py
Menu geral do sistema — ponto de entrada principal.

Comportamento:
  • Exibe cards para cada módulo disponível.
  • Ao abrir um módulo, esta janela se oculta (withdraw).
  • Quando o módulo for fechado, esta janela reaparece (deiconify).
  • Adicione novos módulos em MODULES sem mexer no resto.
"""

import tkinter as tk
from tkinter import ttk
import ui_theme as theme
from lojas import _open_lojas
from menu import MenuPrincipal as _MenuConciliador   # alias para evitar conflito com a classe local

# ── Registro de módulos ────────────────────────────────────────────────────── #
# Cada entrada: (emoji, título, subtítulo, factory)
# factory(root, on_close) -> deve criar e retornar uma tk.Toplevel
# Adicione quantas entradas quiser aqui.
def _open_cofre(root: tk.Tk, on_close):
    """Abre o Sistema de Cofre como Toplevel."""
    from main import CofreApp          # importação local para evitar ciclos

    win = tk.Toplevel(root)
    win.title("")
    win.geometry("960x600")
    win.minsize(800, 520)
    win.resizable(True, True)

    # Aplica o mesmo tema
    win.configure(bg=theme.BG_APP)
    theme.apply_theme(win)

    # Injeta o conteúdo do CofreApp dentro desta Toplevel
    # Reutilizamos a lógica sem instanciar outro tk.Tk
    app_frame = _CofreFrame(win)
    app_frame.pack(fill="both", expand=True)

    # Centraliza
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    x = (win.winfo_screenwidth()  - w) // 2
    y = (win.winfo_screenheight() - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

    win.protocol("WM_DELETE_WINDOW", lambda: on_close(win))
    return win


def _open_conciliador(root: tk.Tk, on_close):
    """Abre o MenuPrincipal de menu.py como Toplevel."""
    win = tk.Toplevel(root)
    win.title("Conciliador")
    win.geometry("560x440")
    win.resizable(False, False)

    # Injeta o MenuPrincipal do menu.py dentro desta Toplevel
    _MenuConciliador(win)

    # Centraliza
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    x = (win.winfo_screenwidth()  - w) // 2
    y = (win.winfo_screenheight() - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

    win.protocol("WM_DELETE_WINDOW", lambda: on_close(win))
    return win


MODULES = [
    {
        "emoji": "🏦",
        "title": "Cofre",
        "subtitle": "Painel do Cofre - Prossegur e Brinks",
        "factory": _open_cofre,
    },
    {
        "emoji": "🏪",
        "title": "Vendas GOODCARD",
        "subtitle": "Conciliador para as vendas GOODCARD",
        "factory": _open_lojas,
    },
    {
        "emoji": "💳",
        "title": "Conciliador",
        "subtitle": "Conciliação para as vendas GETNET e PIX QRS",
        "factory": _open_conciliador,
    },    
    # Exemplo de como adicionar futuros módulos:
    # {
    #     "emoji": "📦",
    #     "title": "Outro Módulo",
    #     "subtitle": "Descrição breve do módulo",
    #     "factory": _open_outro,
    # },
]


# ── Frame reutilizável do CofreApp ─────────────────────────────────────────── #
class _CofreFrame(tk.Frame):
    """
    Replica toda a UI do CofreApp dentro de um Frame comum,
    permitindo embuti-lo numa Toplevel em vez de um tk.Tk separado.
    """

    def __init__(self, master):
        super().__init__(master, bg=theme.BG_APP)

        import json, os
        from tkinter import filedialog, messagebox

        # imports dos módulos do cofre
        try:
            from brinks_depositos   import BrinksDepositos
            from brinks_creditos    import BrinksCreditos
            from brinks_painel      import BrinksPainel
            from prossegur_depositos import ProssegurDepositos
            from prossegur_creditos  import ProssegurCreditos
            from prossegur_painel    import ProssegurPainel
        except ImportError:
            BrinksDepositos = BrinksCreditos = BrinksPainel = None
            ProssegurDepositos = ProssegurCreditos = ProssegurPainel = None

        self._json = json
        self._os   = os
        self._fd   = filedialog
        self._mb   = messagebox

        self._mods = {
            ("Prossegur", "Painel"):    ProssegurPainel,
            ("Prossegur", "Depósitos"): ProssegurDepositos,
            ("Prossegur", "Créditos"):  ProssegurCreditos,
            ("Brinks",    "Painel"):    BrinksPainel,
            ("Brinks",    "Depósitos"): BrinksDepositos,
            ("Brinks",    "Créditos"):  BrinksCreditos,
        }

        MAPA_JSON = os.path.join(os.path.dirname(__file__), "codigos_cofres.json")
        self._MAPA_JSON = MAPA_JSON

        self._palette = theme.apply_theme(master)
        self._build_ui()

    # ── Layout (idêntico ao CofreApp._build_ui) ── #
    def _build_ui(self):
        toolbar = ttk.Frame(self, style="Toolbar.TFrame", height=52)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        ttk.Label(toolbar, text="🏦 Cofre",
                  style="Toolbar.TLabel",
                  font=("Segoe UI Semibold", 14)).pack(side="left", padx=20, pady=10)

        ttk.Label(toolbar, text="v1.0", style="Toolbar.TLabel",
                  font=("Segoe UI", 10)).pack(side="right", padx=20)

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        body = ttk.Frame(self, style="App.TFrame")
        body.pack(fill="both", expand=True)

        self._sidebar = ttk.Frame(body, style="Card.TFrame", width=220)
        self._sidebar.pack(fill="y", side="left")
        self._sidebar.pack_propagate(False)

        self._content = ttk.Frame(body, style="App.TFrame")
        self._content.pack(fill="both", expand=True, side="left")

        status_bar = ttk.Frame(self, style="Status.TFrame", height=26)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        self._status_var = tk.StringVar(value="Pronto.")
        tk.Label(status_bar, textvariable=self._status_var,
                 bg="#0b1a29", fg=theme.FG_MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=12, pady=4)

        self._build_sidebar()
        self._go_home()

    def _build_sidebar(self):
        pad_s = {"padx": 16, "pady": (18, 4)}
        pad_b = {"padx": 10, "pady": 2, "fill": "x"}

        self._active_btn = None
        self._home_btn   = None

        self._home_btn = self._nav_btn(
            self._sidebar, "🏠  Início", self._go_home,
            padx=10, pady=(10, 2), fill="x")

        ttk.Separator(self._sidebar, orient="horizontal").pack(
            fill="x", padx=16, pady=(10, 0))

        self._section_label(self._sidebar, "PROSSEGUR", **pad_s)
        for label, mod in [("📊  Painel", "Painel"),
                            ("💰  Depósitos", "Depósitos"),
                            ("📋  Créditos",  "Créditos")]:
            self._nav_btn(self._sidebar, label,
                          lambda m=mod: self._open_module("Prossegur", m), **pad_b)

        ttk.Separator(self._sidebar, orient="horizontal").pack(
            fill="x", padx=16, pady=14)

        self._section_label(self._sidebar, "BRINKS", padx=16, pady=(2, 4))
        for label, mod in [("📊  Painel", "Painel"),
                            ("💰  Depósitos", "Depósitos"),
                            ("📋  Créditos",  "Créditos")]:
            self._nav_btn(self._sidebar, label,
                          lambda m=mod: self._open_module("Brinks", m), **pad_b)

        spacer = ttk.Frame(self._sidebar, style="Card.TFrame")
        spacer.pack(fill="both", expand=True)

        ttk.Separator(self._sidebar, orient="horizontal").pack(fill="x", padx=16)

        self._nav_btn(self._sidebar, "📤  Exportar Mapeamento",
                      self._exportar_mapeamento,
                      padx=10, pady=(6, 2), fill="x")
        self._nav_btn(self._sidebar, "⚙️  Configurações",
                      lambda: self._open_module("Sistema", "Configurações"),
                      padx=10, pady=(2, 10), fill="x")

    def _section_label(self, parent, text, **pack_opts):
        ttk.Label(parent, text=text,
                  background=theme.CARD_BG, foreground=theme.FG_MUTED,
                  font=("Segoe UI Semibold", 9)).pack(anchor="w", **pack_opts)

    def _nav_btn(self, parent, text, command, **pack_opts):
        btn = tk.Button(parent, text=text,
                        bg=theme.CARD_BG, fg=theme.FG_TEXT,
                        activebackground="#164a79", activeforeground="white",
                        relief="flat", bd=0, cursor="hand2",
                        anchor="w", padx=12, pady=7,
                        font=("Segoe UI", 11))
        btn.pack(**pack_opts)
        btn.configure(command=lambda b=btn, c=command: self._nav_click(b, c))
        btn.bind("<Enter>", lambda e, b=btn: self._btn_hover(b, True))
        btn.bind("<Leave>", lambda e, b=btn: self._btn_hover(b, False))
        return btn

    def _btn_hover(self, btn, entering):
        if btn is self._active_btn:
            return
        btn.configure(bg="#122538" if entering else theme.CARD_BG)

    def _nav_click(self, btn, command):
        if self._active_btn:
            self._active_btn.configure(bg=theme.CARD_BG, fg=theme.FG_TEXT)
        self._active_btn = btn
        if btn:
            btn.configure(bg=theme.PRIMARY, fg="white")
        command()

    def _clear_content(self):
        for w in self._content.winfo_children():
            w.destroy()

    def _go_home(self):
        if self._active_btn and self._active_btn is not self._home_btn:
            self._active_btn.configure(bg=theme.CARD_BG, fg=theme.FG_TEXT)
        self._active_btn = self._home_btn
        if self._home_btn:
            self._home_btn.configure(bg=theme.PRIMARY, fg="white")
        self._show_home()

    def _show_home(self):
        self._clear_content()
        self._status_var.set("Início")
        frame = ttk.Frame(self._content, style="App.TFrame")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(frame, text="🏦", background=theme.BG_APP,
                  foreground=theme.FG_TEXT, font=("Segoe UI", 48)).pack()
        ttk.Label(frame, text="Cofre", style="Title.TLabel",
                  font=("Segoe UI", 22, "bold")).pack(pady=(8, 4))
        ttk.Label(frame, text="Selecione um módulo no menu lateral para começar.",
                  style="Muted.TLabel", font=("Segoe UI", 11)).pack()

    def _open_module(self, empresa: str, modulo: str):
        self._clear_content()
        self._status_var.set(f"{empresa}  ›  {modulo}")

        cor_empresa = theme.PRIMARY if empresa == "Prossegur" else "#b8860b"

        header = ttk.Frame(self._content, style="Card.TFrame")
        header.pack(fill="x")
        tk.Label(header, text=f"  {empresa}  ›  {modulo}",
                 bg=theme.CARD_BG, fg=theme.FG_TEXT,
                 font=("Segoe UI Semibold", 13), pady=12, anchor="w"
                 ).pack(fill="x", padx=8)
        tk.Frame(header, bg=cor_empresa, height=3).pack(fill="x")

        area = ttk.Frame(self._content, style="App.TFrame")
        area.pack(fill="both", expand=True)

        cls = self._mods.get((empresa, modulo))
        if cls:
            cls(area).pack(fill="both", expand=True)
            return

        ttk.Label(area, text=f"Módulo  {modulo}  —  {empresa}",
                  style="Muted.TLabel", font=("Segoe UI", 12)
                  ).place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(area, text="(implementação em breve)",
                  style="Muted.TLabel", font=("Segoe UI", 10)
                  ).place(relx=0.5, rely=0.56, anchor="center")

    def _exportar_mapeamento(self):
        xlsx_path = self._fd.askopenfilename(
            title="Selecionar planilha de cofres",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")])
        if not xlsx_path:
            return
        try:
            import pandas as pd
            df = pd.read_excel(xlsx_path, dtype=str)
            df.columns = [c.strip() for c in df.columns]
            required = {"UF", "LOJA", "NOME", "COFRE"}
            missing = required - set(df.columns)
            if missing:
                self._mb.showerror(
                    "Colunas não encontradas",
                    f"A planilha não contém: {', '.join(missing)}\n"
                    f"Colunas encontradas: {', '.join(df.columns)}")
                return
            lojas, brinks_map, prossegur_map = [], {}, {}
            for _, row in df.iterrows():
                uf    = str(row["UF"]).strip()
                loja  = str(row["LOJA"]).strip()
                nome  = str(row["NOME"]).strip()
                cofre = str(row["COFRE"]).strip()
                lojas.append({"uf": uf, "loja": loja, "nome": nome, "cofre": cofre})
                brinks_map[cofre] = loja
                prossegur_map.setdefault(nome, [])
                if loja not in prossegur_map[nome]:
                    prossegur_map[nome].append(loja)
            output = {"lojas": lojas, "brinks_map": brinks_map, "prossegur_map": prossegur_map}
            with open(self._MAPA_JSON, "w", encoding="utf-8") as f:
                self._json.dump(output, f, ensure_ascii=False, indent=2)
            self._status_var.set(
                f"Mapeamento exportado  —  {len(lojas)} lojas  "
                f"({len(brinks_map)} cofres Brinks, {len(prossegur_map)} nomes Prossegur)")
            self._mb.showinfo(
                "Exportação concluída",
                f"JSON gerado com sucesso!\n\n"
                f"  Lojas:            {len(lojas)}\n"
                f"  Cofres Brinks:    {len(brinks_map)}\n"
                f"  Nomes Prossegur:  {len(prossegur_map)}\n\n"
                f"Arquivo: {self._MAPA_JSON}")
        except Exception as exc:
            self._mb.showerror("Erro na exportação", str(exc))


# ── Menu Principal ─────────────────────────────────────────────────────────── #
class MenuPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("")
        self.geometry("720x480")
        self.minsize(600, 400)
        self.resizable(True, True)

        self.palette = theme.apply_theme(self)
        self._build_ui()
        self._center()

        # ✅ ADICIONAR ISSO:
        from auto_update import verificar_update
        self.after(1500, lambda: verificar_update(self))

    # ── Layout ── #
    def _build_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self, style="Toolbar.TFrame", height=56)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        ttk.Label(toolbar, text="⚙️  Menu Principal",
                  style="Toolbar.TLabel",
                  font=("Segoe UI Semibold", 15)).pack(side="left", padx=20, pady=12)

        ttk.Label(toolbar, text="v1.0", style="Toolbar.TLabel",
                  font=("Segoe UI", 10)).pack(side="right", padx=20)

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # Corpo rolável
        body = ttk.Frame(self, style="App.TFrame")
        body.pack(fill="both", expand=True, padx=32, pady=24)

        ttk.Label(body, text="Selecione um módulo para abrir:",
                  style="Muted.TLabel",
                  font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 16))

        # Grid de cards
        grid = ttk.Frame(body, style="App.TFrame")
        grid.pack(fill="both", expand=True)

        cols = 3  # cards por linha
        for i, mod in enumerate(MODULES):
            row, col = divmod(i, cols)
            card = self._make_card(grid, mod)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        for c in range(cols):
            grid.columnconfigure(c, weight=1)

        # Status bar
        status = ttk.Frame(self, style="Status.TFrame", height=26)
        status.pack(fill="x", side="bottom")
        status.pack_propagate(False)

        self._status_var = tk.StringVar(value="Pronto.")
        tk.Label(status, textvariable=self._status_var,
                 bg="#0b1a29", fg=theme.FG_MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=12, pady=4)

    def _make_card(self, parent, mod: dict) -> tk.Frame:
        """Cria um card clicável para um módulo."""
        card = tk.Frame(parent, bg=theme.CARD_BG, cursor="hand2",
                        relief="flat", bd=0)

        # Borda colorida no topo
        tk.Frame(card, bg=theme.PRIMARY, height=3).pack(fill="x")

        inner = tk.Frame(card, bg=theme.CARD_BG, padx=18, pady=14)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text=mod["emoji"],
                 bg=theme.CARD_BG, fg=theme.FG_TEXT,
                 font=("Segoe UI", 28)).pack(anchor="w")

        tk.Label(inner, text=mod["title"],
                 bg=theme.CARD_BG, fg=theme.FG_TEXT,
                 font=("Segoe UI Semibold", 12), wraplength=180,
                 justify="left").pack(anchor="w", pady=(6, 2))

        tk.Label(inner, text=mod["subtitle"],
                 bg=theme.CARD_BG, fg=theme.FG_MUTED,
                 font=("Segoe UI", 9), wraplength=180,
                 justify="left").pack(anchor="w")

        # Hover e clique
        def _enter(e, c=card, i=inner):
            for w in [c, i] + i.winfo_children():
                try:
                    w.configure(bg="#122538")
                except Exception:
                    pass

        def _leave(e, c=card, i=inner):
            for w in [c, i] + i.winfo_children():
                try:
                    w.configure(bg=theme.CARD_BG)
                except Exception:
                    pass

        def _click(e=None, m=mod):
            self._launch(m)

        for w in [card, inner] + inner.winfo_children():
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)
            w.bind("<Button-1>", _click)

        return card

    # ── Lógica de abertura/fechamento ── #
    def _launch(self, mod: dict):
        """Oculta o menu, abre o módulo; ao fechar o módulo, reaparece."""
        self._status_var.set(f"Abrindo  {mod['title']}…")
        self.withdraw()

        def on_close(win: tk.Toplevel):
            win.destroy()
            self.deiconify()
            self._status_var.set("Pronto.")

        win = mod["factory"](self, on_close)
        # Garante que fechar via X também reaparece (já setado em factory,
        # mas protege contra factories que esqueçam)
        win.protocol("WM_DELETE_WINDOW", lambda w=win: on_close(w))

    # ── Utilitários ── #
    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")


if __name__ == "__main__":
    app = MenuPrincipal()
    app.mainloop()