"""
lojas.py
Módulo de Lojas — Conciliação Vendas × Contabilidade.

Estrutura:
  • Seleção de loja via Combobox
  • Importação de 2 bases Excel (Vendas e Contabilidade)
  • Tabela de conciliação na tela principal
  • Painel inferior com filtro Mês/Ano e cards-resumo por loja
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

import ui_theme as theme

# ── Persistência local ─────────────────────────────────────────────────────── #
_DATA_FILE = os.path.join(os.path.dirname(__file__), "lojas_data.json")


def _load_data() -> dict:
    """Carrega dados salvos em disco."""
    if os.path.exists(_DATA_FILE):
        try:
            with open(_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"lojas": [], "conciliacoes": {}}


def _save_data(data: dict):
    """Persiste dados em disco."""
    with open(_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Utilitários pandas ─────────────────────────────────────────────────────── #
def _read_excel(path: str):
    """Lê um Excel e retorna um DataFrame ou None."""
    try:
        import pandas as pd
        df = pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        messagebox.showerror("Erro ao ler Excel", str(e))
        return None


def _parse_value(v) -> float:
    """Converte string monetária → float."""
    try:
        return float(str(v).replace("R$", "").replace(".", "").replace(",", ".").strip())
    except Exception:
        return 0.0


# ── Diálogo de importação de bases ────────────────────────────────────────── #
class _ImportDialog(tk.Toplevel):
    """
    Janelinha modal para importar as duas bases (Vendas + Contabilidade).
    Retorna os DataFrames via self.df_vendas / self.df_contab após confirmar.
    """

    def __init__(self, parent, loja_nome: str):
        super().__init__(parent)
        self.title(f"Importar Bases — {loja_nome}")
        self.geometry("480x260")
        self.resizable(False, False)
        self.configure(bg=theme.BG_APP)
        theme.apply_theme(self)
        self.grab_set()
        self.transient(parent)

        self.df_vendas  = None
        self.df_contab  = None
        self._path_v    = tk.StringVar(value="Nenhum arquivo selecionado")
        self._path_c    = tk.StringVar(value="Nenhum arquivo selecionado")
        self._confirmed = False

        self._build()
        self._center(parent)

    # ── Layout ── #
    def _build(self):
        # Toolbar interna
        bar = tk.Frame(self, bg=theme.PRIMARY, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="📂  Importar Bases Excel",
                 bg=theme.PRIMARY, fg="white",
                 font=("Segoe UI Semibold", 12)).pack(side="left", padx=16, pady=10)

        body = tk.Frame(self, bg=theme.BG_APP, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        # Vendas
        self._row_import(body, "📈  Base de Vendas", self._path_v,
                         self._browse_vendas, row=0)
        # Contabilidade
        self._row_import(body, "📒  Base de Contabilidade", self._path_c,
                         self._browse_contab, row=1)

        # Botões
        btn_frame = tk.Frame(self, bg=theme.BG_APP, padx=24)
        btn_frame.pack(fill="x", pady=(0, 16))

        tk.Button(btn_frame, text="✔  Confirmar",
                  bg=theme.PRIMARY, fg="white",
                  activebackground=theme.PRIMARY_HOVER, activeforeground="white",
                  font=("Segoe UI Semibold", 11), relief="flat", bd=0,
                  cursor="hand2", padx=18, pady=7,
                  command=self._confirm).pack(side="right", padx=(8, 0))

        tk.Button(btn_frame, text="Cancelar",
                  bg="#14324a", fg=theme.FG_TEXT,
                  activebackground="#1a4061", activeforeground="white",
                  font=("Segoe UI", 11), relief="flat", bd=0,
                  cursor="hand2", padx=14, pady=7,
                  command=self.destroy).pack(side="right")

    def _row_import(self, parent, label: str, var: tk.StringVar, cmd, row: int):
        tk.Label(parent, text=label, bg=theme.BG_APP, fg=theme.FG_TEXT,
                 font=("Segoe UI Semibold", 10)).grid(
            row=row*2, column=0, sticky="w", pady=(8, 2))

        frm = tk.Frame(parent, bg=theme.BG_APP)
        frm.grid(row=row*2+1, column=0, sticky="ew", pady=(0, 6))
        parent.columnconfigure(0, weight=1)

        tk.Label(frm, textvariable=var, bg=theme.CARD_BG, fg=theme.FG_MUTED,
                 font=("Segoe UI", 9), anchor="w", padx=8, pady=5,
                 width=42, relief="flat").pack(side="left", fill="x", expand=True)

        tk.Button(frm, text="Procurar",
                  bg="#14324a", fg=theme.FG_TEXT,
                  activebackground="#1a4061", activeforeground="white",
                  font=("Segoe UI", 10), relief="flat", bd=0,
                  cursor="hand2", padx=10, pady=5,
                  command=cmd).pack(side="left", padx=(6, 0))

    # ── Lógica ── #
    def _browse_vendas(self):
        p = filedialog.askopenfilename(
            title="Selecionar Base de Vendas",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")])
        if p:
            self._path_v.set(p)
            self.df_vendas = _read_excel(p)

    def _browse_contab(self):
        p = filedialog.askopenfilename(
            title="Selecionar Base de Contabilidade",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")])
        if p:
            self._path_c.set(p)
            self.df_contab = _read_excel(p)

    def _confirm(self):
        if self.df_vendas is None or self.df_contab is None:
            messagebox.showwarning("Atenção",
                "Importe as duas bases antes de confirmar.", parent=self)
            return
        self._confirmed = True
        self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        pw = parent.winfo_rootx() + parent.winfo_width()  // 2
        ph = parent.winfo_rooty() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"{w}x{h}+{pw - w//2}+{ph - h//2}")


# ── Frame principal do módulo ──────────────────────────────────────────────── #
class LojasFrame(tk.Frame):
    """
    Frame completo do módulo Lojas.
    Integra-se ao MenuPrincipal exatamente como _CofreFrame.
    """

    def __init__(self, master):
        super().__init__(master, bg=theme.BG_APP)
        self._data        = _load_data()        # {"lojas": [...], "conciliacoes": {...}}
        self._loja_atual  = None                # nome da loja selecionada
        self._df_vendas   = None
        self._df_contab   = None
        self._concil_rows = []                  # linhas exibidas na tabela

        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════════ #
    #   LAYOUT PRINCIPAL
    # ══════════════════════════════════════════════════════════════════════════ #
    def _build_ui(self):
        # ── Toolbar ── #
        toolbar = tk.Frame(self, bg=theme.PRIMARY, height=52)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)
        tk.Label(toolbar, text="🏪  GOODCARD",
                 bg=theme.PRIMARY, fg="white",
                 font=("Segoe UI Semibold", 14)).pack(side="left", padx=20, pady=10)
        tk.Label(toolbar, text="v1.0",
                 bg=theme.PRIMARY, fg="white",
                 font=("Segoe UI", 10)).pack(side="right", padx=20)

        tk.Frame(self, bg=theme.GRID_LINE, height=1).pack(fill="x")

        # ── Área de seleção de loja + importação ── #
        self._build_selector()

        # ── Separador ── #
        tk.Frame(self, bg=theme.GRID_LINE, height=1).pack(fill="x", padx=24)

        # ── Tabela de conciliação ── #
        self._build_concil_table()

        # ── Separador ── #
        tk.Frame(self, bg=theme.GRID_LINE, height=1).pack(fill="x", padx=24, pady=(8, 0))

        # ── Painel de resumo por loja ── #
        self._build_summary_panel()

        # ── Status bar ── #
        status = tk.Frame(self, bg="#0b1a29", height=26)
        status.pack(fill="x", side="bottom")
        status.pack_propagate(False)
        self._status_var = tk.StringVar(value="Selecione uma loja para começar.")
        tk.Label(status, textvariable=self._status_var,
                 bg="#0b1a29", fg=theme.FG_MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=12, pady=4)

    # ── Seletor de loja + botões de ação ── #
    def _build_selector(self):
        bar = tk.Frame(self, bg=theme.BG_APP, padx=24, pady=14)
        bar.pack(fill="x")

        tk.Label(bar, text="Escolha a loja:",
                 bg=theme.BG_APP, fg=theme.FG_TEXT,
                 font=("Segoe UI Semibold", 11)).pack(side="left")

        self._loja_var = tk.StringVar()
        self._combo = ttk.Combobox(bar, textvariable=self._loja_var,
                                   state="readonly", width=28,
                                   font=("Segoe UI", 11))
        self._combo.pack(side="left", padx=(10, 0))
        self._combo.bind("<<ComboboxSelected>>", self._on_loja_selected)
        self._refresh_combo()

        # Botão: adicionar loja
        tk.Button(bar, text="＋  Nova Loja",
                  bg="#14324a", fg=theme.FG_TEXT,
                  activebackground="#1a4061", activeforeground="white",
                  font=("Segoe UI", 10), relief="flat", bd=0,
                  cursor="hand2", padx=12, pady=5,
                  command=self._add_loja).pack(side="left", padx=(12, 0))

        # Botão: importar bases
        self._btn_import = tk.Button(bar, text="📂  Importar Bases",
                  bg=theme.PRIMARY, fg="white",
                  activebackground=theme.PRIMARY_HOVER, activeforeground="white",
                  font=("Segoe UI Semibold", 10), relief="flat", bd=0,
                  cursor="hand2", padx=12, pady=5,
                  state="disabled",
                  command=self._importar_bases)
        self._btn_import.pack(side="left", padx=(8, 0))

        # Botão: remover loja
        tk.Button(bar, text="🗑",
                  bg="#14324a", fg=theme.ACCENT_RED,
                  activebackground="#1a4061", activeforeground=theme.ACCENT_RED,
                  font=("Segoe UI", 11), relief="flat", bd=0,
                  cursor="hand2", padx=8, pady=5,
                  command=self._remove_loja).pack(side="left", padx=(6, 0))

    # ── Tabela de conciliação ── #
    def _build_concil_table(self):
        hdr = tk.Frame(self, bg=theme.BG_APP, padx=24)
        hdr.pack(fill="x", pady=(10, 4))
        tk.Label(hdr, text="📊  Conciliação — Vendas × Contabilidade",
                 bg=theme.BG_APP, fg=theme.FG_TEXT,
                 font=("Segoe UI Semibold", 12)).pack(side="left")

        self._loja_label = tk.Label(hdr, text="",
                 bg=theme.BG_APP, fg=theme.PRIMARY,
                 font=("Segoe UI Semibold", 12))
        self._loja_label.pack(side="left", padx=(8, 0))

        # Frame da tabela com scroll
        tbl_wrap = tk.Frame(self, bg=theme.CARD_BG, padx=2, pady=2)
        tbl_wrap.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        cols = ("mes_ano", "vendas", "contab", "diferenca", "status")
        headers = ("Mês / Ano", "Vendas (R$)", "Contabilidade (R$)", "Diferença (R$)", "Status")
        col_w   = (120, 140, 160, 140, 100)

        self._tree = ttk.Treeview(tbl_wrap, columns=cols, show="headings",
                                  style="Treeview", selectmode="browse")
        for col, hdr_txt, w in zip(cols, headers, col_w):
            self._tree.heading(col, text=hdr_txt)
            self._tree.column(col, width=w, minwidth=80, anchor="center")

        vsb = ttk.Scrollbar(tbl_wrap, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree_placeholder()

    def _tree_placeholder(self):
        self._tree.delete(*self._tree.get_children())
        self._tree.insert("", "end", values=(
            "—", "—", "—", "—", "Selecione uma loja e importe as bases"))

    # ── Painel de resumo ── #
    def _build_summary_panel(self):
        # Cabeçalho + filtro
        hdr = tk.Frame(self, bg=theme.BG_APP, padx=24)
        hdr.pack(fill="x", pady=(10, 6))

        tk.Label(hdr, text="📋  Resumo das Lojas",
                 bg=theme.BG_APP, fg=theme.FG_TEXT,
                 font=("Segoe UI Semibold", 12)).pack(side="left")

        # Filtro Mês
        tk.Label(hdr, text="Mês:",
                 bg=theme.BG_APP, fg=theme.FG_MUTED,
                 font=("Segoe UI", 10)).pack(side="left", padx=(24, 4))
        meses = ["Todos", "01 - Jan", "02 - Fev", "03 - Mar", "04 - Abr",
                 "05 - Mai", "06 - Jun", "07 - Jul", "08 - Ago",
                 "09 - Set", "10 - Out", "11 - Nov", "12 - Dez"]
        self._filter_mes = tk.StringVar(value="Todos")
        ttk.Combobox(hdr, textvariable=self._filter_mes, values=meses,
                     state="readonly", width=10,
                     font=("Segoe UI", 10)).pack(side="left")

        # Filtro Ano
        tk.Label(hdr, text="Ano:",
                 bg=theme.BG_APP, fg=theme.FG_MUTED,
                 font=("Segoe UI", 10)).pack(side="left", padx=(12, 4))
        anos = ["Todos"] + [str(a) for a in range(2020, 2031)]
        self._filter_ano = tk.StringVar(value="Todos")
        ttk.Combobox(hdr, textvariable=self._filter_ano, values=anos,
                     state="readonly", width=8,
                     font=("Segoe UI", 10)).pack(side="left")

        tk.Button(hdr, text="🔍  Filtrar",
                  bg="#14324a", fg=theme.FG_TEXT,
                  activebackground="#1a4061", activeforeground="white",
                  font=("Segoe UI", 10), relief="flat", bd=0,
                  cursor="hand2", padx=10, pady=4,
                  command=self._refresh_cards).pack(side="left", padx=(10, 0))

        # Área de cards (com scroll horizontal via Canvas)
        canvas_wrap = tk.Frame(self, bg=theme.BG_APP)
        canvas_wrap.pack(fill="x", padx=24, pady=(0, 12))

        self._cards_canvas = tk.Canvas(canvas_wrap, bg=theme.BG_APP,
                                       highlightthickness=0, height=148)
        hsb = ttk.Scrollbar(canvas_wrap, orient="horizontal",
                             command=self._cards_canvas.xview)
        self._cards_canvas.configure(xscrollcommand=hsb.set)
        self._cards_canvas.pack(fill="x", expand=True)
        hsb.pack(fill="x")

        self._cards_inner = tk.Frame(self._cards_canvas, bg=theme.BG_APP)
        self._cards_win = self._cards_canvas.create_window(
            (0, 0), window=self._cards_inner, anchor="nw")
        self._cards_inner.bind("<Configure>", self._on_cards_resize)

        self._refresh_cards()

    def _on_cards_resize(self, _event=None):
        self._cards_canvas.configure(
            scrollregion=self._cards_canvas.bbox("all"))

    # ══════════════════════════════════════════════════════════════════════════ #
    #   LÓGICA
    # ══════════════════════════════════════════════════════════════════════════ #

    # ── Combo de lojas ── #
    def _refresh_combo(self):
        lojas = self._data.get("lojas", [])
        self._combo["values"] = lojas if lojas else [""]
        if lojas and self._loja_var.get() not in lojas:
            self._loja_var.set("")

    def _on_loja_selected(self, _event=None):
        nome = self._loja_var.get()
        if not nome:
            return
        self._loja_atual = nome
        self._loja_label.config(text=f"›  {nome}")
        self._btn_import.config(state="normal")
        # Carrega conciliação existente se houver
        rows = self._data.get("conciliacoes", {}).get(nome, [])
        self._concil_rows = rows
        self._refresh_table(rows)
        self._status_var.set(
            f"Loja: {nome}  |  "
            f"{len(rows)} registro(s) de conciliação carregado(s).")

    def _add_loja(self):
        dlg = _InputDialog(self, "Nova Loja", "Nome da loja:")
        self.wait_window(dlg)
        nome = dlg.result.strip() if dlg.result else ""
        if not nome:
            return
        if nome in self._data["lojas"]:
            messagebox.showwarning("Atenção", f"A loja '{nome}' já existe.", parent=self)
            return
        self._data["lojas"].append(nome)
        _save_data(self._data)
        self._refresh_combo()
        self._combo.set(nome)
        self._on_loja_selected()
        self._refresh_cards()
        self._status_var.set(f"Loja '{nome}' adicionada.")

    def _remove_loja(self):
        nome = self._loja_var.get()
        if not nome:
            messagebox.showinfo("Atenção", "Nenhuma loja selecionada.", parent=self)
            return
        if not messagebox.askyesno("Remover", f"Remover a loja '{nome}' e todos os seus dados?",
                                   parent=self):
            return
        self._data["lojas"] = [l for l in self._data["lojas"] if l != nome]
        self._data.get("conciliacoes", {}).pop(nome, None)
        _save_data(self._data)
        self._loja_atual  = None
        self._loja_label.config(text="")
        self._btn_import.config(state="disabled")
        self._loja_var.set("")
        self._refresh_combo()
        self._tree_placeholder()
        self._refresh_cards()
        self._status_var.set(f"Loja '{nome}' removida.")

    # ── Importação ── #
    def _importar_bases(self):
        if not self._loja_atual:
            return
        dlg = _ImportDialog(self, self._loja_atual)
        self.wait_window(dlg)
        if not dlg._confirmed:
            return

        self._df_vendas = dlg.df_vendas
        self._df_contab = dlg.df_contab
        rows = self._conciliar(self._df_vendas, self._df_contab)
        self._concil_rows = rows

        # Persiste
        if "conciliacoes" not in self._data:
            self._data["conciliacoes"] = {}
        self._data["conciliacoes"][self._loja_atual] = rows
        _save_data(self._data)

        self._refresh_table(rows)
        self._refresh_cards()
        n_ok  = sum(1 for r in rows if r["status"] == "OK")
        n_div = len(rows) - n_ok
        self._status_var.set(
            f"Loja: {self._loja_atual}  |  "
            f"{len(rows)} meses conciliados  —  "
            f"✔ {n_ok} OK  |  ⚠ {n_div} divergência(s)")

    # ── Conciliação ── #
    def _conciliar(self, df_v, df_c) -> list:
        """
        Estratégia automática:
          1. Tenta coluna 'MES_ANO' (formato MM/AAAA ou AAAA-MM).
          2. Se não existir, tenta 'DATA' e agrupa por mês.
          3. Soma a primeira coluna numérica como valor.
        Retorna lista de dicts: mes_ano, vendas, contab, diferenca, status.
        """
        import pandas as pd

        def _extract_monthly(df: pd.DataFrame, label: str) -> dict:
            """Retorna {mes_ano: total} para o dataframe."""
            # Tenta coluna explícita MES_ANO / MES-ANO / PERIODO
            ma_col = next((c for c in df.columns
                           if c.upper().replace("-", "_") in
                           ("MES_ANO", "PERIODO", "COMPETENCIA", "MES")), None)
            # Tenta coluna DATA / DT_*
            dt_col = next((c for c in df.columns
                           if c.upper().startswith("DATA") or
                           c.upper().startswith("DT_")), None)
            # Coluna de valor: primeira numérica ou com VALOR / TOTAL / BRUTO / LIQUIDO
            val_col = next((c for c in df.columns
                            if c.upper() in
                            ("VALOR", "TOTAL", "BRUTO", "LIQUIDO",
                             "VLR_VENDA", "VLR_CONTAB", "RECEITA")), None)
            if val_col is None:
                # Pega primeira coluna que converte para float
                for c in df.columns:
                    try:
                        df[c].apply(_parse_value).sum()
                        val_col = c
                        break
                    except Exception:
                        pass
            if val_col is None:
                return {}

            result = {}
            if ma_col:
                for _, row in df.iterrows():
                    key = str(row[ma_col]).strip()
                    result[key] = result.get(key, 0.0) + _parse_value(row[val_col])
            elif dt_col:
                for _, row in df.iterrows():
                    try:
                        dt = pd.to_datetime(str(row[dt_col]), dayfirst=True, errors="coerce")
                        if pd.isna(dt):
                            continue
                        key = dt.strftime("%m/%Y")
                    except Exception:
                        continue
                    result[key] = result.get(key, 0.0) + _parse_value(row[val_col])
            else:
                # Sem referência temporal → agrupa tudo como "—"
                total = df[val_col].apply(_parse_value).sum()
                result["—"] = total
            return result

        map_v = _extract_monthly(df_v, "vendas")
        map_c = _extract_monthly(df_c, "contab")
        keys  = sorted(set(map_v) | set(map_c))

        rows = []
        for k in keys:
            v  = map_v.get(k, 0.0)
            c  = map_c.get(k, 0.0)
            d  = v - c
            st = "OK" if abs(d) < 0.01 else "⚠ Divergente"
            rows.append({"mes_ano": k, "vendas": v, "contab": c,
                          "diferenca": d, "status": st})
        return rows

    # ── Tabela ── #
    def _refresh_table(self, rows: list):
        self._tree.delete(*self._tree.get_children())
        if not rows:
            self._tree_placeholder()
            return
        for r in rows:
            color = "ok" if r["status"] == "OK" else "div"
            self._tree.insert("", "end", values=(
                r["mes_ano"],
                f"R$ {r['vendas']:,.2f}",
                f"R$ {r['contab']:,.2f}",
                f"R$ {r['diferenca']:,.2f}",
                r["status"],
            ), tags=(color,))

        self._tree.tag_configure("ok",  foreground=theme.ACCENT_GREEN)
        self._tree.tag_configure("div", foreground=theme.ACCENT_ORANGE)

    # ── Cards de resumo ── #
    def _refresh_cards(self):
        for w in self._cards_inner.winfo_children():
            w.destroy()

        mes_filtro = self._filter_mes.get()
        ano_filtro = self._filter_ano.get()
        concils    = self._data.get("conciliacoes", {})
        lojas      = self._data.get("lojas", [])

        if not lojas:
            tk.Label(self._cards_inner, text="Nenhuma loja cadastrada.",
                     bg=theme.BG_APP, fg=theme.FG_MUTED,
                     font=("Segoe UI", 10)).pack(padx=16, pady=20)
            self._on_cards_resize()
            return

        for i, loja in enumerate(lojas):
            rows = concils.get(loja, [])

            # Aplica filtro
            def _match(r):
                ma = r.get("mes_ano", "")
                if mes_filtro != "Todos":
                    m_num = mes_filtro.split(" - ")[0]
                    if not ma.startswith(m_num):
                        return False
                if ano_filtro != "Todos":
                    if ano_filtro not in ma:
                        return False
                return True

            filtered = [r for r in rows if _match(r)]

            total_v   = sum(r["vendas"]    for r in filtered)
            total_c   = sum(r["contab"]    for r in filtered)
            total_d   = sum(r["diferenca"] for r in filtered)
            n_div     = sum(1 for r in filtered if r["status"] != "OK")
            status_cor = theme.ACCENT_GREEN if n_div == 0 and filtered else \
                         (theme.ACCENT_ORANGE if filtered else theme.FG_MUTED)

            card = tk.Frame(self._cards_inner, bg=theme.CARD_BG,
                            relief="flat", bd=0, cursor="hand2")
            card.pack(side="left", padx=8, pady=6, ipadx=0, ipady=0)

            # Borda superior colorida
            tk.Frame(card, bg=status_cor, height=3).pack(fill="x")

            body = tk.Frame(card, bg=theme.CARD_BG, padx=14, pady=10)
            body.pack()

            tk.Label(body, text=f"🏪  {loja}",
                     bg=theme.CARD_BG, fg=theme.FG_TEXT,
                     font=("Segoe UI Semibold", 11),
                     wraplength=160, justify="left").pack(anchor="w")

            tk.Frame(body, bg=theme.GRID_LINE, height=1).pack(
                fill="x", pady=(6, 6))

            def _info_row(parent, label, value, color=theme.FG_TEXT):
                f = tk.Frame(parent, bg=theme.CARD_BG)
                f.pack(fill="x", pady=1)
                tk.Label(f, text=label, bg=theme.CARD_BG, fg=theme.FG_MUTED,
                         font=("Segoe UI", 9), width=13, anchor="w").pack(side="left")
                tk.Label(f, text=value, bg=theme.CARD_BG, fg=color,
                         font=("Segoe UI Semibold", 9), anchor="e").pack(side="right")

            if filtered:
                _info_row(body, "Vendas:", f"R$ {total_v:,.2f}", theme.FG_TEXT)
                _info_row(body, "Contabilidade:", f"R$ {total_c:,.2f}", theme.FG_TEXT)
                div_color = theme.ACCENT_GREEN if abs(total_d) < 0.01 else theme.ACCENT_ORANGE
                _info_row(body, "Diferença:", f"R$ {total_d:,.2f}", div_color)
                st_txt  = "✔  OK" if n_div == 0 else f"⚠  {n_div} diverg."
                _info_row(body, "Status:", st_txt, status_cor)
            else:
                tk.Label(body, text="Sem dados no período",
                         bg=theme.CARD_BG, fg=theme.FG_MUTED,
                         font=("Segoe UI", 9)).pack(anchor="w", pady=4)

        self._on_cards_resize()


# ── Diálogo de texto simples ────────────────────────────────────────────────── #
class _InputDialog(tk.Toplevel):
    """Mini-diálogo para capturar um texto simples."""

    def __init__(self, parent, title: str, prompt: str):
        super().__init__(parent)
        self.title(title)
        self.geometry("340x140")
        self.resizable(False, False)
        self.configure(bg=theme.BG_APP)
        theme.apply_theme(self)
        self.grab_set()
        self.transient(parent)
        self.result = ""

        tk.Label(self, text=prompt,
                 bg=theme.BG_APP, fg=theme.FG_TEXT,
                 font=("Segoe UI", 11)).pack(padx=24, pady=(18, 6), anchor="w")

        self._var = tk.StringVar()
        entry = tk.Entry(self, textvariable=self._var,
                         bg=theme.CARD_BG, fg=theme.FG_TEXT,
                         insertbackground=theme.FG_TEXT,
                         font=("Segoe UI", 11), relief="flat", bd=6)
        entry.pack(fill="x", padx=24)
        entry.focus_set()
        entry.bind("<Return>", lambda _: self._ok())

        bf = tk.Frame(self, bg=theme.BG_APP)
        bf.pack(fill="x", padx=24, pady=12)
        tk.Button(bf, text="OK",
                  bg=theme.PRIMARY, fg="white",
                  activebackground=theme.PRIMARY_HOVER, activeforeground="white",
                  font=("Segoe UI Semibold", 10), relief="flat", bd=0,
                  cursor="hand2", padx=16, pady=5,
                  command=self._ok).pack(side="right")
        tk.Button(bf, text="Cancelar",
                  bg="#14324a", fg=theme.FG_TEXT,
                  activebackground="#1a4061", activeforeground="white",
                  font=("Segoe UI", 10), relief="flat", bd=0,
                  cursor="hand2", padx=10, pady=5,
                  command=self.destroy).pack(side="right", padx=(0, 6))

    def _ok(self):
        self.result = self._var.get()
        self.destroy()


# ── Factory para o MenuPrincipal ──────────────────────────────────────────── #
def _open_lojas(root: tk.Tk, on_close):
    """
    Factory compatível com o padrão do MenuPrincipal.
    Cria a Toplevel, injeta o LojasFrame e retorna a janela.
    """
    win = tk.Toplevel(root)
    win.title("")
    win.geometry("1100x680")
    win.minsize(900, 560)
    win.resizable(True, True)
    win.configure(bg=theme.BG_APP)
    theme.apply_theme(win)

    frame = LojasFrame(win)
    frame.pack(fill="both", expand=True)

    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    x = (win.winfo_screenwidth()  - w) // 2
    y = (win.winfo_screenheight() - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

    win.protocol("WM_DELETE_WINDOW", lambda: on_close(win))
    return win


# ── Entrada no registro de módulos (cole em MODULES do menu_principal.py) ─── #
LOJAS_MODULE = {
    "emoji":    "🏪",
    "title":    "Módulo de Lojas",
    "subtitle": "Conciliação Vendas × Contabilidade por loja",
    "factory":  _open_lojas,
}


# ── Execução standalone (teste direto) ── #
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Lojas — Standalone")
    root.geometry("1100x680")
    root.minsize(900, 560)
    theme.apply_theme(root)

    LojasFrame(root).pack(fill="both", expand=True)
    root.mainloop()