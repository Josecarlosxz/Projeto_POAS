async function carregarNoticias() {

    const resposta = await fetch("/api/noticias");
    const noticias = await resposta.json();

    const feed = document.getElementById("feed-noticias");

    feed.innerHTML = "";

    noticias.forEach(noticia => {

        feed.innerHTML += `
        <div class="card-noticia">
            <img src="${noticia.imagem}" alt="">

            <div class="info">
                <span class="fonte">${noticia.fonte}</span>

                <h2>${noticia.titulo}</h2>

                <p>${noticia.descricao || ""}</p>

                <a href="${noticia.link}" target="_blank">
                    Ler matéria →
                </a>
            </div>
        </div>
        `;
    });

}

// Carrega quando abrir a página
carregarNoticias();

// Atualiza a cada 60 segundos
setInterval(carregarNoticias, 60000);