let campeonatosAtuais = [];

document.addEventListener("DOMContentLoaded", function () {

    carregarCampeonatos();

    const modal = document.getElementById("modal-campeonato");
    const btnAbrir = document.getElementById("btn-abrir-modal");
    const btnFechar = document.getElementById("btn-fechar-modal");
    const inputQuantidade = document.getElementById("quantidade-times");
    const listaInputsTimes = document.getElementById("lista-inputs-times");
    const form = document.getElementById("form-campeonato");

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

    gerarInputsTimes(parseInt(inputQuantidade.value));

    inputQuantidade.addEventListener("input", function () {
        let quantidade = parseInt(inputQuantidade.value);

        if (isNaN(quantidade) || quantidade < 2) quantidade = 2;
        if (quantidade > 32) quantidade = 32;

        inputQuantidade.value = quantidade;
        gerarInputsTimes(quantidade);
    });

    btnAbrir.addEventListener("click", () => modal.classList.remove("hidden"));
    btnFechar.addEventListener("click", () => modal.classList.add("hidden"));

    modal.addEventListener("click", function (event) {
        if (event.target === modal) modal.classList.add("hidden");
    });

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const nome = document.getElementById("nome-campeonato").value.trim();
        const esporte = document.getElementById("esporte-campeonato").value;

        const inputsTimes = document.querySelectorAll(".input-time");
        const times = Array.from(inputsTimes)
            .map(input => input.value.trim())
            .filter(Boolean);

        if (times.length < 2) {
            alert("Insira ao menos 2 times!");
            return;
        }

        const formData = new FormData();
        formData.append("nome", nome);
        formData.append("esporte", esporte);
        formData.append("times", JSON.stringify(times));

        try {
            const resposta = await fetch("/api/campeonatos", {
                method: "POST",
                body: formData
            });

            if (!resposta.ok) throw new Error("Erro ao criar campeonato");

            modal.classList.add("hidden");
            form.reset();
            gerarInputsTimes(parseInt(inputQuantidade.value));

            await carregarCampeonatos();

        } catch (erro) {
            console.error(erro);
            alert("Erro ao criar campeonato. Tente novamente.");
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