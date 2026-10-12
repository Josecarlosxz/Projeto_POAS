import json
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session

from acesso_dados.campeonato_repository import (
    salvar_campeonato,
    listar_campeonatos as listar_campeonatos_repo,
    obter_campeonato_por_id,
)
from dados.models import Campeonato
from negocio.partida_service import calcular_num_grupos

FORMATOS_FUTEBOL_VALIDOS = {"pontos_corridos", "grupos_playoffs"}
TURNOS_GRUPO_VALIDOS = {"unico", "ida_volta"}


def _validar_e_normalizar_configuracao(esporte: str, configuracao: Optional[str]) -> dict:
    dados_configuracao: dict = {}
    if configuracao:
        try:
            dados_configuracao = json.loads(configuracao)
        except Exception:
            raise HTTPException(status_code=400, detail="Configuração do campeonato inválida")

    if esporte == "Futebol":
        formato = dados_configuracao.get("formato", "pontos_corridos")
        if formato not in FORMATOS_FUTEBOL_VALIDOS:
            raise HTTPException(status_code=400, detail="Formato de futebol inválido")
        dados_configuracao["formato"] = formato

        if formato == "grupos_playoffs":
            turno_grupos = dados_configuracao.get("turno_grupos", "unico")
            if turno_grupos not in TURNOS_GRUPO_VALIDOS:
                raise HTTPException(status_code=400, detail="Opção de rodadas da fase de grupos inválida")
            dados_configuracao["turno_grupos"] = turno_grupos

    elif esporte == "Basquete":
        conferencias = dados_configuracao.get("conferencias")
        if not isinstance(conferencias, dict) or not conferencias:
            raise HTTPException(status_code=400, detail="Informe ao menos uma conferência com seus times")
        if len(conferencias) > 2:
            raise HTTPException(status_code=400, detail="No máximo 2 conferências são suportadas")

        conferencias_normalizadas = {}
        nomes_vistos = set()
        times_vistos = set()

        for nome_conferencia, times_conferencia in conferencias.items():
            nome_normalizado = (nome_conferencia or "").strip()
            if not nome_normalizado:
                raise HTTPException(status_code=400, detail="O nome da conferência não pode ficar em branco")
            if nome_normalizado.lower() in nomes_vistos:
                raise HTTPException(status_code=400, detail="As conferências precisam ter nomes diferentes")
            nomes_vistos.add(nome_normalizado.lower())

            if not isinstance(times_conferencia, list):
                raise HTTPException(status_code=400, detail=f"Times inválidos para a conferência {nome_normalizado}")
            times_normalizados = [t.strip() for t in times_conferencia if t and t.strip()]
            if len(times_normalizados) < 2:
                raise HTTPException(status_code=400, detail=f"A conferência {nome_normalizado} precisa de pelo menos 2 times")

            for time in times_normalizados:
                if time.lower() in times_vistos:
                    raise HTTPException(status_code=400, detail=f"O time '{time}' aparece mais de uma vez entre as conferências")
                times_vistos.add(time.lower())

            conferencias_normalizadas[nome_normalizado] = times_normalizados

        dados_configuracao["conferencias"] = conferencias_normalizadas

        turno_temporada = dados_configuracao.get("turno_temporada", "unico")
        if turno_temporada not in TURNOS_GRUPO_VALIDOS:
            raise HTTPException(status_code=400, detail="Opção de rodadas da temporada inválida")
        dados_configuracao["turno_temporada"] = turno_temporada

    elif esporte == "UFC":
        categorias = dados_configuracao.get("categorias")
        if not isinstance(categorias, dict) or not categorias:
            raise HTTPException(status_code=400, detail="Informe ao menos uma categoria com seus lutadores")

        categorias_normalizadas = {}
        nomes_vistos = set()
        lutadores_vistos = set()

        for nome_categoria, lutadores_categoria in categorias.items():
            nome_normalizado = (nome_categoria or "").strip()
            if not nome_normalizado:
                raise HTTPException(status_code=400, detail="O nome da categoria não pode ficar em branco")
            if nome_normalizado.lower() in nomes_vistos:
                raise HTTPException(status_code=400, detail="As categorias precisam ter nomes diferentes")
            nomes_vistos.add(nome_normalizado.lower())

            if not isinstance(lutadores_categoria, list):
                raise HTTPException(status_code=400, detail=f"Lutadores inválidos para a categoria {nome_normalizado}")
            lutadores_normalizados = [l.strip() for l in lutadores_categoria if l and l.strip()]
            if len(lutadores_normalizados) < 2:
                raise HTTPException(status_code=400, detail=f"A categoria {nome_normalizado} precisa de pelo menos 2 lutadores")

            for lutador in lutadores_normalizados:
                if lutador.lower() in lutadores_vistos:
                    raise HTTPException(status_code=400, detail=f"O lutador '{lutador}' aparece mais de uma vez entre as categorias")
                lutadores_vistos.add(lutador.lower())

            categorias_normalizadas[nome_normalizado] = lutadores_normalizados

        dados_configuracao["categorias"] = categorias_normalizadas

    return dados_configuracao


