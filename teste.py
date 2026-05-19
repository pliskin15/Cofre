import sqlite3
conn = sqlite3.connect('cofre.db')
rows = conn.execute(
    "SELECT data_deposito, data_hora, valor FROM depositos_prossegur WHERE loja = '49' AND data_deposito = '13/04/2026' ORDER BY data_hora"
).fetchall()
for r in rows:
    print(r)
conn.close()