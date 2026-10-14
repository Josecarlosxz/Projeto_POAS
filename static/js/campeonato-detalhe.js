let campeonatoAtual = null;
let classificacaoCache = null;
let partidasCache = [];
let cardsCache = [];
let semanaNflSelecionada = null;
let numerosConfrontoUfc = new Map(); // id da luta -> nº do confronto (1ª vez, 2ª vez...)
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
    if (esporte === "UFC") {
        return "ufc_categorias";
    }
    if (esporte === "NFL") {
        return "nfl";
    }
    return "generico";
}

function temAbas(modo) {
    return modo === "futebol_grupos" || modo === "basquete_conferencias" || modo === "ufc_categorias" || modo === "nfl";
}

function temPlayoffs(modo) {
    return modo === "futebol_grupos" || modo === "basquete_unica" || modo === "basquete_conferencias" || modo === "nfl";
}

function rotuloAba(nome) {
    if (campeonatoAtual.esporte === "Basquete") return `Conferência ${nome}`;
    if (campeonatoAtual.esporte === "UFC" || campeonatoAtual.esporte === "NFL") return nome;
    return `Grupo ${nome}`;
}

function chaveGrupoDoModo(modo) {
    if (modo === "futebol_grupos") return "grupos";
    if (modo === "ufc_categorias") return "categorias";
    return "conferencias";
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
            nfl: "Sortear temporada",
            generico: "Sortear partidas",
        };

        container.innerHTML = `
            <div class="detalhe-header">
                <a href="/campeonatos-page" class="link-voltar">← Voltar</a>
                <span class="badge-esporte">${campeonatoAtual.esporte}</span>
            </div>

            <h1>${campeonatoAtual.nome}</h1>
            <p class="detalhe-subtitulo">${campeonatoAtual.quantidade_times} times participantes</p>

            <div class="detalhe-colunas">
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
                        ${modo === "ufc_categorias" ? "" : `
                            <button id="btn-gerar-partidas" class="btn-gerar-partidas">
                                <i class="fa-solid fa-shuffle"></i> ${rotulosSortear[modo]}
                            </button>
                        `}
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
            </div>
        `;

        const btnGerarPartidas = document.getElementById("btn-gerar-partidas");
        if (btnGerarPartidas) btnGerarPartidas.addEventListener("click", async () => {
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
                semanaNflSelecionada = null;
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
        N: { classe: "clf-icone--nc", icone: "fa-ban" },
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
            const chaveGrupo = chaveGrupoDoModo(modo);
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
            const chaveGrupo = chaveGrupoDoModo(modo);
            renderizarAbas(campeonatoId, classificacaoCache[chaveGrupo] || {});
            renderizarClassificacaoDaAba(document.getElementById("classificacao-wrap"), chaveGrupo);
            // No UFC os cards mostram lutas de todas as categorias; a aba só muda a tabela.
            if (modo !== "ufc_categorias" && modo !== "nfl") {
                renderizarPartidas(document.getElementById("partidas-wrap"), campeonatoId, partidasCache);
            }
        });
    });
}

function renderizarClassificacaoDaAba(wrap, chaveGrupo) {
    if (chaveGrupo === "categorias") {
        const dadosCategoria = classificacaoCache?.categorias?.[abaSelecionada];
        if (!abaSelecionada || !dadosCategoria) {
            wrap.innerHTML = "<p>Nenhum lutador cadastrado.</p>";
            return;
        }
        const faixaCampeao = dadosCategoria.campeao
            ? `<div class="faixa-campeao"><i class="fa-solid fa-trophy"></i> Campeão: <strong>${dadosCategoria.campeao}</strong></div>`
            : `<div class="faixa-campeao faixa-campeao--vazia">Categoria ainda sem campeão.</div>`;
        renderizarTabela(wrap, dadosCategoria.tabela);
        wrap.insertAdjacentHTML("afterbegin", faixaCampeao);
        return;
    }

    const tabela = classificacaoCache?.[chaveGrupo]?.[abaSelecionada];
    if (!abaSelecionada || !tabela) {
        wrap.innerHTML = "<p>Sorteie a temporada para ver a classificação.</p>";
        return;
    }
    if (campeonatoAtual.esporte === "NFL") {
        renderizarClassificacaoNFL(wrap, tabela);
        return;
    }
    renderizarTabela(wrap, tabela);
}

