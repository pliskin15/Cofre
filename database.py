"""
database.py
Camada de acesso a dados — SQLite local.

Quando migrar para o banco de produção, implemente as mesmas funções
públicas aqui (insert_depositos_brinks, get_depositos_brinks, etc.)
apontando para o novo driver (pyodbc, psycopg2, pymysql...).
Nenhum outro arquivo precisará ser alterado.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "cofre.db")


# ──────────────────────────────────────────────────────────────────────────── #
#  Conexão                                                                      #
# ──────────────────────────────────────────────────────────────────────────── #

def _conectar() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # acesso por nome de coluna
    conn.execute("PRAGMA journal_mode=WAL") # melhor concorrência
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ──────────────────────────────────────────────────────────────────────────── #
#  Criação do schema                                                             #
# ──────────────────────────────────────────────────────────────────────────── #

def inicializar():
    """Cria as tabelas se ainda não existirem. Chame uma vez na inicialização."""
    with _conectar() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS depositos_brinks (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                data_deposito       TEXT    NOT NULL,   -- DD/MM/YYYY
                data_inclusao       TEXT    NOT NULL,   -- DD/MM/YYYY HH:MM:SS
                nr_serial           TEXT    NOT NULL,
                loja                TEXT    NOT NULL,
                valor               REAL    NOT NULL,
                depositante         TEXT,
                nr_envelope         TEXT,
                sequencia           TEXT,
                identificador       TEXT,
                sigla_filial        TEXT,
                razao_social        TEXT,
                arquivo_origem      TEXT,               -- nome do .xlsx importado
                importado_em        TEXT,               -- timestamp do import
                UNIQUE(data_inclusao, nr_serial, identificador)
            );

            CREATE TABLE IF NOT EXISTS conciliacao_ajustes (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                transportadora        TEXT    NOT NULL,
                loja                  TEXT    NOT NULL,
                data_deposito         TEXT    NOT NULL,
                total_deposito        REAL,
                total_credito         REAL,
                memo_remessa          REAL,
                dif_dep_memo          REAL,
                dif_dep_cred          REAL,
                status                TEXT,
                observacao            TEXT,
                data_credito_esperada TEXT,
                editado_em            TEXT    NOT NULL,
                UNIQUE(transportadora, loja, data_deposito)
            );

            CREATE INDEX IF NOT EXISTS idx_dep_brinks_data
                ON depositos_brinks(data_deposito);

            CREATE INDEX IF NOT EXISTS idx_dep_brinks_loja
                ON depositos_brinks(loja);

            CREATE TABLE IF NOT EXISTS creditos_brinks (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                data            TEXT    NOT NULL,   -- DD/MM/YYYY (campo DATA da planilha)
                loja            TEXT    NOT NULL,   -- número extraído do HISTORICO
                historico       TEXT    NOT NULL,   -- ex: "NOSSO DEPOSITO - LOJA.01"
                debito          REAL    NOT NULL DEFAULT 0.0,
                sequencia       TEXT,
                lote            TEXT,
                voucher         TEXT,
                doc_nro         TEXT,
                centro_custo    TEXT,
                conta_partida   TEXT,
                arquivo_origem  TEXT,
                importado_em    TEXT,
                UNIQUE(data, loja, historico, sequencia, lote, voucher)
            );

            CREATE INDEX IF NOT EXISTS idx_cred_brinks_data
                ON creditos_brinks(data);

            CREATE INDEX IF NOT EXISTS idx_cred_brinks_loja
                ON creditos_brinks(loja);

            CREATE TABLE IF NOT EXISTS depositos_prossegur (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                data_deposito   TEXT    NOT NULL,
                data_hora       TEXT    NOT NULL,
                nome_cofre      TEXT    NOT NULL,
                loja            TEXT,
                valor           REAL    NOT NULL,
                tipo            TEXT,
                depositante     TEXT,
                cliente         TEXT,
                moeda           TEXT    DEFAULT 'BRL',
                arquivo_origem  TEXT,
                importado_em    TEXT,
                UNIQUE(data_hora, nome_cofre, valor)
            );

            CREATE INDEX IF NOT EXISTS idx_dep_prossegur_data
                ON depositos_prossegur(data_deposito);

            CREATE INDEX IF NOT EXISTS idx_dep_prossegur_loja
                ON depositos_prossegur(loja);

            CREATE TABLE IF NOT EXISTS creditos_prossegur (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                data            TEXT    NOT NULL,
                loja            TEXT    NOT NULL,
                historico       TEXT    NOT NULL,
                debito          REAL    NOT NULL DEFAULT 0.0,
                sequencia       TEXT,
                lote            TEXT,
                voucher         TEXT,
                doc_nro         TEXT,
                centro_custo    TEXT,
                conta_partida   TEXT,
                arquivo_origem  TEXT,
                importado_em    TEXT,
                UNIQUE(data, loja, historico, sequencia, lote, voucher)
            );

            CREATE INDEX IF NOT EXISTS idx_cred_prossegur_data
                ON creditos_prossegur(data);

            CREATE INDEX IF NOT EXISTS idx_cred_prossegur_loja
                ON creditos_prossegur(loja);
        """)

    # Migração segura: adiciona colunas novas se ainda não existirem
    # (para bancos já criados com a versão antiga)
    _migrar()


