const pesquisa = document.getElementById("pesquisa");

function mostrarFavoritosFixados() {
    let favoritos = JSON.parse(localStorage.getItem("timesFavoritos")) || [];

    if (favoritos.length === 0) return "";

    let html = `<h3 style="margin-bottom:12px;">⭐ Seus favoritos</h3>`;

    favoritos.forEach(nome => {
        html += `
        <div class="card-time" style="border: 2px solid #fbbf24; background: #fffbeb;">
            <span style="font-size:32px;">⭐</span>
            <h3>${nome}</h3>
            <p style="color:#b45309; font-weight:bold;">Favoritado</p>
            <button onclick="removerFavorito('${nome}')" style="background:#e63946; color:white; border:none; padding:8px 15px; border-radius:8px; cursor:pointer;">
                ❌ Remover
            </button>
        </div>
        `;
    });

    return html;
}

function atualizarLista(resultadosBusca) {
    let html = mostrarFavoritosFixados();

    if (resultadosBusca.length > 0) {
        html += `<h3 style="margin:16px 0 12px;">🔍 Resultados da busca</h3>`;
    }

    resultadosBusca.forEach(time => {
        let favoritos = JSON.parse(localStorage.getItem("timesFavoritos")) || [];
        let jaFavoritado = favoritos.includes(time.nome);

        html += `
        <div class="card-time" style="${jaFavoritado ? 'border: 2px solid #fbbf24;' : ''}">
            <img src="${time.escudo}" alt="${time.nome}">
            <h3>${time.nome}</h3>
            <p>${time.liga}</p>
            <p>${time.pais}</p>
            ${jaFavoritado
                ? `<span style="color:#f59e0b;">⭐ Já favoritado</span>`
                : `<button onclick="favoritar('${time.nome}')">⭐ Favoritar</button>`
            }
        </div>
        `;
    });

    document.getElementById("lista-times").innerHTML = html;
}

pesquisa.addEventListener("input", async () => {
    const nome = pesquisa.value;

    if (nome.length < 2) {
        atualizarLista([]);
        return;
    }

    const resposta = await fetch(`/api/times/${nome}`);
    const times = await resposta.json();

    atualizarLista(times);
});

function favoritar(nome) {
    if (!USUARIO_LOGADO) {
        window.location.href = "/login-page";
        return;
    }

    let favoritos = JSON.parse(localStorage.getItem("timesFavoritos")) || [];

    if (!favoritos.includes(nome)) {
        favoritos.push(nome);
    }

    localStorage.setItem("timesFavoritos", JSON.stringify(favoritos));

    // Re-renderiza
    const termo = pesquisa.value;
    if (termo.length >= 2) {
        fetch(`/api/times/${termo}`)
            .then(r => r.json())
            .then(times => atualizarLista(times));
    } else {
        atualizarLista([]);
    }
}

function removerFavorito(nome) {
    let favoritos = JSON.parse(localStorage.getItem("timesFavoritos")) || [];

    favoritos = favoritos.filter(f => f !== nome);
    localStorage.setItem("timesFavoritos", JSON.stringify(favoritos));

    const termo = pesquisa.value;
    if (termo.length >= 2) {
        fetch(`/api/times/${termo}`)
            .then(r => r.json())
            .then(times => atualizarLista(times));
    } else {
        atualizarLista([]);
    }
}

mostrarFavoritosFixados();