async function carregarVideos(esporte){

    const resposta =
        await fetch(`/api/videos/${esporte}`);

    const videos =
        await resposta.json();

    let html = "";

    videos.forEach(video => {

        html += `
        <div class="video-card">

            <img src="${video.thumbnail}">

            <h3>
                ${video.titulo}
            </h3>

            <p>
                ${video.canal}
            </p>

            <a
                href="https://youtube.com/watch?v=${video.id}"
                target="_blank">

                Assistir vídeo →

            </a>

        </div>
        `;
    });

    document.getElementById(
        "feed-videos"
    ).innerHTML = html;
}