def _migrar():
    """Adiciona colunas que podem não existir em bancos antigos."""
    with _conectar() as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(conciliacao_ajustes)")}
        if "dif_dep_memo" not in cols:
            conn.execute("ALTER TABLE conciliacao_ajustes ADD COLUMN dif_dep_memo REAL")
        if "dif_dep_cred" not in cols:
            conn.execute("ALTER TABLE conciliacao_ajustes ADD COLUMN dif_dep_cred REAL")
        if "data_credito_esperada" not in cols:
            conn.execute("ALTER TABLE conciliacao_ajustes ADD COLUMN data_credito_esperada TEXT")
        # remove coluna antiga "diferenca" não é possível em SQLite sem recriar,
        # então apenas deixamos de usá-la.


# ──────────────────────────────────────────────────────────────────────────── #
#  Depósitos Brinks                                                             #
# ──────────────────────────────────────────────────────────────────────────── #

def insert_depositos_brinks(registros: list[dict], arquivo_origem: str) -> tuple[int, int]:
    inicializar()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inseridos = 0
    ignorados = 0

    sql = """
        INSERT OR IGNORE INTO depositos_brinks (
            data_deposito, data_inclusao, nr_serial, loja,
            valor, depositante, nr_envelope, sequencia,
            identificador, sigla_filial, razao_social,
            arquivo_origem, importado_em
        ) VALUES (
            :data_deposito, :data_inclusao, :nr_serial, :loja,
            :valor, :depositante, :nr_envelope, :sequencia,
            :identificador, :sigla_filial, :razao_social,
            :arquivo_origem, :importado_em
        )
    """

    with _conectar() as conn:
        for r in registros:
            r["arquivo_origem"] = arquivo_origem
            r["importado_em"]   = agora
            cur = conn.execute(sql, r)
            if cur.rowcount:
                inseridos += 1
            else:
                ignorados += 1

    return inseridos, ignorados


def get_depositos_brinks(
    data_inicio: str | None = None,
    data_fim:    str | None = None,
    loja:        str | None = None,
) -> list[dict]:
    inicializar()
    where, params = [], {}

    if data_inicio:
        where.append("data_deposito >= :di")
        params["di"] = data_inicio
    if data_fim:
        where.append("data_deposito <= :df")
        params["df"] = data_fim
    if loja:
        where.append("loja = :loja")
        params["loja"] = loja

    clause = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
        SELECT * FROM depositos_brinks
        {clause}
        ORDER BY data_deposito, loja, data_inclusao
    """

    with _conectar() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [dict(r) for r in rows]


def salvar_ajuste(transportadora: str, loja: str, data_deposito: str, dados: dict):
    """Insere ou atualiza um ajuste manual de conciliação."""
    inicializar()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """
        INSERT INTO conciliacao_ajustes (
            transportadora, loja, data_deposito,
            total_deposito, total_credito, memo_remessa,
            dif_dep_memo, dif_dep_cred, status, observacao,
            data_credito_esperada, editado_em
        ) VALUES (
            :transportadora, :loja, :data_deposito,
            :total_deposito, :total_credito, :memo_remessa,
            :dif_dep_memo, :dif_dep_cred, :status, :observacao,
            :data_credito_esperada, :editado_em
        )
        ON CONFLICT(transportadora, loja, data_deposito)
        DO UPDATE SET
            total_deposito        = excluded.total_deposito,
            total_credito         = excluded.total_credito,
            memo_remessa          = excluded.memo_remessa,
            dif_dep_memo          = excluded.dif_dep_memo,
            dif_dep_cred          = excluded.dif_dep_cred,
            status                = excluded.status,
            observacao            = excluded.observacao,
            data_credito_esperada = excluded.data_credito_esperada,
            editado_em            = excluded.editado_em
    """
    with _conectar() as conn:
        conn.execute(sql, {
            "transportadora":        transportadora,
            "loja":                  loja,
            "data_deposito":         data_deposito,
            "total_deposito":        dados.get("total_deposito"),
            "total_credito":         dados.get("total_credito"),
            "memo_remessa":          dados.get("memo_remessa"),
            "dif_dep_memo":          dados.get("dif_dep_memo"),
            "dif_dep_cred":          dados.get("dif_dep_cred"),
            "status":                dados.get("status"),
            "observacao":            dados.get("observacao", ""),
            "data_credito_esperada": dados.get("data_credito_esperada"),
            "editado_em":            agora,
        })


def get_ajustes(transportadora: str) -> dict[tuple[str, str], dict]:
    """Retorna {(loja, data_deposito): dados} para a transportadora."""
    inicializar()
    sql = """
        SELECT loja, data_deposito, total_deposito, total_credito,
               memo_remessa, dif_dep_memo, dif_dep_cred,
               status, observacao, data_credito_esperada
        FROM conciliacao_ajustes
        WHERE transportadora = ?
    """
    with _conectar() as conn:
        rows = conn.execute(sql, (transportadora,)).fetchall()
    return {(r["loja"], r["data_deposito"]): dict(r) for r in rows}


def get_resumo_depositos_brinks(
    data_inicio: str | None = None,
    data_fim:    str | None = None,
    loja:        str | None = None,
) -> list[dict]:
    inicializar()
    where, params = [], {}

    if data_inicio:
        where.append("data_deposito >= :di")
        params["di"] = data_inicio
    if data_fim:
        where.append("data_deposito <= :df")
        params["df"] = data_fim
    if loja:
        where.append("loja = :loja")
        params["loja"] = loja

    clause = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
        SELECT
            data_deposito AS data_corte,
            loja,
            nr_serial,
            SUM(valor)  AS total,
            COUNT(*)    AS qtd
        FROM depositos_brinks
        {clause}
        GROUP BY data_deposito, loja, nr_serial
        ORDER BY data_deposito, CAST(loja AS INTEGER)
        """

    with _conectar() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [dict(r) for r in rows]


