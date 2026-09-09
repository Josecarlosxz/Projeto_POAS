document.addEventListener("DOMContentLoaded", async function () {

    const container = document.getElementById("detalhe-campeonato");
    const campeonatoId = container.dataset.id;

    try {
        const resposta = await fetch(`/api/campeonatos/${campeonatoId}`);

        if (!resposta.ok) throw new Error("Campeonato não encontrado");

        const campeonato = await resposta.json();

        const timesOrdenados = [...campeonato.times].sort((a, b) =>
            a.localeCompare(b, "pt-BR", { sensitivity: "base" })
        );

        const linhasTabela = timesOrdenados.map((time, index) => `
            <tr>
                <td class="col-posicao">${index + 1}</td>
                <td class="col-time">
                    <i class="fa-solid fa-shield-halved"></i>
                    <span>${time}</span>
                </td>
            </tr>
        `).join("");

        container.innerHTML = `
            <div class="detalhe-header">
                <a href="/campeonatos-page" class="link-voltar">← Voltar</a>
                <span class="badge-esporte">${campeonato.esporte}</span>
            </div>

            <h1>${campeonato.nome}</h1>
            <p class="detalhe-subtitulo">${campeonato.quantidade_times} times participantes</p>

            <table class="tabela-times">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Time</th>
                    </tr>
                </thead>
                <tbody>
                    ${linhasTabela}
                </tbody>
            </table>
        `;

    } catch (erro) {
        console.error(erro);
        container.innerHTML = "<p>Erro ao carregar campeonato.</p>";
    }
});