document.addEventListener("DOMContentLoaded", async function () {

    const container = document.getElementById("detalhe-campeonato");
    const campeonatoId = container.dataset.id;

    await carregarDetalheCampeonato(container, campeonatoId);
    await carregarClassificacao(campeonatoId);
    await carregarPartidas(campeonatoId);
});

async function carregarDetalheCampeonato(container, campeonatoId) {
    try {
        const resposta = await fetch(`/api/campeonatos/${campeonatoId}`);

        if (!resposta.ok) throw new Error("Campeonato não encontrado");

        const campeonato = await resposta.json();

        container.innerHTML = `
            <div class="detalhe-header">
                <a href="/campeonatos-page" class="link-voltar">← Voltar</a>
                <span class="badge-esporte">${campeonato.esporte}</span>
            </div>

            <h1>${campeonato.nome}</h1>
            <p class="detalhe-subtitulo">${campeonato.quantidade_times} times participantes</p>

            <div class="secao-classificacao">
                <div class="secao-titulo">
                    <h2>Classificação</h2>
                </div>
                <div id="classificacao-wrap"></div>
            </div>

            <div class="secao-partidas">
                <div class="secao-titulo">
                    <h2>Partidas</h2>
                    <button id="btn-gerar-partidas" class="btn-gerar-partidas">
                        <i class="fa-solid fa-shuffle"></i> Sortear partidas (turno e returno)
                    </button>
                </div>
                <div id="partidas-wrap"></div>
            </div>
        `;

        document.getElementById("btn-gerar-partidas").addEventListener("click", async () => {
            const confirmar = confirm(
                "Isso vai sortear um novo calendário (ida e volta) e apagar as partidas atuais desse campeonato. Continuar?"
            );
            if (!confirmar) return;

            try {
                const resposta = await fetch(`/api/campeonatos/${campeonatoId}/partidas/gerar`, {
                    method: "POST"
                });
                if (!resposta.ok) throw new Error("Erro ao gerar partidas");

                await carregarPartidas(campeonatoId);
                await carregarClassificacao(campeonatoId);
            } catch (erro) {
                console.error(erro);
                alert("Erro ao sortear as partidas. Tente novamente.");
            }
        });

    } catch (erro) {
        console.error(erro);
        container.innerHTML = "<p>Erro ao carregar campeonato.</p>";
    }
}

function iconeResultado(resultado) {
    const mapa = {
        V: { classe: "clf-icone--vitoria", icone: "fa-check" },
        E: { classe: "clf-icone--empate", icone: "fa-minus" },
        D: { classe: "clf-icone--derrota", icone: "fa-xmark" },
    };
    const info = mapa[resultado];
    if (!info) {
        return `<span class="clf-icone clf-icone--vazio"></span>`;
    }
    return `<span class="clf-icone ${info.classe}"><i class="fa-solid ${info.icone}"></i></span>`;
}

async function carregarClassificacao(campeonatoId) {
    const wrap = document.getElementById("classificacao-wrap");
    if (!wrap) return;

    try {
        const resposta = await fetch(`/api/campeonatos/${campeonatoId}/classificacao`);
        if (!resposta.ok) throw new Error("Erro ao buscar classificação");

        const classificacao = await resposta.json();
        renderizarClassificacao(wrap, classificacao);

    } catch (erro) {
        console.error(erro);
        wrap.innerHTML = "<p>Erro ao carregar classificação.</p>";
    }
}

