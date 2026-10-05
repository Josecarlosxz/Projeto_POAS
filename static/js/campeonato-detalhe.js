let campeonatoAtual = null;
let classificacaoCache = null;
let partidasCache = [];
let abaSelecionada = null;

document.addEventListener("DOMContentLoaded", async function () {

    const container = document.getElementById("detalhe-campeonato");
    const campeonatoId = container.dataset.id;

    await carregarDetalheCampeonato(container, campeonatoId);
    await carregarClassificacao(campeonatoId);
    await carregarPartidas(campeonatoId);
});

// Identifica o "modo" de exibição da página a partir do esporte + configuração
// do campeonato. É essa string que decide como renderizar classificação,
// partidas e quais botões aparecem.
function modoExibicao() {
    const esporte = campeonatoAtual?.esporte;
    const config = campeonatoAtual?.configuracao || {};

    if (esporte === "Futebol") {
        return config.formato === "grupos_playoffs" ? "futebol_grupos" : "futebol_pontos_corridos";
    }
    if (esporte === "Basquete") {
        const numConferencias = Object.keys(config.conferencias || {}).length;
        return numConferencias >= 2 ? "basquete_conferencias" : "basquete_unica";
    }
    return "generico";
}

function temAbas(modo) {
    return modo === "futebol_grupos" || modo === "basquete_conferencias";
}

function temPlayoffs(modo) {
    return modo === "futebol_grupos" || modo === "basquete_unica" || modo === "basquete_conferencias";
}

function rotuloAba(nome) {
    return campeonatoAtual.esporte === "Basquete" ? `Conferência ${nome}` : `Grupo ${nome}`;
}