def criar_campeonato(
    session: Session,
    nome: str,
    esporte: str,
    times: str,
    criador_id: Optional[int],
    configuracao: Optional[str] = None,
):
    try:
        lista_times = json.loads(times)
    except Exception:
        raise HTTPException(status_code=400, detail="Times inválidos")

    lista_times = [t.strip() for t in lista_times if t.strip()]

    if len(lista_times) < 2:
        raise HTTPException(status_code=400, detail="Insira ao menos 2 times")

    if esporte == "Futebol":
        dados_configuracao = _validar_e_normalizar_configuracao(esporte, configuracao)
        if dados_configuracao.get("formato") == "grupos_playoffs":
            calcular_num_grupos(len(lista_times))  # levanta HTTPException se não fechar em grupos de 4
    elif esporte == "Basquete":
        dados_configuracao = _validar_e_normalizar_configuracao(esporte, configuracao)
        times_das_conferencias = [
            time for times_conf in dados_configuracao["conferencias"].values() for time in times_conf
        ]
        if sorted(t.lower() for t in times_das_conferencias) != sorted(t.lower() for t in lista_times):
            raise HTTPException(
                status_code=400,
                detail="Os times informados não batem com os times distribuídos nas conferências"
            )
    elif esporte == "UFC":
        dados_configuracao = _validar_e_normalizar_configuracao(esporte, configuracao)
        lutadores_das_categorias = [
            lutador for lutadores in dados_configuracao["categorias"].values() for lutador in lutadores
        ]
        if sorted(t.lower() for t in lutadores_das_categorias) != sorted(t.lower() for t in lista_times):
            raise HTTPException(
                status_code=400,
                detail="Os lutadores informados não batem com os lutadores distribuídos nas categorias"
            )
    else:
        dados_configuracao = _validar_e_normalizar_configuracao(esporte, configuracao)

    novo_campeonato = Campeonato(
        nome=nome,
        esporte=esporte,
        quantidade_times=len(lista_times),
        times=json.dumps(lista_times),
        criador_id=criador_id,
        configuracao=json.dumps(dados_configuracao) if dados_configuracao else None,
    )
    novo_campeonato = salvar_campeonato(session, novo_campeonato)

    return {
        "id": novo_campeonato.id,
        "nome": novo_campeonato.nome,
        "esporte": novo_campeonato.esporte,
        "quantidade_times": novo_campeonato.quantidade_times,
        "times": lista_times,
        "configuracao": dados_configuracao,
    }


def listar_campeonatos(session: Session):
    campeonatos = listar_campeonatos_repo(session)

    return [
        {
            "id": c.id,
            "nome": c.nome,
            "esporte": c.esporte,
            "quantidade_times": c.quantidade_times,
            "times": json.loads(c.times),
            "configuracao": json.loads(c.configuracao) if c.configuracao else {},
        }
        for c in campeonatos
    ]


def obter_campeonato(session: Session, campeonato_id: int):
    campeonato = obter_campeonato_por_id(session, campeonato_id)

    if not campeonato:
        raise HTTPException(status_code=404, detail="Campeonato não encontrado")

    return {
        "id": campeonato.id,
        "nome": campeonato.nome,
        "esporte": campeonato.esporte,
        "quantidade_times": campeonato.quantidade_times,
        "times": json.loads(campeonato.times),
        "configuracao": json.loads(campeonato.configuracao) if campeonato.configuracao else {},
    }