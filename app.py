"""Servidor do Sonno Caffe (Python + Flask + SQLite).

Recebe os pedidos do quiosque, guarda-os na base de dados e
mostra-os no ecrã da cozinha.

Como correr:   pip install -r requirements.txt
               python app.py
"""
import os
import sqlite3

from flask import Flask, abort, jsonify, request, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "pedidos.db")        # ficheiro da base de dados (criado sozinho)
MODOS = ("No local", "Para levar")
ESTADOS = ("novo", "pronto", "entregue")

app = Flask(__name__, static_folder=None)


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def criar_tabelas():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            modo      TEXT NOT NULL,
            estado    TEXT NOT NULL DEFAULT 'novo',
            total     REAL NOT NULL,
            criado_em TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS itens (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id  INTEGER NOT NULL REFERENCES pedidos(id),
            produto    TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco      REAL NOT NULL
        );
        """)


# ---------- API ----------
@app.post("/api/pedidos")
def novo_pedido():
    dados = request.get_json(silent=True) or {}
    modo, itens = dados.get("modo"), dados.get("itens")
    if modo not in MODOS or not isinstance(itens, list) or not 0 < len(itens) <= 50:
        abort(400)
    limpos = []
    try:
        for i in itens:
            nome = str(i["nome"])[:80]
            qtd, preco = int(i["qtd"]), float(i["preco"])
            if not (1 <= qtd <= 50 and 0 <= preco <= 100):
                abort(400)
            limpos.append((nome, qtd, preco))
    except (KeyError, TypeError, ValueError):
        abort(400)
    total = round(sum(q * p for _, q, p in limpos), 2)
    with db() as con:
        cur = con.execute("INSERT INTO pedidos (modo, total) VALUES (?, ?)", (modo, total))
        pid = cur.lastrowid
        con.executemany(
            "INSERT INTO itens (pedido_id, produto, quantidade, preco) VALUES (?, ?, ?, ?)",
            [(pid, n, q, p) for n, q, p in limpos])
    return jsonify(numero=pid), 201


@app.get("/api/pedidos")
def listar_pedidos():
    estados = [e for e in request.args.get("estado", "novo").split(",") if e in ESTADOS]
    if not estados:
        abort(400)
    marcas = ",".join("?" * len(estados))
    with db() as con:
        pedidos = con.execute(
            f"SELECT * FROM pedidos WHERE estado IN ({marcas}) ORDER BY id", estados).fetchall()
        saida = []
        for p in pedidos:
            itens = con.execute(
                "SELECT produto, quantidade FROM itens WHERE pedido_id = ?", (p["id"],)).fetchall()
            saida.append({**dict(p), "itens": [dict(i) for i in itens]})
    return jsonify(saida)


@app.post("/api/pedidos/<int:pid>/estado")
def mudar_estado(pid):
    estado = (request.get_json(silent=True) or {}).get("estado")
    if estado not in ESTADOS:
        abort(400)
    with db() as con:
        cur = con.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (estado, pid))
    if cur.rowcount == 0:
        abort(404)
    return jsonify(ok=True)


# ---------- Páginas ----------
@app.get("/")
def quiosque():
    return send_from_directory(BASE, "index.html")


@app.get("/cozinha")
def cozinha():
    return send_from_directory(BASE, "cozinha.html")


@app.get("/style.css")
def estilos():
    return send_from_directory(BASE, "style.css")


@app.get("/img/<path:ficheiro>")
def imagens(ficheiro):
    return send_from_directory(os.path.join(BASE, "img"), ficheiro)


if __name__ == "__main__":
    criar_tabelas()
    # host 0.0.0.0 permite abrir a partir do tablet, na mesma rede Wi-Fi
    app.run(host="0.0.0.0", port=5000)
