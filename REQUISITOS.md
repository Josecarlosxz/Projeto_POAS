# Documento de Engenharia de Software

Este documento descreve os requisitos funcionais, não funcionais e as regras de negócio que guiam o desenvolvimento da plataforma esportiva.

---

## ⚙️ Requisitos Funcionais (RF)

- **RF01 – Cadastro de usuário:** O sistema deve permitir que novos usuários realizem seu cadastro.
- **RF02 – Login de usuário:** O sistema deve permitir que usuários cadastrados realizem login na plataforma.
- **RF03 – Visualização de notícias esportivas:** O sistema deve permitir que os usuários visualizem notícias esportivas.
- **RF04 – Visualização de notícias por modalidade:** O sistema deve permitir a visualização de notícias separadas por diferentes modalidades esportivas.
- **RF05 – Busca de notícias esportivas:** O sistema deve permitir que o usuário pesquise notícias esportivas.
- **RF06 – Simulação de campeonatos:** O sistema deve permitir que o usuário simule os resultados de campeonatos.
- **RF07 – Escolha de time favorito:** O sistema deve permitir que o usuário escolha e define seu time favorito.
- **RF08 – Busca de times:** O sistema deve permitir que o usuário pesquise e visualize informações sobre times.
- **RF09 – Visualização de vídeos esportivos:** O sistema deve permitir que os usuários visualizem vídeos relacionados ao conteúdo esportivo.
- **RF10 – Área do usuário:** O sistema deve disponibilizar uma area específica para o usuário após a realização do login.
- **RF11 – Logout:** O sistema deve permitir que o usuário encerre sua sessão na plataforma.
- **RF12 – Inserção de notícias pelo administrador:** O sistema deve permitir que o administrador insira notícias na plataforma.

---

## 🔒 Requisitos Não Funcionais (RNF)

- **RNF01 – Segurança:** O sistema deve garantir a segurança dos dados dos usuários e das informações armazenadas.
- **RNF02 – Usabilidade:** O sistema deve possuir uma interface simples, intuitiva e de fácil utilização.
- **RNF03 – Desempenho:** O sistema deve apresentar bom desempenho durante a navegação e carregamento das informações.
- **RNF04 – Disponibilidade:** O sistema deve disponibilizar as informações esportivas de forma adequada, considerando a utilização de serviços e APIs externas.

---

## 💼 Regras de Negócio (RN)

| Identificador | Título | Descrição |
| :--- | :--- | :--- |
| **RN01** | Cadastro de usuário | O usuário deve informar os dados obrigatórios para realizar o cadastro, não sendo permitido cadastrar um e-mail que já esteja registrado no sistema. |
| **RN02** | Senha do usuário | A senha do usuário deve ser armazenada de forma segura, não sendo salva diretamente em texto simples. |
| **RN03** | Login | Somente usuários cadastrados com e-mail e senha válidos poderão acessar as funcionalidades que exigem autenticação. |
| **RN04** | Sessão do usuário | Após realizar o login, o sistema deve manter a sessão do usuário enquanto ele estiver autenticado. |
| **RN05** | Encerramento da sessão | Ao realizar o logout, o acesso às funcionalidades que exigem autenticação deve ser encerrado. |
| **RN06** | Notícias esportivas | As notícias exibidas no sistema devem possuir informações relacionadas ao conteúdo esportivo e ser apresentadas de forma organizada. |
| **RN07** | Modalidades esportivas | As notícias devem ser organizadas de acordo com suas respectivas modalidades esportivas, quando essa informação estiver disponível. |
| **RN08** | Busca de notícias | A pesquisa de notícias deve retornar apenas conteúdos relacionados aos termos informados pelo usuário. |
| **RN09** | Simulação de campeonatos | O usuário deve escolher os resultados dos confrontos para avançar nas etapas da simulação do campeonato. |
| **RN10** | Resultado da simulação | O sistema deve atualizar os confrontos seguintes de acordo com os resultados escolhidos pelo usuário. |
| **RN11** | Time favorito | O usuário poderá selecionar um time como favorito, e o sistema deve associar essa escolha ao seu perfil. |
| **| RN12** | Busca de times | As informações apresentadas sobre os times devem corresponder aos dados obtidos pela fonte de dados utilizada pelo sistema. |
| **RN13** | Conteúdo em vídeo | Os vídeos apresentados devem estar relacionados ao conteúdo esportivo pesquisado ou à modalidade selecionada. |
| **RN14** | Área do usuário | As informações específicas do usuário somente poderão ser acessadas pelo próprio usuário autenticado. |
| **RN15** | Acesso administrativo | Funcionalidades exclusivas de administrador, como inserção de notícias, devem ser acessíveis somente a usuários com permissão administrativa. |
| **RN16** | Notícias cadastradas pelo administrador | As notícias inseridas manualmente pelo administrador devem conter as informações necessárias para serem exibidas corretamente na plataforma. |
| **RN17** | Segurança de acesso | O sistema deve impedir o acesso direto a funcionalidades protegidas por usuários que não estejam devidamente autenticados ou autorizados. |
| **RN18** | Disponibilidade de dados externos | Quando uma informação depender de uma API externa, o sistema deve tratar possíveis falhas ou indisponibilidade do serviço sem comprometer o funcionamento das demais funcionalidades. |
| **RN19** | Integridade dos dados | O sistema deve evitar o armazenamento de informações inválidas, incompletas ou duplicadas quando houver uma regra específica que impeça isso. |
| **RN20** | Usabilidade | As funcionalidades devem apresentar informações e opções de forma clara, permitindo que o usuário compreenda facilmente como realizar cada ação. |
