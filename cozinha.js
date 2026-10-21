/* =====================================================================
   cozinha.js  (linguagem: JAVASCRIPT) - o ecrã da cozinha.
   De 3 em 3 segundos pergunta ao servidor pelos pedidos e desenha-os.
   ===================================================================== */
const $ = id => document.getElementById(id);

// Diz ao servidor que o pedido mudou de estado (ex.: "pronto") e recarrega.
async function mudar(id, estado) {
  await fetch(`/api/pedidos/${id}/estado`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ estado })
  });
  carregar();
}

// Cria o cartão de UM pedido, com o botão que muda o estado.
// (textContent em vez de innerHTML: mais seguro contra texto malicioso)
function cartao(p, proximo, rotulo) {
  const d = document.createElement("div");
  d.className = "ped";
  const h = document.createElement("h3");
  h.textContent = "Pedido " + p.id;
  const s = document.createElement("small");
  s.textContent = p.modo + " · " + p.criado_em.slice(11, 16);   // só as horas e minutos
  const ul = document.createElement("ul");
  p.itens.forEach(i => {
    const li = document.createElement("li");
    li.textContent = i.quantidade + "x " + i.produto;
    ul.append(li);
  });
  const b = document.createElement("button");
  b.textContent = rotulo;
  b.onclick = () => mudar(p.id, proximo);
  d.append(h, s, ul, b);
  return d;
}

// Vai buscar os pedidos ao servidor e desenha as duas colunas.
async function carregar() {
  try {
    const r = await fetch("/api/pedidos?estado=novo,pronto");
    const lista = await r.json();
    $("novo").replaceChildren(...lista.filter(p => p.estado === "novo")
      .map(p => cartao(p, "pronto", "Marcar como pronto")));
    $("pronto").replaceChildren(...lista.filter(p => p.estado === "pronto")
      .map(p => cartao(p, "entregue", "Entregue")));
    $("estado").textContent = "Ligado. Atualiza sozinho a cada 3 segundos.";
  } catch (e) {
    $("estado").textContent = "Sem ligação ao servidor.";
  }
}

carregar();                      // carrega já ao abrir
setInterval(carregar, 3000);     // e repete de 3 em 3 segundos (3000 ms)