async function carregarDetalheCampeonato(container, campeonatoId) {
    try {
        const resposta = await fetch(`/api/campeonatos/${campeonatoId}`);

        if (!resposta.ok) throw new Error("Campeonato não encontrado");

        campeonatoAtual = await resposta.json();
        const modo = modoExibicao();
        const comPlayoffs = temPlayoffs(modo);

        const rotulosSortear = {
            futebol_pontos_corridos: "Sortear partidas (turno e returno)",
            futebol_grupos: "Sortear fase de grupos",
            basquete_unica: "Sortear temporada",
            basquete_conferencias: "Sortear temporada",
            generico: "Sortear partidas",
        };

        container.innerHTML = `
            <div class="detalhe-header">
                <a href="/campeonatos-page" class="link-voltar">← Voltar</a>
                <span class="badge-esporte">${campeonatoAtual.esporte}</span>
            </div>

            <h1>${campeonatoAtual.nome}</h1>
            <p class="detalhe-subtitulo">${campeonatoAtual.quantidade_times} times participantes</p>

            <div class="secao-classificacao">
                <div class="secao-titulo">
                    <h2>Classificação</h2>
                </div>
                <div id="abas-grupo" class="abas-grupo"></div>
                <div id="classificacao-wrap"></div>
            </div>

            <div class="secao-partidas">
                <div class="secao-titulo">
                    <h2>Partidas</h2>
                    <div class="acoes-partidas">
                        <button id="btn-gerar-partidas" class="btn-gerar-partidas">
                            <i class="fa-solid fa-shuffle"></i> ${rotulosSortear[modo]}
                        </button>
                        ${comPlayoffs ? `
                            <button id="btn-gerar-playoffs" class="btn-gerar-partidas">
                                <i class="fa-solid fa-trophy"></i> Gerar Playoffs
                            </button>
                            <button id="btn-avancar-fase" class="btn-gerar-partidas">
                                <i class="fa-solid fa-forward"></i> Avançar Fase
                            </button>
                        ` : ""}
                    </div>
                </div>
                <div id="partidas-wrap"></div>
            </div>
        `;

        document.getElementById("btn-gerar-partidas").addEventListener("click", async () => {
            const confirmar = confirm(
                comPlayoffs
                    ? "Isso vai sortear a temporada e apagar todas as partidas (incluindo playoffs) desse campeonato. Continuar?"
                    : "Isso vai sortear um novo calendário e apagar as partidas atuais desse campeonato. Continuar?"
            );
            if (!confirmar) return;

            try {
                const resposta = await fetch(`/api/campeonatos/${campeonatoId}/partidas/gerar`, {
                    method: "POST"
                });
                if (!resposta.ok) throw new Error("Erro ao gerar partidas");

                abaSelecionada = null;
                await carregarPartidas(campeonatoId);
                await carregarClassificacao(campeonatoId);
            } catch (erro) {
                console.error(erro);
                alert("Erro ao sortear as partidas. Tente novamente.");
            }
        });

        if (comPlayoffs) {
            document.getElementById("btn-gerar-playoffs").addEventListener("click", async () => {
                try {
                    const resposta = await fetch(`/api/campeonatos/${campeonatoId}/playoffs/gerar`, {
                        method: "POST"
                    });
                    if (!resposta.ok) {
                        const erro = await resposta.json().catch(() => null);
                        throw new Error(erro?.detail || "Erro ao gerar playoffs");
                    }
                    await carregarPartidas(campeonatoId);
                } catch (erro) {
                    console.error(erro);
                    alert(erro.message);
                }
            });

            document.getElementById("btn-avancar-fase").addEventListener("click", async () => {
                try {
                    const resposta = await fetch(`/api/campeonatos/${campeonatoId}/playoffs/avancar`, {
                        method: "POST"
                    });
                    if (!resposta.ok) {
                        const erro = await resposta.json().catch(() => null);
                        throw new Error(erro?.detail || "Erro ao avançar de fase");
                    }
                    const dados = await resposta.json();
                    if (dados.finalizado) {
                        alert(`🏆 Campeão: ${dados.campeao}`);
                    }
                    await carregarPartidas(campeonatoId);
                } catch (erro) {
                    console.error(erro);
                    alert(erro.message);
                }
            });
        }

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

        classificacaoCache = await resposta.json();
        const modo = modoExibicao();

        if (temAbas(modo)) {
            const chaveGrupo = modo === "futebol_grupos" ? "grupos" : "conferencias";
            renderizarAbas(campeonatoId, classificacaoCache[chaveGrupo] || {});
            const nomes = Object.keys(classificacaoCache[chaveGrupo] || {}).sort();
            if (!abaSelecionada || !nomes.includes(abaSelecionada)) {
                abaSelecionada = nomes[0] || null;
            }
            renderizarClassificacaoDaAba(wrap, chaveGrupo);
        } else if (modo === "basquete_unica") {
            // Só 1 conferência: mesmo sem abas, a tabela vem dentro de "conferencias".
            document.getElementById("abas-grupo").innerHTML = "";
            const nomeUnico = Object.keys(classificacaoCache.conferencias || {})[0];
            renderizarTabela(wrap, classificacaoCache.conferencias?.[nomeUnico] || []);
        } else {
            document.getElementById("abas-grupo").innerHTML = "";
            renderizarTabela(wrap, classificacaoCache.classificacao);
        }

    } catch (erro) {
        console.error(erro);
        wrap.innerHTML = "<p>Erro ao carregar classificação.</p>";
    }
}

function renderizarAbas(campeonatoId, grupos) {
    const abasWrap = document.getElementById("abas-grupo");
    if (!abasWrap) return;

    const nomes = Object.keys(grupos).sort();

    abasWrap.innerHTML = nomes.map(nome => `
        <button type="button" class="aba-grupo-btn ${nome === abaSelecionada ? "aba-grupo-btn--ativa" : ""}" data-aba="${nome}">
            ${rotuloAba(nome)}
        </button>
    `).join("");

    abasWrap.querySelectorAll(".aba-grupo-btn").forEach(botao => {
        botao.addEventListener("click", () => {
            abaSelecionada = botao.dataset.aba;
            const modo = modoExibicao();
            const chaveGrupo = modo === "futebol_grupos" ? "grupos" : "conferencias";
            renderizarAbas(campeonatoId, classificacaoCache[chaveGrupo] || {});
            renderizarClassificacaoDaAba(document.getElementById("classificacao-wrap"), chaveGrupo);
            renderizarPartidas(document.getElementById("partidas-wrap"), campeonatoId, partidasCache);
        });
    });
}

