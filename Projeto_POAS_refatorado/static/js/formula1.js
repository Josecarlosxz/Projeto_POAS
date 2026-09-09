async function carregarNoticias() {

    const resposta = await fetch("/api/formula1");

    const noticias = await resposta.json();

    const feed = document.getElementById("feed-noticias");

    feed.innerHTML = "";

    noticias.forEach(noticia => {

        feed.innerHTML += `
        <div class="card-noticia">

            <img src="${noticia.urlToImage}" alt="">

            <div class="info">

                <span class="fonte">
                    ${noticia.source.name}
                </span>

                <h2>
                    ${noticia.title}
                </h2>

                <p>
                    ${noticia.description || ""}
                </p>

                <a href="${noticia.url}" target="_blank">
                    Ler matéria →
                </a>

            </div>

        </div>
        `;
    });

}

carregarNoticias();

setInterval(carregarNoticias, 60000);