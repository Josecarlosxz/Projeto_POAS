let campeonatosAtuais = [];

document.addEventListener("DOMContentLoaded", function () {

    carregarCampeonatos();

    const modal = document.getElementById("modal-campeonato");
    const btnAbrir = document.getElementById("btn-abrir-modal");
    const btnFechar = document.getElementById("btn-fechar-modal");
    const inputQuantidade = document.getElementById("quantidade-times");
    const listaInputsTimes = document.getElementById("lista-inputs-times");
    const secaoTimesPadrao = document.getElementById("secao-times-padrao");
    const selectEsporte = document.getElementById("esporte-campeonato");
    const opcoesEspecificas = document.getElementById("opcoes-especificas-esporte");
    const form = document.getElementById("form-campeonato");

    function limitarQuantidade(valor) {
        let quantidade = parseInt(valor, 10);
        if (isNaN(quantidade) || quantidade < 2) quantidade = 2;
        if (quantidade > 32) quantidade = 32;
        return quantidade;
    }

    function gerarInputsTimes(quantidade) {
        listaInputsTimes.innerHTML = "";
        for (let i = 1; i <= quantidade; i++) {
            listaInputsTimes.innerHTML += `
                <div class="form-group">
                    <label>Time ${i}</label>
                    <input type="text" class="input-time" placeholder="Nome do time ${i}" required>
                </div>
            `;
        }
    }

    // A seção genérica de times (usada por Futebol, NFL, F1, Outro) some quando
    // o esporte já define os times de outro jeito (Basquete por conferência,
    // UFC por categoria).
    function atualizarVisibilidadeSecaoTimesPadrao(esporte) {
        const temTimesProprios = esporte === "Basquete" || esporte === "UFC";
        secaoTimesPadrao.classList.toggle("hidden", temTimesProprios);
        inputQuantidade.required = !temTimesProprios;
        listaInputsTimes.querySelectorAll(".input-time").forEach(input => {
            input.required = !temTimesProprios;
        });
    }

    function gerarInputsTimesConferencia(containerId, quantidade, rotulo) {
        const container = document.getElementById(containerId);
        container.innerHTML = "";
        for (let i = 1; i <= quantidade; i++) {
            container.innerHTML += `
                <div class="form-group">
                    <label>${rotulo} — Time ${i}</label>
                    <input type="text" class="input-time-conferencia" placeholder="Nome do time ${i}" required>
                </div>
            `;
        }
    }

    // Renderiza os campos extras de acordo com o esporte escolhido.
    function renderizarOpcoesEspecificas(esporte) {
        if (esporte === "Futebol") {
            opcoesEspecificas.innerHTML = `
                <div class="form-group">
                    <label for="formato-futebol">Formato do campeonato</label>
                    <select id="formato-futebol">
                        <option value="pontos_corridos">Pontos corridos</option>
                        <option value="grupos_playoffs">Fase de grupos + playoffs</option>
                    </select>
                    <small class="form-hint">Grupos de 4 times cada — use 8, 16 ou 32 times ao todo.</small>
                </div>
                <div class="form-group campo-rodadas-grupo hidden">
                    <label for="turno-grupos-futebol">Rodadas dentro do grupo</label>
                    <select id="turno-grupos-futebol">
                        <option value="unico">Turno único (3 rodadas)</option>
                        <option value="ida_volta">Ida e volta (6 rodadas)</option>
                    </select>
                </div>
            `;

            const selectFormato = document.getElementById("formato-futebol");
            const campoRodadasGrupo = opcoesEspecificas.querySelector(".campo-rodadas-grupo");

            const atualizarVisibilidadeRodadas = () => {
                campoRodadasGrupo.classList.toggle("hidden", selectFormato.value !== "grupos_playoffs");
            };
            atualizarVisibilidadeRodadas();
            selectFormato.addEventListener("change", atualizarVisibilidadeRodadas);

        } else if (esporte === "Basquete") {
            opcoesEspecificas.innerHTML = `
                <div class="form-group">
                    <label for="turno-temporada-basquete">Rodadas da temporada</label>
                    <select id="turno-temporada-basquete">
                        <option value="unico">Turno único</option>
                        <option value="ida_volta">Ida e volta</option>
                    </select>
                </div>

                <div class="bloco-conferencia">
                    <div class="form-group">
                        <label for="nome-conferencia-1">Nome da conferência</label>
                        <input type="text" id="nome-conferencia-1" required placeholder="Ex: Conferência Leste">
                    </div>
                    <div class="form-group">
                        <label for="qtd-times-conferencia-1">Quantidade de times</label>
                        <input type="number" id="qtd-times-conferencia-1" min="2" max="32" value="4" required>
                    </div>
                    <div id="lista-times-conferencia-1" class="lista-inputs-times"></div>
                </div>

                <div class="bloco-conferencia">
                    <div class="form-group">
                        <label for="nome-conferencia-2">Nome da 2ª conferência (opcional)</label>
                        <input type="text" id="nome-conferencia-2" placeholder="Deixe em branco se for só uma conferência">
                    </div>
                    <div class="form-group campo-qtd-conferencia-2 hidden">
                        <label for="qtd-times-conferencia-2">Quantidade de times</label>
                        <input type="number" id="qtd-times-conferencia-2" min="2" max="32" value="4">
                    </div>
                    <div id="lista-times-conferencia-2" class="lista-inputs-times"></div>
                </div>
            `;

            const qtdConf1 = document.getElementById("qtd-times-conferencia-1");
            gerarInputsTimesConferencia("lista-times-conferencia-1", limitarQuantidade(qtdConf1.value), "Conferência 1");
            qtdConf1.addEventListener("input", () => {
                qtdConf1.value = limitarQuantidade(qtdConf1.value);
                gerarInputsTimesConferencia("lista-times-conferencia-1", parseInt(qtdConf1.value, 10), "Conferência 1");
            });

            const nomeConf2 = document.getElementById("nome-conferencia-2");
            const campoQtdConf2 = opcoesEspecificas.querySelector(".campo-qtd-conferencia-2");
            const qtdConf2 = document.getElementById("qtd-times-conferencia-2");

            const atualizarConferencia2 = () => {
                const temConferencia2 = nomeConf2.value.trim().length > 0;
                campoQtdConf2.classList.toggle("hidden", !temConferencia2);
                qtdConf2.required = temConferencia2;
                if (temConferencia2) {
                    gerarInputsTimesConferencia("lista-times-conferencia-2", limitarQuantidade(qtdConf2.value), "Conferência 2");
                } else {
                    document.getElementById("lista-times-conferencia-2").innerHTML = "";
                }
            };
            nomeConf2.addEventListener("input", atualizarConferencia2);
            qtdConf2.addEventListener("input", () => {
                qtdConf2.value = limitarQuantidade(qtdConf2.value);
                gerarInputsTimesConferencia("lista-times-conferencia-2", parseInt(qtdConf2.value, 10), "Conferência 2");
            });
            atualizarConferencia2();

        } else if (esporte === "UFC") {
            opcoesEspecificas.innerHTML = `
                <div id="lista-categorias-ufc"></div>
                <button type="button" id="btn-add-categoria-ufc" class="btn-gerar-partidas">
                    <i class="fa-solid fa-plus"></i> Adicionar categoria
                </button>
            `;

            const listaCategorias = document.getElementById("lista-categorias-ufc");
            listaCategorias.appendChild(criarBlocoCategoriaUFC());

            document.getElementById("btn-add-categoria-ufc").addEventListener("click", () => {
                listaCategorias.appendChild(criarBlocoCategoriaUFC());
            });

        } else {
            opcoesEspecificas.innerHTML = "";
        }
    }

    function coletarTimesDeConferencia(containerId) {
        return Array.from(document.querySelectorAll(`#${containerId} .input-time-conferencia`))
            .map(input => input.value.trim())
            .filter(Boolean);
    }

    // --- UFC: blocos de categoria (nome + lutadores), com quantas o usuário quiser ---

    function gerarInputsLutadores(container, quantidade, rotulo) {
        container.innerHTML = "";
        for (let i = 1; i <= quantidade; i++) {
            container.innerHTML += `
                <div class="form-group">
                    <label>${rotulo} — Lutador ${i}</label>
                    <input type="text" class="input-lutador-ufc" placeholder="Nome do lutador ${i}" required>
                </div>
            `;
        }
    }

    function criarBlocoCategoriaUFC() {
        const bloco = document.createElement("div");
        bloco.className = "bloco-conferencia bloco-categoria-ufc";
        bloco.innerHTML = `
            <div class="form-group">
                <label>Nome da categoria</label>
                <input type="text" class="input-nome-categoria-ufc" required placeholder="Ex: Peso Pena">
            </div>
            <div class="form-group">
                <label>Quantidade de lutadores</label>
                <input type="number" class="input-qtd-categoria-ufc" min="2" max="32" value="4" required>
            </div>
            <div class="lista-lutadores-categoria-ufc lista-inputs-times"></div>
            <button type="button" class="btn-remover-categoria-ufc">Remover categoria</button>
        `;

        const inputNome = bloco.querySelector(".input-nome-categoria-ufc");
        const inputQtd = bloco.querySelector(".input-qtd-categoria-ufc");
        const listaLutadores = bloco.querySelector(".lista-lutadores-categoria-ufc");

        const atualizarInputsLutadores = () => {
            gerarInputsLutadores(listaLutadores, parseInt(inputQtd.value, 10), inputNome.value.trim() || "Categoria");
        };
        atualizarInputsLutadores();

        inputQtd.addEventListener("input", () => {
            inputQtd.value = limitarQuantidade(inputQtd.value);
            atualizarInputsLutadores();
        });

        bloco.querySelector(".btn-remover-categoria-ufc").addEventListener("click", () => {
            const listaCategorias = document.getElementById("lista-categorias-ufc");
            if (listaCategorias.children.length <= 1) {
                alert("É preciso ao menos uma categoria.");
                return;
            }
            bloco.remove();
        });

        return bloco;
    }

    gerarInputsTimes(parseInt(inputQuantidade.value, 10));
    renderizarOpcoesEspecificas(selectEsporte.value);
    atualizarVisibilidadeSecaoTimesPadrao(selectEsporte.value);

    inputQuantidade.addEventListener("input", function () {
        inputQuantidade.value = limitarQuantidade(inputQuantidade.value);
        gerarInputsTimes(parseInt(inputQuantidade.value, 10));
    });

    selectEsporte.addEventListener("change", function () {
        renderizarOpcoesEspecificas(selectEsporte.value);
        atualizarVisibilidadeSecaoTimesPadrao(selectEsporte.value);
    });

    btnAbrir.addEventListener("click", () => modal.classList.remove("hidden"));
    btnFechar.addEventListener("click", () => modal.classList.add("hidden"));

    modal.addEventListener("click", function (event) {
        if (event.target === modal) modal.classList.add("hidden");
    });

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const nome = document.getElementById("nome-campeonato").value.trim();
        const esporte = selectEsporte.value;

        let times;
        let configuracao;

        if (esporte === "Basquete") {
            const nomeConf1 = document.getElementById("nome-conferencia-1").value.trim();
            const nomeConf2 = document.getElementById("nome-conferencia-2").value.trim();

            if (!nomeConf1) {
                alert("Informe o nome da conferência.");
                return;
            }

            const timesConf1 = coletarTimesDeConferencia("lista-times-conferencia-1");
            if (timesConf1.length < 2) {
                alert(`A conferência "${nomeConf1}" precisa de ao menos 2 times.`);
                return;
            }

            const conferencias = { [nomeConf1]: timesConf1 };
            times = [...timesConf1];

            if (nomeConf2) {
                if (nomeConf2 === nomeConf1) {
                    alert("As duas conferências precisam ter nomes diferentes.");
                    return;
                }
                const timesConf2 = coletarTimesDeConferencia("lista-times-conferencia-2");
                if (timesConf2.length < 2) {
                    alert(`A conferência "${nomeConf2}" precisa de ao menos 2 times.`);
                    return;
                }
                conferencias[nomeConf2] = timesConf2;
                times = times.concat(timesConf2);
            }

            if (new Set(times).size !== times.length) {
                alert("Não repita o nome de um time em conferências diferentes.");
                return;
            }

            configuracao = {
                conferencias,
                turno_temporada: document.getElementById("turno-temporada-basquete").value,
            };

        } else if (esporte === "UFC") {
            const blocosCategoria = document.querySelectorAll("#lista-categorias-ufc .bloco-categoria-ufc");
            if (blocosCategoria.length === 0) {
                alert("Adicione ao menos uma categoria.");
                return;
            }

            const categorias = {};
            let todosLutadores = [];

            for (const bloco of blocosCategoria) {
                const nomeCategoria = bloco.querySelector(".input-nome-categoria-ufc").value.trim();
                if (!nomeCategoria) {
                    alert("Informe o nome de todas as categorias.");
                    return;
                }
                if (categorias[nomeCategoria]) {
                    alert("As categorias precisam ter nomes diferentes.");
                    return;
                }

                const lutadores = Array.from(bloco.querySelectorAll(".input-lutador-ufc"))
                    .map(input => input.value.trim())
                    .filter(Boolean);
                if (lutadores.length < 2) {
                    alert(`A categoria "${nomeCategoria}" precisa de ao menos 2 lutadores.`);
                    return;
                }

                categorias[nomeCategoria] = lutadores;
                todosLutadores = todosLutadores.concat(lutadores);
            }

            if (new Set(todosLutadores).size !== todosLutadores.length) {
                alert("Não repita o nome de um lutador em categorias diferentes.");
                return;
            }

            times = todosLutadores;
            configuracao = { categorias };

        } else {
            times = Array.from(document.querySelectorAll(".input-time"))
                .map(input => input.value.trim())
                .filter(Boolean);

            if (times.length < 2) {
                alert("Insira ao menos 2 times!");
                return;
            }

            configuracao = {};
            if (esporte === "Futebol") {
                const formato = document.getElementById("formato-futebol").value;
                configuracao = { formato };
                if (formato === "grupos_playoffs") {
                    configuracao.turno_grupos = document.getElementById("turno-grupos-futebol").value;

                    const numGrupos = times.length / 4;
                    const numGruposValido = Number.isInteger(numGrupos) && (numGrupos & (numGrupos - 1)) === 0 && numGrupos >= 2;
                    if (!numGruposValido) {
                        alert("A fase de grupos + playoffs exige grupos de 4 times: use 8, 16 ou 32 times ao todo.");
                        return;
                    }
                }
            }
        }

        const formData = new FormData();
        formData.append("nome", nome);
        formData.append("esporte", esporte);
        formData.append("times", JSON.stringify(times));
        formData.append("configuracao", JSON.stringify(configuracao));

        try {
            const resposta = await fetch("/api/campeonatos", {
                method: "POST",
                body: formData
            });

            if (!resposta.ok) {
                const erro = await resposta.json().catch(() => null);
                throw new Error(erro?.detail || "Erro ao criar campeonato");
            }

            modal.classList.add("hidden");
            form.reset();
            gerarInputsTimes(parseInt(inputQuantidade.value, 10));
            renderizarOpcoesEspecificas(selectEsporte.value);
            atualizarVisibilidadeSecaoTimesPadrao(selectEsporte.value);

            await carregarCampeonatos();

        } catch (erro) {
            console.error(erro);
            alert(erro.message || "Erro ao criar campeonato. Tente novamente.");
        }
    });
});