def get_lancamentos_dia_brinks(data_deposito: str, nr_serial: str) -> list[dict]:
    inicializar()
    sql = """
        SELECT data_inclusao, valor, depositante
        FROM depositos_brinks
        WHERE SUBSTR(data_inclusao, 1, 10) = ? AND nr_serial = ?
        ORDER BY data_inclusao
    """
    with _conectar() as conn:
        rows = conn.execute(sql, (data_deposito, nr_serial)).fetchall()

    return [dict(r) for r in rows]


# ──────────────────────────────────────────────────────────────────────────── #
#  Créditos Brinks                                                              #
# ──────────────────────────────────────────────────────────────────────────── #

def insert_creditos_brinks(registros: list[dict]) -> tuple[int, int]:
    inicializar()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inseridos = 0
    ignorados = 0

    sql = """
        INSERT OR IGNORE INTO creditos_brinks (
            data, loja, historico, debito,
            sequencia, lote, voucher, doc_nro,
            centro_custo, conta_partida,
            arquivo_origem, importado_em
        ) VALUES (
            :data, :loja, :historico, :debito,
            :sequencia, :lote, :voucher, :doc_nro,
            :centro_custo, :conta_partida,
            :arquivo_origem, :importado_em
        )
    """

    with _conectar() as conn:
        for r in registros:
            r["importado_em"] = agora
            cur = conn.execute(sql, r)
            if cur.rowcount:
                inseridos += 1
            else:
                ignorados += 1

    return inseridos, ignorados


