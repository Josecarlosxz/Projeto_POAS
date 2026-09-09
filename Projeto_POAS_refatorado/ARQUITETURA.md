# Arquitetura em 4 camadas — Projeto POAS

Este projeto foi reorganizado a partir da versão original (tudo em `main.py`,
`models.py` e `database.py`) para uma arquitetura em camadas.

## Estrutura

```
Projeto_POAS/
├── main.py                      # monta o app FastAPI e inclui os routers
│
├── presentation/                 # 1) APRESENTAÇÃO — HTTP, templates, DTOs de entrada
│   ├── dependencies.py           # obter_usuario_logado (cookie) e get_current_user (JWT)
│   └── routers/
│       ├── pages.py              # páginas HTML (home, login, cadastro, etc.)
│       ├── auth.py               # cadastro/login/logout (cookie e JWT)
│       ├── noticias.py           # /api/noticias, /api/basquete, /api/ufc, ...
│       ├── videos.py             # /api/videos/{esporte}, /api/buscar-videos
│       ├── times.py              # /api/times/{nome}
│       └── simulador.py          # /simulador-page e confrontos iniciais
│
├── application/                  # 2) APLICAÇÃO — casos de uso, orquestração
│   ├── auth_service.py           # cadastrar_usuario, autenticar_usuario, gerar_token_para
│   ├── noticias_service.py       # filtragem de notícias por esporte
│   ├── videos_service.py         # formatação dos resultados do YouTube
│   └── times_service.py          # busca de times + cache em memória
│
├── domain/                       # 3) DOMÍNIO — regra de negócio pura, sem framework
│   ├── entities/usuario.py       # tabela Usuario (SQLModel)
│   ├── schemas/usuario_schemas.py# UsuarioCadastro, UsuarioLogin, TokenResponse
│   └── repositories/
│       └── usuario_repository.py # interface (contrato) do repositório
│
└── infrastructure/                # 4) INFRAESTRUTURA — banco, segurança, APIs externas
    ├── config.py                  # variáveis de ambiente (.env)
    ├── database.py                # engine/sessão SQLModel
    ├── security.py                # bcrypt + JWT
    ├── repositories/
    │   └── usuario_repository_sql.py  # implementação concreta do repositório
    └── external/
        ├── news_api_client.py     # chamadas cruas à NewsAPI
        ├── youtube_api_client.py  # chamadas cruas à YouTube Data API
        └── sportsdb_client.py     # chamadas cruas à TheSportsDB
```

## Regra de dependência

`presentation` → `application` → `domain` ← `infrastructure`

O `domain` não importa nada de `infrastructure` ou `presentation`. Quem
implementa o contrato definido em `domain/repositories` é a
`infrastructure`, e quem decide *quando* usar esse contrato é a
`application`.

## O que mudou de comportamento

Nada. Todas as rotas, nomes de campos de resposta e regras de filtragem de
notícias foram preservados exatamente como estavam. As únicas mudanças reais
são:

- **Chaves secretas** (`SECRET_KEY`, `NEWS_API_KEY`, `YOUTUBE_API_KEY`) que
  estavam hardcoded no `main.py` agora vêm do arquivo `.env` (veja
  `.env.example`). Como essas chaves já estavam expostas no código-fonte,
  **recomendo fortemente gerar novas chaves** na NewsAPI/YouTube e trocar o
  `SECRET_KEY` antes de colocar isso em produção.
- `models.py` e `database.py` (raiz) foram divididos entre `domain/` e
  `infrastructure/`. Se você tiver algum script fora deste projeto que faça
  `from models import Usuario`, ajuste para
  `from domain.entities.usuario import Usuario`.

## Como rodar

```bash
pip install -r requeriments.txt
cp .env.example .env   # já existe um .env funcional neste pacote, mas revise as chaves
uvicorn main:app --reload
```

## Migrações (Alembic)

`alembic/env.py` foi atualizado para importar de `domain.entities.usuario`
em vez do antigo `models.py`. O restante do fluxo de migração (`alembic
revision`, `alembic upgrade head`) continua igual.