async function carregarCampeonatos() {

    const feed = document.getElementById("feed-campeonatos");

    try {
        const resposta = await fetch("/api/campeonatos");

        if (!resposta.ok) throw new Error("Erro ao buscar campeonatos");

        const campeonatos = await resposta.json();
        campeonatosAtuais = campeonatos;

        renderizarCampeonatos(campeonatos);

    } catch (erro) {
        console.error(erro);
        feed.innerHTML = "<p>Erro ao carregar campeonatos.</p>";
    }
}

function renderizarCampeonatos(campeonatos) {

    const feed = document.getElementById("feed-campeonatos");
    feed.innerHTML = "";

    if (campeonatos.length === 0) {
        feed.innerHTML = "<p>Nenhum campeonato criado ainda. Crie o primeiro!</p>";
        return;
    }

    campeonatos.forEach(campeonato => {

        const card = document.createElement("div");
        card.className = "card-campeonato";

        card.innerHTML = `
            <div class="card-campeonato-topo">
                <span class="badge-esporte">${campeonato.esporte}</span>
                <span class="badge-times">${campeonato.quantidade_times} times</span>
            </div>
            <h3>${campeonato.nome}</h3>
            <p>${campeonato.times.slice(0, 3).join(", ")}${campeonato.times.length > 3 ? "..." : ""}</p>
            <span class="ver-detalhes">Ver detalhes →</span>
        `;

        card.addEventListener("click", () => {
            window.location.href = `/campeonato-page/${campeonato.id}`;
        });

        feed.appendChild(card);
    });
}