function renderizarClassificacao(wrap, classificacao) {
    if (!classificacao.length) {
        wrap.innerHTML = "<p>Nenhum time cadastrado.</p>";
        return;
    }

    const linhas = classificacao.map((time, index) => {
        const ultimos5 = [...time.ultimos_5];
        while (ultimos5.length < 5) ultimos5.unshift(null);

        const iconesHtml = ultimos5.map(resultado => iconeResultado(resultado)).join("");

        return `
            <tr>
                <td class="clf-td-pos">${index + 1}</td>
                <td class="clf-td-nome">${time.time}</td>
                <td class="clf-td-pts">${time.pontos}</td>
                <td>${time.jogos}</td>
                <td>${time.vitorias}</td>
                <td>${time.empates}</td>
                <td>${time.derrotas}</td>
                <td>${time.gols_marcados}</td>
                <td>${time.gols_sofridos}</td>
                <td>${time.saldo_gols}</td>
                <td class="clf-td-ultimas">
                    <div class="clf-icones">${iconesHtml}</div>
                </td>
            </tr>
        `;
    }).join("");

    wrap.innerHTML = `
        <div class="clf-wrap">
            <table class="clf-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th class="clf-th-esquerda">Time</th>
                        <th>Pts</th>
                        <th>PJ</th>
                        <th>VIT</th>
                        <th>E</th>
                        <th>DER</th>
                        <th>GM</th>
                        <th>GC</th>
                        <th>SG</th>
                        <th class="clf-td-ultimas">Últimas 5</th>
                    </tr>
                </thead>
                <tbody>
                    ${linhas}
                </tbody>
            </table>
        </div>
    `;
}

async function carregarPartidas(campeonatoId) {
    const wrap = document.getElementById("partidas-wrap");
    if (!wrap) return;

    try {
        const resposta = await fetch(`/api/campeonatos/${campeonatoId}/partidas`);
        if (!resposta.ok) throw new Error("Erro ao buscar partidas");

        const partidas = await resposta.json();
        renderizarPartidas(wrap, campeonatoId, partidas);

    } catch (erro) {
        console.error(erro);
        wrap.innerHTML = "<p>Erro ao carregar partidas.</p>";
    }
}

function renderizarPartidas(wrap, campeonatoId, partidas) {
    if (!partidas.length) {
        wrap.innerHTML = "<p>Nenhuma partida sorteada ainda. Clique em \"Sortear partidas\" para gerar o calendário.</p>";
        return;
    }

    const rodadasMap = new Map();
    partidas.forEach(partida => {
        const chave = `${partida.turno}-${partida.rodada}`;
        if (!rodadasMap.has(chave)) rodadasMap.set(chave, []);
        rodadasMap.get(chave).push(partida);
    });

    const blocos = [...rodadasMap.entries()].map(([chave, partidasDaRodada]) => {
        const [turno, rodada] = chave.split("-");
        const rotuloTurno = turno === "1" ? "Turno" : "Returno";

        const linhas = partidasDaRodada.map(partida => `
            <div class="prt-linha ${partida.finalizada ? "prt-linha--finalizada" : ""}" data-partida-id="${partida.id}">
                <span class="prt-time prt-time--casa">${partida.time_casa}</span>
                <input type="number" min="0" class="prt-input input-gols-casa" value="${partida.gols_casa ?? ""}">
                <span>x</span>
                <input type="number" min="0" class="prt-input input-gols-visitante" value="${partida.gols_visitante ?? ""}">
                <span class="prt-time prt-time--visitante">${partida.time_visitante}</span>
                <button class="prt-btn-salvar">Salvar</button>
            </div>
        `).join("");

        return `
            <div class="prt-rodada">
                <h3>${rotuloTurno} · Rodada ${rodada}</h3>
                ${linhas}
            </div>
        `;
    }).join("");

    wrap.innerHTML = `<div class="prt-lista">${blocos}</div>`;

    wrap.querySelectorAll(".prt-btn-salvar").forEach(botao => {
        botao.addEventListener("click", async (evento) => {
            const linha = evento.target.closest(".prt-linha");
            const partidaId = linha.dataset.partidaId;
            const golsCasa = linha.querySelector(".input-gols-casa").value;
            const golsVisitante = linha.querySelector(".input-gols-visitante").value;

            if (golsCasa === "" || golsVisitante === "") {
                alert("Preencha o placar dos dois times.");
                return;
            }

            try {
                const resposta = await fetch(`/api/partidas/${partidaId}/resultado`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        gols_casa: parseInt(golsCasa, 10),
                        gols_visitante: parseInt(golsVisitante, 10)
                    })
                });

                if (!resposta.ok) throw new Error("Erro ao salvar resultado");

                linha.classList.add("prt-linha--finalizada");
                await carregarClassificacao(campeonatoId);

            } catch (erro) {
                console.error(erro);
                alert("Erro ao salvar o placar. Tente novamente.");
            }
        });
    });
}