"""
app.py  (linguagem: PYTHON)
O servidor do Sonno Caffe. Faz 3 coisas:
  1. Mostra as páginas (quiosque e cozinha).
  2. Recebe os pedidos do quiosque e guarda-os na base de dados.
  3. Dá os pedidos à cozinha e deixa-a mudar o estado deles.

Como correr:  pip install -r requirements.txt   e depois   python app.py
"""
import os
import sqlite3                       # biblioteca da base de dados SQLite
from flask import Flask, abort, jsonify, request, send_from_directory

# ---------- Configuração ----------
BASE = os.path.dirname(os.path.abspath(__file__))  # pasta onde este ficheiro está
DB = os.path.join(BASE, "pedidos.db")              # ficheiro da base de dados
SCHEMA = os.path.join(BASE, "schema.sql")          # ficheiro SQL com as tabelas
MODOS = ("No local", "Para levar")                 # valores aceites para "modo"
ESTADOS = ("novo", "pronto", "entregue")           # valores aceites para "estado"

app = Flask(__name__, static_folder=None)          # cria o servidor


def db():
    """Abre uma ligação à base de dados."""
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row   # permite ler colunas pelo nome (p["id"])
    return con


def criar_tabelas():
    """Lê o schema.sql e cria as tabelas (se ainda não existirem)."""
    with open(SCHEMA, encoding="utf-8") as f:
        with db() as con:
            con.executescript(f.read())


# ---------- API: o JavaScript fala com estas rotas ----------
@app.post("/api/pedidos")
def novo_pedido():
    """O quiosque envia aqui um pedido novo. Devolve o número do pedido."""
    dados = request.get_json(silent=True) or {}
    modo, itens = dados.get("modo"), dados.get("itens")

    # Validação: se algo estiver estranho, responde "400" (pedido inválido).
    if modo not in MODOS or not isinstance(itens, list) or not 0 < len(itens) <= 50:
        abort(400)

    limpos = []
    try:
        for i in itens:
            nome = str(i["nome"])[:80]                  # corta nomes enormes
            qtd, preco = int(i["qtd"]), float(i["preco"])
            if not (1 <= qtd <= 50 and 0 <= preco <= 100):
                abort(400)                              # quantidade ou preço absurdos
            limpos.append((nome, qtd, preco))
    except (KeyError, TypeError, ValueError):
        abort(400)                                      # faltam dados ou têm tipo errado

    total = round(sum(q * p for _, q, p in limpos), 2)  # soma quantidade x preço

    with db() as con:
        # Os "?" são preenchidos com os valores (evita "injeção de SQL").
        cur = con.execute("INSERT INTO pedidos (modo, total) VALUES (?, ?)", (modo, total))
        pid = cur.lastrowid                             # número do pedido acabado de criar
        con.executemany(
            "INSERT INTO itens (pedido_id, produto, quantidade, preco) VALUES (?, ?, ?, ?)",
            [(pid, n, q, p) for n, q, p in limpos])
    return jsonify(numero=pid), 201                     # 201 = "criado com sucesso"


@app.get("/api/pedidos")
def listar_pedidos():
    """A cozinha pede aqui a lista. Ex.: /api/pedidos?estado=novo,pronto"""
    estados = [e for e in request.args.get("estado", "novo").split(",") if e in ESTADOS]
    if not estados:
        abort(400)
    marcas = ",".join("?" * len(estados))               # gera "?,?" conforme o nº de estados
    with db() as con:
        pedidos = con.execute(
            f"SELECT * FROM pedidos WHERE estado IN ({marcas}) ORDER BY id", estados).fetchall()
        saida = []
        for p in pedidos:                               # para cada pedido, vai buscar os itens
            itens = con.execute(
                "SELECT produto, quantidade FROM itens WHERE pedido_id = ?", (p["id"],)).fetchall()
            saida.append({**dict(p), "itens": [dict(i) for i in itens]})
    return jsonify(saida)


@app.post("/api/pedidos/<int:pid>/estado")
def mudar_estado(pid):
    """A cozinha muda o estado de um pedido (novo -> pronto -> entregue)."""
    estado = (request.get_json(silent=True) or {}).get("estado")
    if estado not in ESTADOS:
        abort(400)
    with db() as con:
        cur = con.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (estado, pid))
    if cur.rowcount == 0:                               # nenhum pedido com esse número
        abort(404)
    return jsonify(ok=True)


# ---------- Páginas e ficheiros ----------
@app.get("/")
def quiosque():
    return send_from_directory(BASE, "index.html")      # ecrã do cliente


@app.get("/cozinha")
def cozinha():
    return send_from_directory(BASE, "cozinha.html")    # ecrã da cozinha


@app.get("/style.css")
def estilos():
    return send_from_directory(BASE, "style.css")


@app.get("/script.js")
def script_quiosque():
    return send_from_directory(BASE, "script.js")


@app.get("/cozinha.js")
def script_cozinha():
    return send_from_directory(BASE, "cozinha.js")


@app.get("/img/<path:ficheiro>")
def imagens(ficheiro):
    return send_from_directory(os.path.join(BASE, "img"), ficheiro)


# ---------- Arranque ----------
if __name__ == "__main__":
    criar_tabelas()
    # host 0.0.0.0 deixa o tablet abrir o site (mesma rede Wi-Fi). Porta 5000.
    app.run(host="0.0.0.0", port=5000)
