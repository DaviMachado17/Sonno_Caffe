-- =====================================================================
-- schema.sql  (linguagem: SQL)
-- Descreve a base de dados. O app.py lê este ficheiro quando arranca.
-- "IF NOT EXISTS" quer dizer: só cria a tabela se ela ainda não existir.
-- =====================================================================

-- Tabela 1: "pedidos". Cada linha é UM pedido de um cliente.
CREATE TABLE IF NOT EXISTS pedidos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT, -- número do pedido (sobe sozinho: 1, 2, 3...)
    modo      TEXT NOT NULL,                     -- "No local" ou "Para levar"
    estado    TEXT NOT NULL DEFAULT 'novo',      -- novo -> pronto -> entregue
    total     REAL NOT NULL,                     -- preço total em euros
    criado_em TEXT NOT NULL DEFAULT (datetime('now','localtime')) -- data e hora
);

-- Tabela 2: "itens". Cada linha é UM produto dentro de um pedido.
-- "pedido_id" liga cada item ao seu pedido (como uma etiqueta).
CREATE TABLE IF NOT EXISTS itens (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id  INTEGER NOT NULL REFERENCES pedidos(id),
    produto    TEXT NOT NULL,     -- nome, ex.: "Café"
    quantidade INTEGER NOT NULL,  -- quantas unidades
    preco      REAL NOT NULL      -- preço de uma unidade
);