def get_creditos_brinks(
    data_inicio: str | None = None,
    data_fim:    str | None = None,
    loja:        str | None = None,
) -> list[dict]:
    inicializar()
    where, params = [], {}

    if data_inicio:
        where.append("data >= :di")
        params["di"] = data_inicio
    if data_fim:
        where.append("data <= :df")
        params["df"] = data_fim
    if loja:
        where.append("loja = :loja")
        params["loja"] = loja

    clause = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
        SELECT data, loja, debito, historico,
               sequencia, lote, voucher, doc_nro,
               centro_custo, conta_partida, arquivo_origem
        FROM creditos_brinks
        {clause}
        ORDER BY data, CAST(loja AS INTEGER)
    """

    with _conectar() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [dict(r) for r in rows]


# ──────────────────────────────────────────────────────────────────────────── #
#  Depósitos Prossegur                                                          #
# ──────────────────────────────────────────────────────────────────────────── #

def insert_depositos_prossegur(registros: list[dict], arquivo_origem: str) -> tuple[int, int]:
    inicializar()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inseridos = 0
    ignorados = 0
    sql = """
        INSERT OR IGNORE INTO depositos_prossegur (
            data_deposito, data_hora, nome_cofre, loja,
            valor, tipo, depositante, cliente, moeda,
            arquivo_origem, importado_em
        ) VALUES (
            :data_deposito, :data_hora, :nome_cofre, :loja,
            :valor, :tipo, :depositante, :cliente, :moeda,
            :arquivo_origem, :importado_em
        )
    """
    with _conectar() as conn:
        for r in registros:
            r["arquivo_origem"] = arquivo_origem
            r["importado_em"]   = agora
            cur = conn.execute(sql, r)
            if cur.rowcount: inseridos += 1
            else:            ignorados += 1
    return inseridos, ignorados


def get_resumo_depositos_prossegur(
    data_inicio: str | None = None,
    data_fim:    str | None = None,
    loja:        str | None = None,
) -> list[dict]:
    """Agrupa por (data_deposito, loja) — 1 linha por loja/dia com soma."""
    inicializar()
    where, params = [], {}
    if data_inicio: where.append("data_deposito >= :di");  params["di"]   = data_inicio
    if data_fim:    where.append("data_deposito <= :df");  params["df"]   = data_fim
    if loja:        where.append("loja = :loja");          params["loja"] = loja
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT data_deposito AS data_corte, loja,
               SUM(valor) AS total, COUNT(*) AS qtd
        FROM depositos_prossegur
        {clause}
        GROUP BY data_deposito, loja
        ORDER BY data_deposito, CAST(loja AS INTEGER)
    """
    with _conectar() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_resumo_depositos_prossegur_com_hora(
    data_inicio: str | None = None,
    data_fim:    str | None = None,
    loja:        str | None = None,
) -> list[dict]:
    """
    Retorna cada lançamento individual com data_hora, para que o motor
    de conciliação possa aplicar o corte de 16h (lançamentos após 16h
    são contabilizados no dia seguinte para comparação com créditos).
    """
    inicializar()
    where, params = [], {}
    if data_inicio: where.append("data_deposito >= :di");  params["di"]   = data_inicio
    if data_fim:    where.append("data_deposito <= :df");  params["df"]   = data_fim
    if loja:        where.append("loja = :loja");          params["loja"] = loja
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT data_deposito, data_hora, loja, valor
        FROM depositos_prossegur
        {clause}
        ORDER BY data_hora, CAST(loja AS INTEGER)
    """
    with _conectar() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_lancamentos_dia_prossegur(data_deposito: str, loja: str) -> list[dict]:
    """Todos os lançamentos de uma loja em um dia (todos os cofres)."""
    inicializar()
    sql = """
        SELECT data_hora, tipo, valor, nome_cofre, depositante, cliente
        FROM depositos_prossegur
        WHERE data_deposito = ? AND loja = ?
        ORDER BY data_hora
    """
    with _conectar() as conn:
        rows = conn.execute(sql, (data_deposito, loja)).fetchall()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────────────────────────────────── #
#  Créditos Prossegur                                                           #
# ──────────────────────────────────────────────────────────────────────────── #

def insert_creditos_prossegur(registros: list[dict]) -> tuple[int, int]:
    inicializar()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inseridos = 0
    ignorados = 0
    sql = """
        INSERT OR IGNORE INTO creditos_prossegur (
            data, loja, historico, debito,
            sequencia, lote, voucher, doc_nro,
            centro_custo, conta_partida,
            arquivo_origem, importado_em
        ) VALUES (
            :data, :loja, :historico, :debito,
            :sequencia, :lote, :voucher, :doc_nro,
            :centro_custo, :conta_partida,
            :arquivo_origem, :importado_em
        )
    """
    with _conectar() as conn:
        for r in registros:
            r["importado_em"] = agora
            cur = conn.execute(sql, r)
            if cur.rowcount: inseridos += 1
            else:            ignorados += 1
    return inseridos, ignorados


def get_creditos_prossegur(
    data_inicio: str | None = None,
    data_fim:    str | None = None,
    loja:        str | None = None,
) -> list[dict]:
    """Agrupa por (data, loja) somando o débito — 1 linha por loja/dia."""
    inicializar()
    where, params = [], {}
    if data_inicio: where.append("data >= :di");   params["di"]   = data_inicio
    if data_fim:    where.append("data <= :df");   params["df"]   = data_fim
    if loja:        where.append("loja = :loja");  params["loja"] = loja
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT data, loja, SUM(debito) AS debito, COUNT(*) AS qtd
        FROM creditos_prossegur
        {clause}
        GROUP BY data, loja
        ORDER BY data, CAST(loja AS INTEGER)
    """
    with _conectar() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]