function renderizarClassificacaoDaAba(wrap, chaveGrupo) {
    const tabela = classificacaoCache?.[chaveGrupo]?.[abaSelecionada];
    if (!abaSelecionada || !tabela) {
        wrap.innerHTML = "<p>Sorteie a temporada para ver a classificação.</p>";
        return;
    }
    renderizarTabela(wrap, tabela);
}

// Escolhe as colunas certas (futebol x basquete) e delega pro renderizador.
function renderizarTabela(wrap, classificacao) {
    if (campeonatoAtual?.esporte === "Basquete") {
        renderizarClassificacaoBasquete(wrap, classificacao);
    } else {
        renderizarClassificacaoFutebol(wrap, classificacao);
    }
}

function renderizarClassificacaoFutebol(wrap, classificacao) {
    if (!classificacao || !classificacao.length) {
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
                <tbody>${linhas}</tbody>
            </table>
        </div>
    `;
}

function renderizarClassificacaoBasquete(wrap, classificacao) {
    if (!classificacao || !classificacao.length) {
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
                <td class="clf-td-pts">${time.vitorias}</td>
                <td>${time.derrotas}</td>
                <td>${time.jogos}</td>
                <td>${time.pontos_marcados}</td>
                <td>${time.pontos_sofridos}</td>
                <td>${time.saldo_pontos}</td>
                <td>${time.aproveitamento}%</td>
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
                        <th>V</th>
                        <th>D</th>
                        <th>J</th>
                        <th>PF</th>
                        <th>PC</th>
                        <th>SALDO</th>
                        <th>APROV.</th>
                        <th class="clf-td-ultimas">Últimas 5</th>
                    </tr>
                </thead>
                <tbody>${linhas}</tbody>
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

        partidasCache = await resposta.json();
        renderizarPartidas(wrap, campeonatoId, partidasCache);

    } catch (erro) {
        console.error(erro);
        wrap.innerHTML = "<p>Erro ao carregar partidas.</p>";
    }
}

function linhaPartidaHtml(partida, permitirPenaltis) {
    const empatePendente = permitirPenaltis
        && partida.gols_casa !== null && partida.gols_visitante !== null
        && partida.gols_casa === partida.gols_visitante;

    const seletorPenaltis = permitirPenaltis ? `
        <select class="prt-select-penaltis" ${empatePendente ? "" : "style=\"display:none\""}>
            <option value="">Pênaltis: quem venceu?</option>
            <option value="${partida.time_casa}" ${partida.vencedor_penaltis === partida.time_casa ? "selected" : ""}>${partida.time_casa}</option>
            <option value="${partida.time_visitante}" ${partida.vencedor_penaltis === partida.time_visitante ? "selected" : ""}>${partida.time_visitante}</option>
        </select>
    ` : "";

    return `
        <div class="prt-linha ${partida.finalizada ? "prt-linha--finalizada" : ""}" data-partida-id="${partida.id}" data-permite-penaltis="${permitirPenaltis ? "1" : "0"}">
            <span class="prt-time prt-time--casa">${partida.time_casa}</span>
            <input type="number" min="0" class="prt-input input-gols-casa" value="${partida.gols_casa ?? ""}">
            <span>x</span>
            <input type="number" min="0" class="prt-input input-gols-visitante" value="${partida.gols_visitante ?? ""}">
            <span class="prt-time prt-time--visitante">${partida.time_visitante}</span>
            ${seletorPenaltis}
            <button class="prt-btn-salvar">Salvar</button>
        </div>
    `;
}

function renderizarPartidas(wrap, campeonatoId, partidas) {
    if (!partidas.length) {
        wrap.innerHTML = "<p>Nenhuma partida sorteada ainda.</p>";
        return;
    }

    const modo = modoExibicao();
    const permitePenaltisNosPlayoffs = campeonatoAtual.esporte === "Futebol";

    if (modo === "futebol_grupos") {
        const partidasDaAba = partidas.filter(p => p.fase === "grupos" && p.grupo === abaSelecionada);
        const partidasPlayoffs = partidas.filter(p => p.fase === "playoffs");
        const temReturno = partidasDaAba.some(p => p.turno === 2);

        const blocoTemporada = renderizarBlocoRodadas(partidasDaAba, p =>
            temReturno ? `${p.turno === 1 ? "Turno" : "Returno"} · Rodada ${p.rodada}` : `Rodada ${p.rodada}`
        );
        const blocoPlayoffs = renderizarBlocoPorEtapa(partidasPlayoffs, permitePenaltisNosPlayoffs);

        wrap.innerHTML = `
            <div class="prt-lista">
                <h3>Fase de Grupos — ${rotuloAba(abaSelecionada || "")}</h3>
                ${blocoTemporada || "<p>Sorteie a fase de grupos para ver as partidas.</p>"}
                <h3>Playoffs</h3>
                ${blocoPlayoffs || "<p>Playoffs ainda não gerados. Finalize a fase de grupos e clique em \"Gerar Playoffs\".</p>"}
            </div>
        `;

    } else if (modo === "basquete_conferencias") {
        const partidasDaAba = partidas.filter(p => p.fase === null && p.conferencia === abaSelecionada);
        const partidasPlayoffs = partidas.filter(p => p.fase === "playoffs");
        const temReturno = partidasDaAba.some(p => p.turno === 2);

        const blocoTemporada = renderizarBlocoRodadas(partidasDaAba, p =>
            temReturno ? `${p.turno === 1 ? "Turno" : "Returno"} · Rodada ${p.rodada}` : `Rodada ${p.rodada}`
        );
        const blocoPlayoffs = renderizarBlocoPorEtapa(partidasPlayoffs, false);

        wrap.innerHTML = `
            <div class="prt-lista">
                <h3>Temporada — ${rotuloAba(abaSelecionada || "")}</h3>
                ${blocoTemporada || "<p>Sorteie a temporada para ver as partidas.</p>"}
                <h3>Playoffs</h3>
                ${blocoPlayoffs || "<p>Playoffs ainda não gerados. Finalize a temporada e clique em \"Gerar Playoffs\".</p>"}
            </div>
        `;

    } else if (modo === "basquete_unica") {
        const partidasTemporada = partidas.filter(p => p.fase === null);
        const partidasPlayoffs = partidas.filter(p => p.fase === "playoffs");
        const temReturno = partidasTemporada.some(p => p.turno === 2);

        const blocoTemporada = renderizarBlocoRodadas(partidasTemporada, p =>
            temReturno ? `${p.turno === 1 ? "Turno" : "Returno"} · Rodada ${p.rodada}` : `Rodada ${p.rodada}`
        );
        const blocoPlayoffs = renderizarBlocoPorEtapa(partidasPlayoffs, false);

        wrap.innerHTML = `
            <div class="prt-lista">
                <h3>Temporada</h3>
                ${blocoTemporada || "<p>Sorteie a temporada para ver as partidas.</p>"}
                <h3>Playoffs</h3>
                ${blocoPlayoffs || "<p>Playoffs ainda não gerados. Finalize a temporada e clique em \"Gerar Playoffs\".</p>"}
            </div>
        `;

    } else {
        const bloco = renderizarBlocoRodadas(partidas, p => {
            const rotuloTurno = p.turno === 1 ? "Turno" : "Returno";
            return `${rotuloTurno} · Rodada ${p.rodada}`;
        });
        wrap.innerHTML = `<div class="prt-lista">${bloco}</div>`;
    }

    ativarBotoesSalvar(wrap, campeonatoId);
}

function renderizarBlocoRodadas(partidas, rotuloFn) {
    if (!partidas.length) return "";

    const rodadasMap = new Map();
    partidas.forEach(partida => {
        const chave = `${partida.turno}-${partida.rodada}`;
        if (!rodadasMap.has(chave)) rodadasMap.set(chave, []);
        rodadasMap.get(chave).push(partida);
    });

    return [...rodadasMap.entries()].map(([, partidasDaRodada]) => {
        const linhas = partidasDaRodada.map(p => linhaPartidaHtml(p, false)).join("");
        return `
            <div class="prt-rodada">
                <h3>${rotuloFn(partidasDaRodada[0])}</h3>
                ${linhas}
            </div>
        `;
    }).join("");
}

function renderizarBlocoPorEtapa(partidas, permitirPenaltis) {
    if (!partidas.length) return "";

    const blocosMap = new Map();
    partidas.forEach(partida => {
        const chave = `${partida.etapa}||${partida.conferencia || ""}`;
        if (!blocosMap.has(chave)) blocosMap.set(chave, []);
        blocosMap.get(chave).push(partida);
    });

    return [...blocosMap.entries()].map(([chave, partidasDoBloco]) => {
        const [etapa, conferencia] = chave.split("||");
        const titulo = conferencia ? `${etapa} — Conferência ${conferencia}` : etapa;
        const linhas = partidasDoBloco.map(p => linhaPartidaHtml(p, permitirPenaltis)).join("");
        return `
            <div class="prt-rodada">
                <h3>${titulo}</h3>
                ${linhas}
            </div>
        `;
    }).join("");
}

function ativarBotoesSalvar(wrap, campeonatoId) {
    wrap.querySelectorAll(".prt-linha").forEach(linha => {
        const permitePenaltis = linha.dataset.permitePenaltis === "1";
        if (!permitePenaltis) return;

        const inputCasa = linha.querySelector(".input-gols-casa");
        const inputVisitante = linha.querySelector(".input-gols-visitante");
        const seletorPenaltis = linha.querySelector(".prt-select-penaltis");
        if (!seletorPenaltis) return;

        const atualizarVisibilidade = () => {
            const empatado = inputCasa.value !== "" && inputVisitante.value !== ""
                && inputCasa.value === inputVisitante.value;
            seletorPenaltis.style.display = empatado ? "" : "none";
        };
        inputCasa.addEventListener("input", atualizarVisibilidade);
        inputVisitante.addEventListener("input", atualizarVisibilidade);
    });

    wrap.querySelectorAll(".prt-btn-salvar").forEach(botao => {
        botao.addEventListener("click", async (evento) => {
            const linha = evento.target.closest(".prt-linha");
            const partidaId = linha.dataset.partidaId;
            const golsCasa = linha.querySelector(".input-gols-casa").value;
            const golsVisitante = linha.querySelector(".input-gols-visitante").value;
            const seletorPenaltis = linha.querySelector(".prt-select-penaltis");

            if (golsCasa === "" || golsVisitante === "") {
                alert("Preencha o placar dos dois times.");
                return;
            }

            if (campeonatoAtual.esporte === "Basquete" && golsCasa === golsVisitante) {
                alert("Basquete não permite empate — ajuste o placar.");
                return;
            }

            if (seletorPenaltis && seletorPenaltis.style.display !== "none" && golsCasa === golsVisitante && !seletorPenaltis.value) {
                alert("Essa fase é eliminatória: em caso de empate, informe o vencedor nos pênaltis.");
                return;
            }

            try {
                const resposta = await fetch(`/api/partidas/${partidaId}/resultado`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        gols_casa: parseInt(golsCasa, 10),
                        gols_visitante: parseInt(golsVisitante, 10),
                        vencedor_penaltis: seletorPenaltis ? (seletorPenaltis.value || null) : null
                    })
                });

                if (!resposta.ok) {
                    const erro = await resposta.json().catch(() => null);
                    throw new Error(erro?.detail || "Erro ao salvar resultado");
                }

                linha.classList.add("prt-linha--finalizada");
                await carregarClassificacao(campeonatoId);

            } catch (erro) {
                console.error(erro);
                alert(erro.message || "Erro ao salvar o placar. Tente novamente.");
            }
        });
    });
}