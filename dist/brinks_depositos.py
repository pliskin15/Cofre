"""
brinks_depositos.py
Módulo de Depósitos — Brinks
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import json
import os

import ui_theme as theme
import database as db

MAPA_JSON = os.path.join(os.path.dirname(__file__), "codigos_cofres.json")


# ──────────────────────────────────────────────────────────────────────────── #
#  Helpers de mapeamento                                                        #
# ──────────────────────────────────────────────────────────────────────────── #

def _carregar_mapa() -> dict:
    if os.path.exists(MAPA_JSON):
        with open(MAPA_JSON, encoding="utf-8") as f:
            return json.load(f)
    return {"brinks_map": {}}


def _loja_por_serial(serial: str) -> str:
    mapa = _carregar_mapa()
    loja = mapa.get("brinks_map", {}).get(str(serial).strip())
    return loja if loja else f"({serial})"


# ──────────────────────────────────────────────────────────────────────────── #
#  Janela de detalhe (duplo clique)                                             #
# ──────────────────────────────────────────────────────────────────────────── #

class DetalheDeposito(tk.Toplevel):
    def __init__(self, parent, data: str, loja: str, lancamentos: list[dict]):
        super().__init__(parent)
        self.title(f"Depósitos  —  Loja {loja}  —  {data}")
        self.geometry("680x400")
        self.minsize(560, 300)
        self.resizable(True, True)
        self.configure(bg=theme.BG_APP)
        theme.apply_theme(self)

        self._build(data, loja, lancamentos)
        self._center(parent)

    def _build(self, data: str, loja: str, lancamentos: list[dict]):
        header = tk.Frame(self, bg=theme.PRIMARY)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"  Loja {loja}   ·   {data}   ·   {len(lancamentos)} lançamento(s)",
            bg=theme.PRIMARY, fg="white",
            font=("Segoe UI Semibold", 11), pady=10, anchor="w",
        ).pack(fill="x", padx=12)

        cols = ("inclusao", "valor", "depositante")
        frame = ttk.Frame(self, style="App.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            style="Treeview", selectmode="browse")

        tree.heading("inclusao",    text="Data de Inclusão")
        tree.heading("valor",       text="Valor")
        tree.heading("depositante", text="Depositante")

        tree.column("inclusao",    width=180, anchor="center")
        tree.column("valor",       width=120, anchor="e")
        tree.column("depositante", width=260, anchor="w")

        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview,
                           style="Vertical.TScrollbar")
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        total = 0.0
        for i, lc in enumerate(lancamentos):
            valor = float(lc["valor"]) if lc["valor"] else 0.0
            total += valor
            tag = "par" if i % 2 == 0 else "impar"
            tree.insert("", "end", values=(
                lc["data_inclusao"] if "data_inclusao" in lc else lc.get("inclusao", ""),
                f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                lc.get("depositante", ""),
            ), tags=(tag,))

        tree.tag_configure("par",   background=theme.CARD_BG)
        tree.tag_configure("impar", background="#0d2033")

        footer = tk.Frame(self, bg="#0b1a29", pady=8)
        footer.pack(fill="x")

        total_fmt = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        tk.Label(
            footer,
            text=f"Total do dia:   {total_fmt}",
            bg="#0b1a29", fg=theme.FG_TEXT,
            font=("Segoe UI Semibold", 11),
        ).pack(side="right", padx=16)

    def _center(self, parent):
        self.update_idletasks()
        pw = parent.winfo_rootx() + parent.winfo_width() // 2
        ph = parent.winfo_rooty() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"{w}x{h}+{pw - w // 2}+{ph - h // 2}")


# ──────────────────────────────────────────────────────────────────────────── #
#  Frame principal do módulo                                                    #
# ──────────────────────────────────────────────────────────────────────────── #

class BrinksDepositos(ttk.Frame):

    def __init__(self, master, **kwargs):
        super().__init__(master, style="App.TFrame", **kwargs)
        self._resumo: list[dict] = []
        db.inicializar()
        self._build()
        self._carregar_do_banco()   # carrega o que já estava salvo

    # ------------------------------------------------------------------ #
    #  Layout                                                               #
    # ------------------------------------------------------------------ #
    def _build(self):
        toolbar = tk.Frame(self, bg=theme.CARD_BG, pady=6)
        toolbar.pack(fill="x")

        tk.Button(
            toolbar,
            text="📂  Importar Planilha",
            command=self._importar,
            bg=theme.PRIMARY, fg="white",
            activebackground=theme.PRIMARY_HOVER, activeforeground="white",
            relief="flat", bd=0, cursor="hand2",
            padx=14, pady=6,
            font=("Segoe UI Semibold", 10),
        ).pack(side="left", padx=10)

        self._lbl_arquivo = tk.Label(
            toolbar, text="Dados carregados do banco local",
            bg=theme.CARD_BG, fg=theme.FG_MUTED,
            font=("Segoe UI", 9),
        )
        self._lbl_arquivo.pack(side="left", padx=6)

        self._lbl_total = tk.Label(
            toolbar, text="",
            bg=theme.CARD_BG, fg=theme.FG_TEXT,
            font=("Segoe UI Semibold", 10),
        )
        self._lbl_total.pack(side="right", padx=16)

        tk.Frame(self, bg=theme.GRID_LINE, height=1).pack(fill="x")

        cols = ("data", "loja", "qtd", "valor")
        frame_tree = ttk.Frame(self, style="App.TFrame")
        frame_tree.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(
            frame_tree, columns=cols, show="headings",
            style="Treeview", selectmode="browse",
        )

        self._tree.heading("data",  text="Data do Depósito")
        self._tree.heading("loja",  text="Loja")
        self._tree.heading("qtd",   text="Qtd.")
        self._tree.heading("valor", text="Valor Total do Dia")

        self._tree.column("data",  width=160, anchor="center")
        self._tree.column("loja",  width=80,  anchor="center")
        self._tree.column("qtd",   width=60,  anchor="center")
        self._tree.column("valor", width=200, anchor="e")

        sb = ttk.Scrollbar(frame_tree, orient="vertical",
                           command=self._tree.yview,
                           style="Vertical.TScrollbar")
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._tree.bind("<Double-1>", self._on_duplo_clique)

        tk.Label(
            self,
            text="Dê duplo clique em uma linha para ver os lançamentos do dia.",
            bg=theme.BG_APP, fg=theme.FG_MUTED, font=("Segoe UI", 9),
        ).pack(side="bottom", pady=6)

    # ------------------------------------------------------------------ #
    #  Banco → tela                                                         #
    # ------------------------------------------------------------------ #
    def _carregar_do_banco(self):
        self._resumo = db.get_resumo_depositos_brinks()
        self._preencher_tabela()

    # ------------------------------------------------------------------ #
    #  Importação                                                           #
    # ------------------------------------------------------------------ #
    def _importar(self):
        path = filedialog.askopenfilename(
            title="Selecionar planilha Brinks — Depósitos",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")],
        )
        if not path:
            return

        try:
            df = pd.read_excel(path, dtype=str)
            df.columns = [c.strip() for c in df.columns]

            required = {
                "Data do Depósito", "Data de Inclusão",
                "Valor do Depósito", "Nr Serial do Equipamento", "Depositante",
            }
            missing = required - set(df.columns)
            if missing:
                messagebox.showerror(
                    "Colunas não encontradas",
                    f"Faltando: {', '.join(missing)}",
                )
                return

            df["Valor do Depósito"] = (
                pd.to_numeric(df["Valor do Depósito"], errors="coerce").fillna(0.0)
            )

            # Monta lista de registros para o banco
            registros = []
            for _, row in df.iterrows():
                serial = str(row["Nr Serial do Equipamento"]).strip()
                registros.append({
                    "data_deposito": str(row["Data do Depósito"]).strip(),
                    "data_inclusao": str(row["Data de Inclusão"]).strip(),
                    "nr_serial":     serial,
                    "loja":          _loja_por_serial(serial),
                    "valor":         float(row["Valor do Depósito"]),
                    "depositante":   str(row.get("Depositante", "")).strip(),
                    "nr_envelope":   str(row.get("Número do Envelope", "")).strip(),
                    "sequencia":     str(row.get("Sequência Numérica", "")).strip(),
                    "identificador": str(row.get("Identificador do Depósito", "")).strip(),
                    "sigla_filial":  str(row.get("Sigla Filial", "")).strip(),
                    "razao_social":  str(row.get("Razão Social Cliente", "")).strip(),
                })

            import os as _os
            inseridos, ignorados = db.insert_depositos_brinks(
                registros, _os.path.basename(path)
            )

            msg = f"✔  {inseridos} novo(s) inserido(s)"
            if ignorados:
                msg += f"   ·   {ignorados} duplicata(s) ignorada(s)"
            self._lbl_arquivo.configure(text=msg, fg=theme.ACCENT_GREEN)

            # Recarrega tela do banco
            self._carregar_do_banco()

        except Exception as exc:
            messagebox.showerror("Erro ao importar", str(exc))

    # ------------------------------------------------------------------ #
    #  Preenchimento da tabela                                              #
    # ------------------------------------------------------------------ #
    def _preencher_tabela(self):
        for row in self._tree.get_children():
            self._tree.delete(row)

        total_geral = 0.0
        for i, r in enumerate(self._resumo):
            valor_fmt = (
                f"R$ {r['total']:,.2f}"
                .replace(",", "X").replace(".", ",").replace("X", ".")
            )
            tag = "par" if i % 2 == 0 else "impar"
            self._tree.insert("", "end", iid=str(i), values=(
                r["data_corte"], r["loja"], r["qtd"], valor_fmt,
            ), tags=(tag,))
            total_geral += r["total"]

        self._tree.tag_configure("par",   background=theme.CARD_BG)
        self._tree.tag_configure("impar", background="#0d2033")

        total_fmt = (
            f"Total geral:  R$ {total_geral:,.2f}"
            .replace(",", "X").replace(".", ",").replace("X", ".")
        )
        self._lbl_total.configure(text=total_fmt)

    # ------------------------------------------------------------------ #
    #  Duplo clique → detalhe                                               #
    # ------------------------------------------------------------------ #
    def _on_duplo_clique(self, event):
        sel = self._tree.selection()
        if not sel:
            return

        idx     = int(sel[0])
        resumo  = self._resumo[idx]
        data    = resumo["data_corte"]
        serial  = resumo["nr_serial"]
        loja    = resumo["loja"]

        lancamentos = db.get_lancamentos_dia_brinks(data, serial)
        DetalheDeposito(self.winfo_toplevel(), data, loja, lancamentos)
