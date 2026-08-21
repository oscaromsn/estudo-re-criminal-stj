# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Estudo jurimétrico sobre a admissibilidade de recursos extraordinários criminais no STJ
(biênio 2024–2026 da Vice-Presidência). O repositório é inteiramente em pt-BR — código,
comentários e documentação.

## Comandos

```bash
make ajuda        # lista os alvos
make analise      # tabelas gerais (segundos)
make defesa       # recorte defensivo (segundos)
make cruzamento   # refaz o merge das três fontes (~1 min)
make taxonomia    # reclassifica o corpus DJEN inteiro (~8 min)
make atas         # amplia a cobertura de turma de origem
make coleta       # rebaixa DJEN e DataJud das APIs (~3 h, retomável)
make teste        # 12 testes de fumaça
make limpar       # remove só o regerável
```

Um único teste:

```bash
PYTHONPATH=src python3 -m unittest tests.test_pipeline.TestDispositivo.test_inciso_V_pode_ser_positivo
```

Sem dependências externas — biblioteca padrão apenas (ADR-007). Existe `.venv`/`uv.lock`
por conveniência, mas nada precisa ser instalado. Todo módulo roda como
`PYTHONPATH=src python3 -m estudo_re.<pacote>.<modulo>`.

## Arquitetura

O pipeline é `data/raw → data/interim → data/processed → resultados/`, alimentado por
**três fontes que não se substituem** — cada uma entrega algo que as outras não têm, e
essa é a razão de existirem três:

| fonte | entrega | módulo |
|---|---|---|
| **DJEN** (`comunicaapi.pje.jus.br`) | texto integral da decisão, partes, advogados | `coleta/djen.py` |
| **DataJud** (`api-publica.datajud.cnj.jus.br`) | assunto TPU, classe, movimentos datados | `coleta/datajud.py` |
| **Atas de Distribuição** (CKAN do STJ) | turma de origem e relator do acórdão recorrido | `coleta/atas.py` |

`processamento/taxonomia.py` é o núcleo. Ele classifica cada comunicação do DJEN em
**quatro eixos deliberadamente separados** — colapsá-los destrói a análise:

1. **`tipo_ato`** — pelo prefixo do cabeçalho (`RE no…`, `ARE no…`, `AgInt no RE…`). Sem
   esse eixo, 52% das decisões ficam "não classificado" no dispositivo, porque o órgão
   coletado processa também decisões estrangeiras, recursos ordinários e agravos.
2. **`dispositivo`** — rótulo único do art. 1.030 CPC.
3. **`fundamento`** — ancorado (razão de decidir) e mencionado (qualquer citação), em
   colunas distintas.
4. **partes** — via `processamento/partes.py`, que parseia a tabela HTML do cabeçalho.

`processamento/cruzamento.py` junta as três fontes pelo CNJ só-dígitos e produz
`data/processed/criminais_3fontes.csv`. `analise/resultados.py` e `analise/defesa.py`
geram as 13 tabelas de `resultados/`.

O racional de cada escolha está em `docs/` — leia `03-decisoes-metodologicas.md` (11 ADRs)
antes de alterar classificação, e `04-limitacoes-e-vieses.md` antes de citar qualquer
número. `06-dicionario-de-dados.md` descreve todas as colunas.

## Invariantes que não podem ser quebradas

Estas custaram resultado errado antes de serem descobertas. Os testes em
`tests/test_pipeline.py` travam as duas primeiras.

**O dispositivo é decidido pelo VERBO, nunca pelo inciso (ADR-003).** O art. 1.030, V é o
juízo de admissibilidade e pode ser **positivo** — existem decisões dizendo "nos termos do
art. 1.030, V, c, admito o recurso extraordinário". Classificar pelo inciso inverte o
resultado. Pelo mesmo motivo, `"não admito"` contém `"admito"`: o lookbehind negativo é
obrigatório.

**A classificação lê só o parágrafo dispositivo (ADR-002).** Segmentar no último marcador
("Ante o exposto" e variantes) e classificar apenas até "Publique-se". Aplicar as regex ao
texto inteiro faz uma decisão que *discute* um inciso e *decide* por outro receber os dois
rótulos.

**Análise por turma usa somente `turma_fonte == "ata_direta"`.** O grupo resolvido pelo
mapa gabinete→turma tem perfil estruturalmente distinto (≈62% de inadmissão e ≈61% de MP
recorrente, contra ≈15% e ≈18% no observado) — são processos que só tiveram "Registro",
sem distribuição a turma. Misturar contamina.

**O agravo interno nunca é reportado agregado.** A taxa de reconsideração de ~13% é puxada
pelo MP (37,8%); a da defesa é 1,4%.

## Contratos das APIs

Detalhe completo em `docs/02-fontes-e-contratos.md`. O que mais derruba código novo:

**DJEN** — o filtro de órgão é `orgaoId`; `idOrgao` e `nomeOrgao` **não existem e são
ignorados em silêncio**, devolvendo o diário nacional inteiro com cara de resultado
legítimo. Com `itensPorPagina > 5` é obrigatório mandar também `siglaTribunal`. `count`
satura em 10000 — é teto, não total, daí o recorte por dia. Envelope real:
`{status, message, count, items}`; paginação por `pagina` + `itensPorPagina`.

**DataJud** — `movimentos` **não é `nested`**: combinar `movimentos.codigo` com `range` em
`movimentos.dataHora` casa campos de movimentos diferentes. Filtre data no cliente. Ordene
por `id.keyword` (`_id` é recusado). O índice tem mojibake recuperável com
`s.encode("latin-1").decode("utf-8")`.

**Atas** — a última distribuição de um processo com RE é o "Registro" à Vice-Presidência,
gravado com `codigoOrgaoJulgador` **nulo**. A turma está nas distribuições anteriores.

## Ao adicionar análise

Análise exploratória inline é legítima para descobrir se vale a pena. **O que entrar em
resposta ou conclusão precisa virar módulo em `analise/`, com tabela em `resultados/` e
entrada em `docs/`.** Classificações normativas — que atribuem juízo em vez de ler o que o
texto diz — precisam de ADR próprio declarando os grupos, como em ADR-011.

## O corpus NÃO está no repositório

`data/raw/`, `data/interim/` e os dois CSVs de microdados em `data/processed/`
(`decisoes_admissibilidade.csv`, `criminais_3fontes.csv`) estão no `.gitignore` e **nunca
devem ser commitados**. O corpus traz nome civil de acusados em processos criminais e
advogados com OAB — dados públicos, vindos do DJEN, mas republicá-los em massa,
estruturados e indexáveis, é outra coisa.

O que está versionado: código, documentação, as 13 tabelas agregadas de `resultados/`, as
tabelas de referência do CNJ e os metadados de composição de turmas (só agentes públicos).

Para trabalhar com dados, regenere localmente:

```bash
make coleta      # ~3 h, retomável — rebaixa DJEN e DataJud
make atas        # turma de origem
make taxonomia   # classificação
make cruzamento  # merge das três fontes
```

`make analise` e `make defesa` funcionam a partir de `data/processed/`, que só existe
após o passo acima.

**Git LFS** está configurado (`git lfs install --local`, regras em `.gitattributes` por
extensão para `*.gz`). Hoje ele carrega só as tabelas de referência do CNJ; as regras
existem para que qualquer dado grande que venha a ser versionado no futuro caia em LFS
automaticamente, em vez de inchar o histórico.

Os `.gitkeep` em `data/raw/`, `data/interim/` e `resultados/` mantêm a estrutura no clone
— não os remova.
