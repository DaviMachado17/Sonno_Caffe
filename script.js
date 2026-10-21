/* =====================================================================
   script.js  (linguagem: JAVASCRIPT) - o "cérebro" do quiosque.
   Trata dos cliques, do carrinho e envia o pedido ao servidor (Python).
   ===================================================================== */

/* ---------------------------------------------------------------------
   1) CONFIGURAÇÃO: É AQUI QUE SE MUDAM PRODUTOS, PREÇOS E IMAGENS
   Formato de cada produto:  ["Nome", preço, "img/ficheiro.jpg"]
   Põe as fotos na pasta "img". Se faltar a foto, aparece "Sem imagem".
   --------------------------------------------------------------------- */
const LOGO = "img/logo.png";   // logótipo no topo. Usa "" para não ter logótipo.

const MENU = {
  "Pastelaria": [
    ["1000 folhas",        2.0, "img/classico.jpg"],
    ["Delicia de chocolate",    2.0, "img/duplo-queijo.jpg"],
    ["Pão com chouriço", 2.0, "img/frango-crocante.jpg"],
    ["Nata",     1.5, "img/vegetariano.jpg"]
  ],
  "Acompanhamentos": [
    ["Batatas pequenas", 1.9, "img/batatas-pequenas.jpg"],
    ["Batatas grandes",  2.6, "img/batatas-grandes.jpg"],
    ["Nuggets (6)",      3.4, "img/nuggets.jpg"],
    ["Salada",           2.8, "img/salada.jpg"]
  ],
  "Bebidas": [
    ["Refrigerante",    1.9, "img/refrigerante.jpg"],
    ["Água",            1.2, "img/agua.jpg"],
    ["Sumo de laranja", 2.3, "img/sumo-laranja.jpg"],
    ["Café",            1.1, "img/cafe.jpg"]
  ],
  "Sobremesas": [
    ["Gelado",        1.8, "img/gelado.jpg"],
    ["Tarte de maçã", 1.7, "img/tarte-maca.jpg"],
    ["Brownie",       2.1, "img/brownie.jpg"]
  ]
};

/* ---------------------------------------------------------------------
   2) VARIÁVEIS: a "memória" do quiosque
   --------------------------------------------------------------------- */
const $ = id => document.getElementById(id);              // atalho: $("pay") = elemento com id "pay"
const fmt = n => n.toFixed(2).replace(".", ",") + " €";   // 3.9 -> "3,90 €"

let mode = "";                       // "No local" ou "Para levar"
let cat = Object.keys(MENU)[0];      // categoria aberta (começa na primeira)
let cart = {};                       // carrinho: { "Café": {price: 1.1, qty: 2}, ... }

/* ---------------------------------------------------------------------
   3) FUNÇÕES DE ECRÃ
   --------------------------------------------------------------------- */
// Mostra um ecrã ("s1", "s2" ou "s3") e esconde os outros.
function show(id) {
  ["s1", "s2", "s3"].forEach(s => $(s).hidden = (s !== id));
}

// Mostra o logótipo (e esconde-o se o ficheiro não existir).
function renderLogo() {
  const el = $("logo");
  if (!LOGO) { el.hidden = true; return; }
  el.src = LOGO;
  el.hidden = false;
  el.onerror = () => { el.hidden = true; };
}

// Desenha os botões das categorias (Hambúrgueres, Bebidas...).
function renderTabs() {
  $("tabs").innerHTML = "";
  Object.keys(MENU).forEach(c => {
    const b = document.createElement("button");   // cria um botão novo
    b.textContent = c;
    b.setAttribute("aria-pressed", c === cat);    // marca a categoria ativa
    b.onclick = () => { cat = c; renderTabs(); renderGrid(); };
    $("tabs").append(b);                          // põe o botão na página
  });
}

// Desenha os produtos da categoria aberta.
function renderGrid() {
  $("grid").innerHTML = "";
  MENU[cat].forEach(([name, price, img]) => {     // [nome, preço, imagem]
    const b = document.createElement("button");
    b.className = "item";
    // Se a imagem falhar a carregar (onerror), mostra a caixa "Sem imagem".
    const pic = img
      ? `<img src="${img}" alt="${name}" onerror="this.outerHTML='<div class=ph>Sem imagem</div>'">`
      : `<div class="ph">Sem imagem</div>`;
    b.innerHTML = `${pic}<b>${name}</b><span>${fmt(price)}</span>`;
    b.onclick = () => add(name, price);           // clicar no produto = juntar ao carrinho
    $("grid").append(b);
  });
}

/* ---------------------------------------------------------------------
   4) CARRINHO
   --------------------------------------------------------------------- */
// Junta 1 unidade do produto ao carrinho.
function add(name, price) {
  cart[name] = cart[name] || { price, qty: 0 };   // se não existe, cria com 0
  cart[name].qty++;
  renderCart();
}

// Muda a quantidade (+1 ou -1). Se chegar a 0, tira o produto.
function change(name, d) {
  cart[name].qty += d;
  if (cart[name].qty <= 0) delete cart[name];
  renderCart();
}

// Desenha o carrinho e calcula o total.
function renderCart() {
  const ul = $("cart");
  ul.innerHTML = "";
  let total = 0;
  Object.entries(cart).forEach(([name, { price, qty }]) => {
    total += price * qty;
    const li = document.createElement("li");
    li.innerHTML = `<span>${name}</span>
      <div><button aria-label="Retirar ${name}">−</button><b>${qty}</b>
      <button aria-label="Adicionar ${name}">+</button></div>`;
    const [minus, plus] = li.querySelectorAll("button");
    minus.onclick = () => change(name, -1);
    plus.onclick = () => change(name, 1);
    ul.append(li);
  });
  $("total").textContent = fmt(total);
  $("empty").hidden = total > 0;      // esconde "Ainda não escolheu nada"
  $("pay").disabled = (total === 0);  // sem produtos, não deixa pagar
}

// Começa um pedido novo: carrinho vazio e mostra o menu.
function start() {
  cart = {};
  cat = Object.keys(MENU)[0];
  renderTabs(); renderGrid(); renderCart();
  $("mode").textContent = mode;
  show("s2");
}

/* ---------------------------------------------------------------------
   5) BOTÕES (ligam os cliques às funções)
   --------------------------------------------------------------------- */
// "Comer aqui" / "Para levar"
document.querySelectorAll("[data-mode]").forEach(b => {
  b.onclick = () => { mode = b.dataset.mode; start(); };
});
$("reset").onclick = () => { cart = {}; show("s1"); };
$("again").onclick = () => show("s1");

// PAGAR: envia o pedido ao servidor Python e mostra o número.
$("pay").onclick = async () => {
  // Transforma o carrinho numa lista simples para enviar.
  const itens = Object.entries(cart).map(([nome, { price, qty }]) =>
    ({ nome, preco: price, qtd: qty }));
  try {
    const r = await fetch("/api/pedidos", {       // fala com a rota do app.py
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ modo: mode, itens })
    });
    if (!r.ok) throw new Error();                 // servidor recusou
    $("num").textContent = (await r.json()).numero;  // número vindo da base de dados
  } catch (e) {
    alert("Não foi possível enviar o pedido para a cozinha. Chame um funcionário.");
    return;                                       // não avança para o ecrã final
  }
  $("where").textContent = mode === "No local"
    ? "Sente-se e aguarde. Chamamos o seu número."
    : "Aguarde junto ao balcão de recolha.";
  show("s3");
};

renderLogo();   // arranque: mostra o logótipo