// Escolhe as colunas certas (futebol x vitórias) e delega pro renderizador.
// Basquete (sem empate) e UFC (com empate e NC) têm tabelas por vitórias, cada uma com suas colunas.
function renderizarTabela(wrap, classificacao) {
    if (campeonatoAtual?.esporte === "UFC") {
        renderizarClassificacaoUFC(wrap, classificacao);
    } else if (campeonatoAtual?.esporte === "Basquete") {
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

function formatarAproveitamento(valor) {
    return valor.toFixed(3).replace(/^0/, "");
}

function tabelaTimesNFL(linhas) {
    const corpo = linhas.map((time, index) => {
        const ultimos5 = [...time.ultimos_5];
        while (ultimos5.length < 5) ultimos5.unshift(null);
        const iconesHtml = ultimos5.map(resultado => iconeResultado(resultado)).join("");

        return `
            <tr>
                <td class="clf-td-pos">${index + 1}</td>
                <td class="clf-td-nome">${time.time}</td>
                <td class="clf-td-pts">${time.vitorias}</td>
                <td>${time.derrotas}</td>
                <td>${time.empates}</td>
                <td>${formatarAproveitamento(time.aproveitamento)}</td>
                <td>${time.pontos_marcados}</td>
                <td>${time.pontos_sofridos}</td>
                <td>${time.saldo_pontos}</td>
                <td>${time.record_divisao}</td>
                <td>${time.record_conferencia}</td>
                <td class="clf-td-ultimas">
                    <div class="clf-icones">${iconesHtml}</div>
                </td>
            </tr>
        `;
    }).join("");

    return `
        <div class="clf-wrap">
            <table class="clf-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th class="clf-th-esquerda">Time</th>
                        <th>V</th>
                        <th>D</th>
                        <th>E</th>
                        <th>%</th>
                        <th>PF</th>
                        <th>PC</th>
                        <th>SALDO</th>
                        <th>DIV</th>
                        <th>CONF</th>
                        <th class="clf-td-ultimas">Últimas 5</th>
                    </tr>
                </thead>
                <tbody>${corpo}</tbody>
            </table>
        </div>
    `;
}

// NFL: cabeças de chave (7 vagas) + uma tabela por divisão da conferência escolhida
function renderizarClassificacaoNFL(wrap, dados) {
    const divisoes = dados.divisoes || {};
    const algumJogoFinalizado = Object.values(divisoes).some(linhas => linhas.some(l => l.jogos > 0));

    let blocoSeeds = "";
    if (algumJogoFinalizado) {
        const linhasSeeds = (dados.seeds || []).map(seed => `
            <tr>
                <td class="clf-td-pos">${seed.seed}</td>
                <td class="clf-td-nome">${seed.time}</td>
                <td class="clf-td-vaga">${seed.tipo}${seed.divisao ? ` — ${seed.divisao}` : ""}</td>
            </tr>
        `).join("");

        blocoSeeds = `
            <h3 class="nfl-titulo-secao">Cabeças de chave (playoffs)</h3>
            <div class="clf-wrap">
                <table class="clf-table">
                    <thead>
                        <tr>
                            <th>Seed</th>
                            <th class="clf-th-esquerda">Time</th>
                            <th class="clf-th-esquerda">Vaga</th>
                        </tr>
                    </thead>
                    <tbody>${linhasSeeds}</tbody>
                </table>
            </div>
        `;
    }

    const blocosDivisoes = Object.entries(divisoes).map(([nomeDivisao, linhas]) => `
        <h3 class="nfl-titulo-secao">${nomeDivisao}</h3>
        ${tabelaTimesNFL(linhas)}
    `).join("");

    wrap.innerHTML = blocoSeeds + blocosDivisoes;
}

function renderizarClassificacaoUFC(wrap, classificacao) {
    if (!classificacao || !classificacao.length) {
        wrap.innerHTML = "<p>Nenhum lutador no ranking.</p>";
        return;
    }

    const linhas = classificacao.map((lutador, index) => {
        const ultimos5 = [...lutador.ultimos_5];
        while (ultimos5.length < 5) ultimos5.unshift(null);
        const iconesHtml = ultimos5.map(resultado => iconeResultado(resultado)).join("");

        return `
            <tr>
                <td class="clf-td-pos">${index + 1}</td>
                <td class="clf-td-nome">${lutador.time}</td>
                <td class="clf-td-pts">${lutador.vitorias}</td>
                <td>${lutador.derrotas}</td>
                <td>${lutador.empates}</td>
                <td>${lutador.nc}</td>
                <td>${lutador.jogos}</td>
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
                        <th class="clf-th-esquerda">Lutador</th>
                        <th>V</th>
                        <th>D</th>
                        <th>E</th>
                        <th>NC</th>
                        <th>J</th>
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

        if (modoExibicao() === "ufc_categorias") {
            const respostaCards = await fetch(`/api/campeonatos/${campeonatoId}/cards`);
            if (!respostaCards.ok) throw new Error("Erro ao buscar cards");
            cardsCache = await respostaCards.json();
        }

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
    const modo = modoExibicao();

    // UFC sempre renderiza (mesmo com 0 lutas sorteadas), porque o formulário
    // de luta de título precisa aparecer independente disso.
    if (!partidas.length && modo !== "ufc_categorias") {
        wrap.innerHTML = "<p>Nenhuma partida sorteada ainda.</p>";
        return;
    }

    if (modo === "ufc_categorias") {
        renderizarPartidasUFC(wrap, campeonatoId, partidas);
        return;
    }

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

    } else if (modo === "nfl") {
        const jogosTemporada = partidas.filter(p => p.fase === null);
        const partidasPlayoffs = partidas.filter(p => p.fase === "playoffs");
        const semanas = [...new Set(jogosTemporada.map(p => p.rodada))].sort((a, b) => a - b);

        if (semanaNflSelecionada === null || !semanas.includes(semanaNflSelecionada)) {
            const primeiraPendente = semanas.find(s => jogosTemporada.some(p => p.rodada === s && !p.finalizada));
            semanaNflSelecionada = primeiraPendente ?? semanas[semanas.length - 1] ?? null;
        }

        const jogosDaSemana = jogosTemporada.filter(p => p.rodada === semanaNflSelecionada);
        const opcoesSemana = semanas.map(s =>
            `<option value="${s}" ${s === semanaNflSelecionada ? "selected" : ""}>Semana ${s}</option>`
        ).join("");
        const blocoPlayoffs = renderizarBlocoPorEtapa(partidasPlayoffs, false);

        wrap.innerHTML = `
            <div class="prt-lista">
                <h3>Temporada regular</h3>
                ${semanas.length ? `
                    <div class="seletor-semana">
                        <label>Semana</label>
                        <select class="select-semana-nfl">${opcoesSemana}</select>
                    </div>
                    <div class="prt-rodada">
                        ${jogosDaSemana.map(p => linhaPartidaHtml(p, false)).join("")}
                    </div>
                ` : "<p>Sorteie a temporada para ver os jogos.</p>"}
                <h3>Playoffs</h3>
                ${blocoPlayoffs || "<p>Playoffs ainda não gerados. Finalize a temporada e clique em \"Gerar Playoffs\".</p>"}
            </div>
        `;

        const selectSemana = wrap.querySelector(".select-semana-nfl");
        if (selectSemana) {
            selectSemana.addEventListener("change", () => {
                semanaNflSelecionada = parseInt(selectSemana.value, 10);
                renderizarPartidas(wrap, campeonatoId, partidasCache);
            });
        }

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

// --- UFC: cards (eventos) criados pelo usuário; as lutas são adicionadas dentro de cada card ---

function escaparHtml(texto) {
    return String(texto).replace(/[&<>"']/g, c => (
        { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
    ));
}

async function chamarApiUfc(url, opcoes, mensagemPadrao) {
    const resposta = await fetch(url, opcoes);
    if (!resposta.ok) {
        const erro = await resposta.json().catch(() => null);
        throw new Error(erro?.detail || mensagemPadrao);
    }
    return resposta.json();
}

// Mesmo confronto (mesmos dois lutadores, em qualquer ordem) em cards diferentes ganha número:
// 1ª vez sem número, depois 2, 3... seguindo a ordem dos cards.
function calcularNumerosConfronto(lutas) {
    const ordenadas = [...lutas].sort((a, b) => ((a.card_id ?? 0) - (b.card_id ?? 0)) || (a.id - b.id));
    const contagem = new Map();
    const numeros = new Map();

    ordenadas.forEach(luta => {
        const chave = [luta.time_casa, luta.time_visitante].map(n => n.toLowerCase()).sort().join("||");
        const numero = (contagem.get(chave) || 0) + 1;
        contagem.set(chave, numero);
        numeros.set(luta.id, numero);
    });

    return numeros;
}

function linhaLutaHtml(partida) {
    const ehTitulo = partida.fase === "titulo";
    const numeroConfronto = numerosConfrontoUfc.get(partida.id) || 1;
    const metodos = [["KO", "KO"], ["TKO", "TKO"], ["SUB", "SUB"], ["DEC", "DEC"], ["DQ", "DQ (desqualificação)"]];
    const opcoesVencedor = `
        <option value="">Vencedor</option>
        <option value="${partida.time_casa}" ${partida.finalizada && partida.gols_casa === 1 ? "selected" : ""}>${partida.time_casa}</option>
        <option value="${partida.time_visitante}" ${partida.finalizada && partida.gols_visitante === 1 ? "selected" : ""}>${partida.time_visitante}</option>
        <option value="__empate__" ${partida.metodo_vitoria === "EMPATE" ? "selected" : ""}>Empate</option>
        <option value="__nc__" ${partida.metodo_vitoria === "NC" ? "selected" : ""}>NC (sem resultado)</option>
    `;
    const semVencedor = partida.metodo_vitoria === "EMPATE" || partida.metodo_vitoria === "NC";
    const opcoesMetodo = `<option value="">Método</option>` + metodos.map(([valor, rotulo]) =>
        `<option value="${valor}" ${partida.metodo_vitoria === valor ? "selected" : ""}>${rotulo}</option>`
    ).join("");

    return `
        <div class="prt-linha prt-linha--luta ${partida.finalizada ? "prt-linha--finalizada" : ""}" data-partida-id="${partida.id}">
            <span class="tag-categoria">${escaparHtml(partida.categoria || "")}</span>
            ${ehTitulo ? `<span class="badge-titulo"><i class="fa-solid fa-trophy"></i> Cinturão</span>` : ""}
            <span class="prt-time prt-time--casa">${partida.time_casa}</span>
            <span>vs</span>
            <span class="prt-time prt-time--visitante">${partida.time_visitante}${numeroConfronto > 1 ? ` <span class="numero-confronto">${numeroConfronto}</span>` : ""}</span>
            <select class="prt-select-vencedor">${opcoesVencedor}</select>
            <select class="prt-select-metodo" ${semVencedor ? "disabled" : ""}>${opcoesMetodo}</select>
            <button class="prt-btn-salvar-luta">Salvar</button>
            ${partida.finalizada ? "" : `<button class="prt-btn-remover-luta" title="Remover luta">&times;</button>`}
        </div>
    `;
}

function cardUfcHtml(card, lutas) {
    const categorias = Object.keys(campeonatoAtual.configuracao?.categorias || {});
    const opcoesCategoria = categorias.map(c => `<option value="${escaparHtml(c)}">${escaparHtml(c)}</option>`).join("");

    return `
        <div class="card-ufc" data-card-id="${card.id}">
            <div class="card-ufc-topo">
                <h3>${escaparHtml(card.nome)}</h3>
                <button type="button" class="btn-remover-card" title="Remover card">&times;</button>
            </div>

            ${lutas.map(linhaLutaHtml).join("") || `<p class="card-ufc-vazio">Nenhuma luta nesse card ainda.</p>`}

            <div class="form-luta-titulo form-adicionar-luta">
                <select class="select-luta-categoria">${opcoesCategoria}</select>
                <select class="select-luta-lutador-1"></select>
                <span>vs</span>
                <select class="select-luta-lutador-2"></select>
                <select class="select-luta-tipo">
                    <option value="normal">Luta normal</option>
                    <option value="titulo">Luta pelo cinturão</option>
                </select>
                <button type="button" class="btn-gerar-partidas btn-adicionar-luta">
                    <i class="fa-solid fa-plus"></i> Adicionar luta
                </button>
            </div>
        </div>
    `;
}

function preencherLutadoresDoForm(form) {
    const categoria = form.querySelector(".select-luta-categoria").value;
    const lutadores = campeonatoAtual.configuracao?.categorias?.[categoria] || [];
    const opcoes = lutadores.map(l => `<option value="${escaparHtml(l)}">${escaparHtml(l)}</option>`).join("");

    const select1 = form.querySelector(".select-luta-lutador-1");
    const select2 = form.querySelector(".select-luta-lutador-2");
    select1.innerHTML = opcoes;
    select2.innerHTML = opcoes;
    select2.selectedIndex = Math.min(1, lutadores.length - 1);
}

function renderizarPartidasUFC(wrap, campeonatoId, partidas) {
    const lutasUfc = partidas.filter(p => p.fase === null || p.fase === "titulo");
    numerosConfrontoUfc = calcularNumerosConfronto(lutasUfc);
    const cardsOrdenados = [...cardsCache].sort((a, b) => b.id - a.id);

    const blocosCards = cardsOrdenados.map(card => {
        const lutasDoCard = lutasUfc.filter(p => p.card_id === card.id).sort((a, b) => a.id - b.id);
        return cardUfcHtml(card, lutasDoCard);
    }).join("");

    // Lutas marcadas antes do sistema de cards existir
    const lutasSemCard = lutasUfc.filter(p => p.card_id === null || p.card_id === undefined).sort((a, b) => a.id - b.id);
    const blocoSemCard = lutasSemCard.length ? `
        <div class="card-ufc">
            <div class="card-ufc-topo"><h3>Lutas sem card</h3></div>
            ${lutasSemCard.map(linhaLutaHtml).join("")}
        </div>
    ` : "";

    wrap.innerHTML = `
        <div class="prt-lista">
            <div class="form-criar-card">
                <input type="text" class="input-nome-card" maxlength="80" placeholder="Nome do card (ex: UFC 300)">
                <button type="button" class="btn-gerar-partidas btn-criar-card">
                    <i class="fa-solid fa-plus"></i> Criar card
                </button>
            </div>
            ${blocosCards || "<p>Nenhum card criado ainda. Crie o primeiro para começar a marcar lutas.</p>"}
            ${blocoSemCard}
        </div>
    `;

    ativarBotoesSalvarLutas(wrap, campeonatoId);

    // Criar card
    const inputNomeCard = wrap.querySelector(".input-nome-card");
    const criarCard = async () => {
        const nome = inputNomeCard.value.trim();
        if (!nome) {
            alert("Dê um nome ao card.");
            return;
        }
        try {
            await chamarApiUfc(`/api/campeonatos/${campeonatoId}/cards`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ nome })
            }, "Erro ao criar o card");
            await carregarPartidas(campeonatoId);
        } catch (erro) {
            console.error(erro);
            alert(erro.message);
        }
    };
    wrap.querySelector(".btn-criar-card").addEventListener("click", criarCard);
    inputNomeCard.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter") {
            evento.preventDefault();
            criarCard();
        }
    });

    wrap.querySelectorAll(".card-ufc[data-card-id]").forEach(blocoCard => {
        const cardId = blocoCard.dataset.cardId;

        // Remover card
        blocoCard.querySelector(".btn-remover-card").addEventListener("click", async () => {
            if (!confirm("Remover esse card e as lutas dele que ainda não têm resultado?")) return;
            try {
                await chamarApiUfc(`/api/cards/${cardId}`, { method: "DELETE" }, "Erro ao remover o card");
                await carregarPartidas(campeonatoId);
            } catch (erro) {
                console.error(erro);
                alert(erro.message);
            }
        });

        // Adicionar luta ao card
        const form = blocoCard.querySelector(".form-adicionar-luta");
        preencherLutadoresDoForm(form);
        form.querySelector(".select-luta-categoria").addEventListener("change", () => preencherLutadoresDoForm(form));

        form.querySelector(".btn-adicionar-luta").addEventListener("click", async () => {
            const categoria = form.querySelector(".select-luta-categoria").value;
            const lutador1 = form.querySelector(".select-luta-lutador-1").value;
            const lutador2 = form.querySelector(".select-luta-lutador-2").value;
            const titulo = form.querySelector(".select-luta-tipo").value === "titulo";

            if (!lutador1 || !lutador2 || lutador1 === lutador2) {
                alert("Escolha dois lutadores diferentes.");
                return;
            }

            try {
                await chamarApiUfc(`/api/cards/${cardId}/lutas`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ categoria, lutador_casa: lutador1, lutador_visitante: lutador2, titulo })
                }, "Erro ao adicionar a luta");
                await carregarPartidas(campeonatoId);
            } catch (erro) {
                console.error(erro);
                alert(erro.message);
            }
        });
    });

    // Remover luta ainda sem resultado
    wrap.querySelectorAll(".prt-btn-remover-luta").forEach(botao => {
        botao.addEventListener("click", async (evento) => {
            const linha = evento.target.closest(".prt-linha");
            if (!confirm("Remover essa luta?")) return;
            try {
                await chamarApiUfc(`/api/lutas/${linha.dataset.partidaId}`, { method: "DELETE" }, "Erro ao remover a luta");
                await carregarPartidas(campeonatoId);
            } catch (erro) {
                console.error(erro);
                alert(erro.message);
            }
        });
    });
}

function ativarBotoesSalvarLutas(wrap, campeonatoId) {
    // Empate/NC não têm método de vitória: desabilita o campo de método quando escolhidos
    wrap.querySelectorAll(".prt-linha--luta").forEach(linha => {
        const selectVencedor = linha.querySelector(".prt-select-vencedor");
        const selectMetodo = linha.querySelector(".prt-select-metodo");
        if (!selectVencedor || !selectMetodo) return;

        const atualizarMetodo = () => {
            const semVencedor = selectVencedor.value === "__empate__" || selectVencedor.value === "__nc__";
            selectMetodo.disabled = semVencedor;
            if (semVencedor) selectMetodo.value = "";
        };
        selectVencedor.addEventListener("change", atualizarMetodo);
        atualizarMetodo();
    });

    wrap.querySelectorAll(".prt-btn-salvar-luta").forEach(botao => {
        botao.addEventListener("click", async (evento) => {
            const linha = evento.target.closest(".prt-linha");
            const partidaId = linha.dataset.partidaId;
            const escolha = linha.querySelector(".prt-select-vencedor").value;
            const metodoEscolhido = linha.querySelector(".prt-select-metodo").value;

            // Empate e NC não têm vencedor nem método de vitória
            const semVencedor = escolha === "__empate__" || escolha === "__nc__";
            const vencedor = semVencedor ? null : escolha;
            const metodo = escolha === "__empate__" ? "EMPATE" : escolha === "__nc__" ? "NC" : metodoEscolhido;

            if (!escolha || !metodo) {
                alert("Escolha o resultado da luta (e o método, se houve vencedor).");
                return;
            }

            try {
                const resposta = await fetch(`/api/partidas/${partidaId}/resultado-luta`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ vencedor, metodo })
                });

                if (!resposta.ok) {
                    const erro = await resposta.json().catch(() => null);
                    throw new Error(erro?.detail || "Erro ao salvar o resultado da luta");
                }

                linha.classList.add("prt-linha--finalizada");
                await carregarClassificacao(campeonatoId);
                await carregarPartidas(campeonatoId);

            } catch (erro) {
                console.error(erro);
                alert(erro.message || "Erro ao salvar o resultado. Tente novamente.");
            }
        });
    });
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

                const partidaAtualizada = await resposta.json();
                const posicaoNoCache = partidasCache.findIndex(p => p.id === partidaAtualizada.id);
                if (posicaoNoCache >= 0) partidasCache[posicaoNoCache] = partidaAtualizada;

                linha.classList.add("prt-linha--finalizada");
                await carregarClassificacao(campeonatoId);

            } catch (erro) {
                console.error(erro);
                alert(erro.message || "Erro ao salvar o placar. Tente novamente.");
            }
        });
    });
}