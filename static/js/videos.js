let videosAtuais = [];

async function carregarVideos(esporte) {

    try {

        const resposta =
            await fetch(`/api/videos/${esporte}`);

        if (!resposta.ok) {
            throw new Error("Erro ao carregar vídeos");
        }

        const videos =
            await resposta.json();

        videosAtuais = videos;

        mostrarVideos(videos);

    } catch (erro) {

        console.error(erro);

        document.getElementById(
            "feed-videos"
        ).innerHTML = `
            <p>Erro ao carregar vídeos.</p>
        `;
    }
}


// ============================
// MOSTRAR VÍDEOS
// ============================

function mostrarVideos(videos) {

    let html = "";

    videos.forEach(video => {

        html += `
        <div class="video-card">

            <img
                src="${video.thumbnail}"
                alt="${video.titulo}"
            >

            <h3>
                ${video.titulo}
            </h3>

            <p>
                ${video.canal}
            </p>

            <a
                href="https://youtube.com/watch?v=${video.id}"
                target="_blank"
                rel="noopener noreferrer">

                Assistir vídeo →

            </a>

        </div>
        `;
    });

    document.getElementById(
        "feed-videos"
    ).innerHTML = html;
}


// ============================
// PESQUISA GLOBAL NO YOUTUBE
// ============================

document.addEventListener("DOMContentLoaded", function () {

    const campo =
        document.getElementById(
            "campo-pesquisa-videos"
        );

    const botao =
        document.getElementById(
            "btn-pesquisa-videos"
        );


    async function pesquisarVideos() {

        const termo =
            campo.value.trim();


        // Se estiver vazio, volta aos vídeos iniciais
        if (!termo) {

            mostrarVideos(videosAtuais);

            return;
        }


        // Mensagem enquanto pesquisa
        document.getElementById(
            "feed-videos"
        ).innerHTML = `
            <p>🔎 Pesquisando no YouTube...</p>
        `;


        try {

            const resposta =
                await fetch(
                    `/api/buscar-videos?q=${encodeURIComponent(termo)}`
                );


            if (!resposta.ok) {

                throw new Error(
                    "Erro na busca de vídeos"
                );

            }


            const resultados =
                await resposta.json();


            if (resultados.length === 0) {

                document.getElementById(
                    "feed-videos"
                ).innerHTML = `
                    <p>
                        Nenhum vídeo encontrado para
                        "${termo}".
                    </p>
                `;

                return;
            }


            mostrarVideos(resultados);


        } catch (erro) {

            console.error(erro);

            document.getElementById(
                "feed-videos"
            ).innerHTML = `
                <p>
                    ❌ Erro ao realizar a pesquisa.
                </p>
            `;
        }
    }


    botao.addEventListener(
        "click",
        pesquisarVideos
    );


    campo.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Enter") {

                pesquisarVideos();

            }

        }
    );

});