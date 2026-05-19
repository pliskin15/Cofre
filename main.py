"""
main.py
Menu principal do sistema de Cofre — Prossegur & Brinks
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import ui_theme as theme
from brinks_depositos import BrinksDepositos
from brinks_creditos import BrinksCreditos
from brinks_painel import BrinksPainel
from prossegur_depositos import ProssegurDepositos
from prossegur_creditos import ProssegurCreditos
from prossegur_painel import ProssegurPainel
# ── Arquivo de mapeamento (gerado pela exportação) ──────────────────────── #
MAPA_JSON = os.path.join(os.path.dirname(__file__), "codigos_cofres.json")


def _carregar_mapa() -> dict:
    """Carrega o JSON de mapeamento se existir, senão retorna estrutura vazia."""
    if os.path.exists(MAPA_JSON):
        with open(MAPA_JSON, encoding="utf-8") as f:
            return json.load(f)
    return {"lojas": [], "brinks_map": {}, "prossegur_map": {}}


def loja_por_cofre_brinks(cofre: str) -> str | None:
    """Retorna o nº da loja a partir do código do cofre Brinks."""
    mapa = _carregar_mapa()
    return mapa.get("brinks_map", {}).get(str(cofre).strip())


def lojas_por_nome_prossegur(nome: str) -> list[str]:
    """Retorna lista de lojas a partir do NOME do cofre Prossegur."""
    mapa = _carregar_mapa()
    return mapa.get("prossegur_map", {}).get(nome.strip(), [])


class CofreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("")
        self.geometry("960x600")
        self.minsize(800, 520)
        self.resizable(True, True)

        self.palette = theme.apply_theme(self)
        self._build_ui()
        self.center_window()

    # ------------------------------------------------------------------ #
    #  Layout principal                                                     #
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        # ── Toolbar superior ──────────────────────────────────────────── #
        toolbar = ttk.Frame(self, style="Toolbar.TFrame", height=52)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        ttk.Label(
            toolbar,
            text="🏦 Cofre",
            style="Toolbar.TLabel",
            font=("Segoe UI Semibold", 14),
        ).pack(side="left", padx=20, pady=10)

        ttk.Label(
            toolbar,
            text="v1.0",
            style="Toolbar.TLabel",
            font=("Segoe UI", 10),
        ).pack(side="right", padx=20)

        # ── Separador ─────────────────────────────────────────────────── #
        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # ── Corpo ──────────────────────────────────────────────────────── #
        body = ttk.Frame(self, style="App.TFrame")
        body.pack(fill="both", expand=True)

        self._sidebar = ttk.Frame(body, style="Card.TFrame", width=220)
        self._sidebar.pack(fill="y", side="left")
        self._sidebar.pack_propagate(False)

        self._content = ttk.Frame(body, style="App.TFrame")
        self._content.pack(fill="both", expand=True, side="left")

        # ── Status bar ────────────────────────────────────────────────── #
        status_bar = ttk.Frame(self, style="Status.TFrame", height=26)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        self._status_var = tk.StringVar(value="Pronto.")
        ttk.Label(
            status_bar,
            textvariable=self._status_var,
            background="#0b1a29",
            foreground=theme.FG_MUTED,
            font=("Segoe UI", 9),
        ).pack(side="left", padx=12, pady=4)

        self._build_sidebar()
        self._go_home()

    # ------------------------------------------------------------------ #
    #  Sidebar                                                              #
    # ------------------------------------------------------------------ #
    def _build_sidebar(self):
        pad_section = {"padx": 16, "pady": (18, 4)}
        pad_btn     = {"padx": 10, "pady": 2, "fill": "x"}

        self._active_btn = None
        self._home_btn   = None

        # ── Home ──────────────────────────────────────────────────────── #
        self._home_btn = self._nav_btn(
            self._sidebar, "🏠  Início", self._go_home,
            padx=10, pady=(10, 2), fill="x",
        )

        ttk.Separator(self._sidebar, orient="horizontal").pack(
            fill="x", padx=16, pady=(10, 0)
        )

        # ── Prossegur ─────────────────────────────────────────────────── #
        self._section_label(self._sidebar, "PROSSEGUR", **pad_section)
        for label, cmd in [
            ("📊  Painel",    lambda: self._open_module("Prossegur", "Painel")),
            ("💰  Depósitos", lambda: self._open_module("Prossegur", "Depósitos")),
            ("📋  Créditos",  lambda: self._open_module("Prossegur", "Créditos")),
        ]:
            self._nav_btn(self._sidebar, label, cmd, **pad_btn)

        ttk.Separator(self._sidebar, orient="horizontal").pack(
            fill="x", padx=16, pady=14
        )

        # ── Brinks ────────────────────────────────────────────────────── #
        self._section_label(self._sidebar, "BRINKS", padx=16, pady=(2, 4))
        for label, cmd in [
            ("📊  Painel",    lambda: self._open_module("Brinks", "Painel")),
            ("💰  Depósitos", lambda: self._open_module("Brinks", "Depósitos")),
            ("📋  Créditos",  lambda: self._open_module("Brinks", "Créditos")),
        ]:
            self._nav_btn(self._sidebar, label, cmd, **pad_btn)

        # ── Rodapé ────────────────────────────────────────────────────── #
        spacer = ttk.Frame(self._sidebar, style="Card.TFrame")
        spacer.pack(fill="both", expand=True)

        ttk.Separator(self._sidebar, orient="horizontal").pack(fill="x", padx=16)

        self._nav_btn(
            self._sidebar, "📤  Exportar Mapeamento", self._exportar_mapeamento,
            padx=10, pady=(6, 2), fill="x",
        )
        self._nav_btn(
            self._sidebar, "⚙️  Configurações",
            lambda: self._open_module("Sistema", "Configurações"),
            padx=10, pady=(2, 10), fill="x",
        )

    def _section_label(self, parent, text, **pack_opts):
        ttk.Label(
            parent, text=text,
            background=theme.CARD_BG, foreground=theme.FG_MUTED,
            font=("Segoe UI Semibold", 9),
        ).pack(anchor="w", **pack_opts)

    def _nav_btn(self, parent, text, command, **pack_opts):
        btn = tk.Button(
            parent, text=text,
            bg=theme.CARD_BG, fg=theme.FG_TEXT,
            activebackground="#164a79", activeforeground="white",
            relief="flat", bd=0, cursor="hand2",
            anchor="w", padx=12, pady=7,
            font=("Segoe UI", 11),
        )
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

    # ------------------------------------------------------------------ #
    #  Área de conteúdo                                                     #
    # ------------------------------------------------------------------ #
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

        # ── Cabeçalho ─────────────────────────────────────────────────── #
        header = ttk.Frame(self._content, style="Card.TFrame")
        header.pack(fill="x")

        tk.Label(
            header, text=f"  {empresa}  ›  {modulo}",
            bg=theme.CARD_BG, fg=theme.FG_TEXT,
            font=("Segoe UI Semibold", 13), pady=12, anchor="w",
        ).pack(fill="x", padx=8)

        tk.Frame(header, bg=cor_empresa, height=3).pack(fill="x")

        # ── Roteamento de módulos ──────────────────────────────────────── #
        area = ttk.Frame(self._content, style="App.TFrame")
        area.pack(fill="both", expand=True)

        if empresa == "Prossegur" and modulo == "Painel":
            ProssegurPainel(area).pack(fill="both", expand=True)
            return

        if empresa == "Prossegur" and modulo == "Depósitos":
            ProssegurDepositos(area).pack(fill="both", expand=True)
            return
        
        if empresa == "Prossegur" and modulo == "Créditos":
            ProssegurCreditos(area).pack(fill="both", expand=True)
            return        

        if empresa == "Brinks" and modulo == "Depósitos":
            BrinksDepositos(area).pack(fill="both", expand=True)
            return

        if empresa == "Brinks" and modulo == "Créditos":
            BrinksCreditos(area).pack(fill="both", expand=True)
            return

        if empresa == "Brinks" and modulo == "Painel":
            BrinksPainel(area).pack(fill="both", expand=True)
            return

        # Placeholder para módulos ainda não implementados
        ttk.Label(area, text=f"Módulo  {modulo}  —  {empresa}",
                  style="Muted.TLabel", font=("Segoe UI", 12),
                  ).place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(area, text="(implementação em breve)",
                  style="Muted.TLabel", font=("Segoe UI", 10),
                  ).place(relx=0.5, rely=0.56, anchor="center")

    # ------------------------------------------------------------------ #
    #  Exportar mapeamento                                                  #
    # ------------------------------------------------------------------ #
    def _exportar_mapeamento(self):
        """
        Abre diálogo para o usuário escolher a planilha (.xlsx),
        gera o JSON de mapeamento e salva na pasta do projeto.
        """
        xlsx_path = filedialog.askopenfilename(
            title="Selecionar planilha de cofres",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")],
        )
        if not xlsx_path:
            return

        try:
            import pandas as pd

            df = pd.read_excel(xlsx_path, dtype=str)
            df.columns = [c.strip() for c in df.columns]

            required = {"UF", "LOJA", "NOME", "COFRE"}
            missing = required - set(df.columns)
            if missing:
                messagebox.showerror(
                    "Colunas não encontradas",
                    f"A planilha não contém: {', '.join(missing)}\n"
                    f"Colunas encontradas: {', '.join(df.columns)}",
                )
                return

            lojas         = []
            brinks_map    = {}   # COFRE -> LOJA  (1:1)
            prossegur_map = {}   # NOME  -> [LOJA, ...]  (1:N)

            for _, row in df.iterrows():
                uf    = str(row["UF"]).strip()
                loja  = str(row["LOJA"]).strip()
                nome  = str(row["NOME"]).strip()
                cofre = str(row["COFRE"]).strip()

                lojas.append({"uf": uf, "loja": loja, "nome": nome, "cofre": cofre})

                # Brinks: cofre -> loja (1:1)
                brinks_map[cofre] = loja

                # Prossegur: nome -> lista de lojas (1:N)
                prossegur_map.setdefault(nome, [])
                if loja not in prossegur_map[nome]:
                    prossegur_map[nome].append(loja)

            output = {
                "lojas":         lojas,
                "brinks_map":    brinks_map,
                "prossegur_map": prossegur_map,
            }

            with open(MAPA_JSON, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            self._status_var.set(
                f"Mapeamento exportado  —  {len(lojas)} lojas  "
                f"({len(brinks_map)} cofres Brinks, {len(prossegur_map)} nomes Prossegur)"
            )

            messagebox.showinfo(
                "Exportação concluída",
                f"JSON gerado com sucesso!\n\n"
                f"  Lojas:            {len(lojas)}\n"
                f"  Cofres Brinks:    {len(brinks_map)}\n"
                f"  Nomes Prossegur:  {len(prossegur_map)}\n\n"
                f"Arquivo: {MAPA_JSON}",
            )

        except Exception as exc:
            messagebox.showerror("Erro na exportação", str(exc))

    # ------------------------------------------------------------------ #
    #  Utilitários                                                          #
    # ------------------------------------------------------------------ #
    def center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")


if __name__ == "__main__":
    app = CofreApp()
    app.mainloop()
