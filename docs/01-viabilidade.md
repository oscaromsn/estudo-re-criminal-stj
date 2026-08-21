# 01 — Viabilidade: o que foi testado antes de escolher as fontes

Este documento registra a fase exploratória. Ele existe porque **três das quatro
fontes candidatas foram descartadas por evidência empírica**, e refazer esses testes
custaria dias. Cada descarte abaixo traz o teste que o produziu.

## O problema

A pergunta do estudo é sobre **fundamentos**, o que exige o texto integral das
decisões. Isso descarta de saída qualquer fonte que entregue apenas metadados
processuais — inclusive a mais óbvia.

## Candidata 1 — DataJud (API Pública do CNJ) — **serve como frame, não para fundamento**

O índice `api_publica_stj` tem 3.603.220 documentos e registra os movimentos de
admissibilidade com códigos TPU próprios (429 admitido, 432 não admitido, 15621
negado seguimento por tema RG, 265 sobrestado). Baixamos 32.513 processos com esses
movimentos.

O que ele **não** tem, e por isso não fecha o estudo:

- **Nenhum texto de decisão.**
- **Nenhuma parte ou advogado.** A API pública resguarda esses dados. Um projeto
  vizinho no mesmo workspace (`SU/backend/app/integrations/tribunais/cnj.py`) já
  registra a mesma conclusão após tentar busca por OAB. Sem partes não há eixo
  MP × defesa — a variável central em matéria criminal.
- **O número do tema de repercussão geral não é propagado.** O movimento 15621 chega
  com `nome` vazio e sem `complementosTabelados`, embora a TPU defina o complemento
  `numero_tema_RG`. Controlar pelo tema — o confundidor principal — exigiria o texto.
- **Nenhuma turma de origem.** Varremos 471.397 movimentos: o STJ registra órgão
  julgador por gabinete de ministro, nunca por turma.

Serve, e muito bem, como **esqueleto processual**: classe, assuntos TPU e cronologia.

## Candidata 2 — Íntegras de Decisões Terminativas (dados abertos do STJ) — **descartada**

A descrição do conjunto lista "Recurso Extraordinário" entre os tipos de petição
cobertos, o que o faria perfeito. Não é o caso.

**Teste:** amostramos 7 dias distribuídos pelo biênio — 18/11/2024, 10/02/2025,
03/06/2025, 12/08/2025, 10/03/2026 e outros — totalizando **22.739 registros**.
Resultado: **zero** menções a "extraordinário" nos campos `recurso`, `teor`,
`descricaoMonocratica` ou `processo`. Os códigos de `recurso` efetivamente presentes
são `AgRg`, `EDcl`, `AgInt`, `DESIS`, `PET`, `RCD`. **Salomão não aparece uma única
vez** em todo o período amostrado.

**Causa:** o critério real de seleção é "decisões monocráticas indicadas **pelos
gabinetes de ministros** como terminativas". As decisões de admissibilidade saem pela
secretaria da Vice-Presidência, não por gabinete — ficam fora do escopo.

Nota lateral: o dicionário publicado do conjunto está desatualizado — o campo é
`NM_MINISTRO`, não `ministro`.

## Candidata 3 — SCON (jurisprudência do STJ) — **inacessível**

WAF rejeita requisições programáticas (`Request Rejected`), inclusive com cabeçalhos
de navegador completos. Nenhum dos scrapers existentes no workspace acessa o SCON com
sucesso. Não insistimos: seria contornar uma proteção deliberada.

## Candidata 4 — PDPJ / Jus.br Data Lake — **tecnicamente adequada, bloqueada por credencial**

A `datalake-processos (prd).json` descreve exatamente a forma certa: `/processos` com
filtros por `tribunal`, `idOrgaoJulgador`, `idClasse` e `searchAfter`;
`/processos/{n}/documentos/{id}/texto` para inteiro teor; `/recuperarDocumentoTexto`
em lotes de 50. Nenhum parâmetro de parte é obrigatório.

**Testes:** o host `api-processo.data-lake.pdpj.jus.br` responde e **não está atrás do
WAF** que protege o `portaldeservicos` — sem token devolve um `500` de Keycloak; com
JWT inválido, `401` limpo. O `juscraper` do workspace já envia token gov.br pessoal
para esse host, então a credencial pessoal é ao menos o tipo esperado.

**Por que não seguimos:** a conta do pesquisador é federada via gov.br e não há token
programático — só sessão interativa de 8 horas. E permanecia em aberto se um token
pessoal alcança processo público de terceiro (o único teste registrado usava processo
sigiloso, o que não decide a questão). Deixamos a sonda pronta em
`probe-stj-integra.py` (fora deste repositório) e seguimos por caminho sem
autenticação. **Se o DJEN mudar, esta é a alternativa a retomar.**

## Candidata 5 — Diário da Justiça do próprio STJ — **viável, custosa, mantida como reserva**

O formulário em `processo.stj.jus.br/processo/dj/` indexa exatamente o necessário:
`orgao=5` (Vice-Presidência), `orgao=718` (ARP), `tipo_documento=6` (despacho/decisão),
`tipo_documento=14` (vista para contrarrazões de RE — o marcador de interposição),
além de partes e advogados.

**Obstáculo:** os endpoints de resultado (`/processo/dj/consulta/<tipo>/`) devolvem
apenas o esqueleto do portal via cliente HTTP, mesmo com sessão e cookies — os
resultados são montados no cliente. Exigiria automação de navegador, infraestrutura
que o projeto não tem.

**Continua relevante** por um motivo: é a única fonte para os ~3 meses do biênio que o
DJEN não cobre (ver adiante).

## Escolhida — DJEN, via API pública do CNJ

`GET https://comunicaapi.pje.jus.br/api/v1/comunicacao`. Sem autenticação, sem WAF,
sem captcha. O DJEN **cobre o STJ**, e o órgão **59696** — "SPF Coordenadoria de
Processamento de Decisões Estrangeiras e Recursos para o STF" — é por onde saem as
decisões de admissibilidade.

O campo `texto` traz a decisão integral em HTML, e o cabeçalho tabular traz o polo
ativo, o polo passivo, os advogados com OAB e a assinatura nominal de quem decidiu.
Uma única fonte pública resolve fundamento **e** partes.

**Limite conhecido e não contornável por aqui:** a cobertura do STJ no DJEN começa em
**fins de novembro de 2024**. Agosto, setembro e outubro de 2024 devolvem `count=0`.
O biênio perde cerca de três meses — ver `04-limitacoes-e-vieses.md`.

## Terceira fonte — Atas de Distribuição (CKAN do STJ)

Descoberta ao buscar solução para a turma de origem. Traz, por processo distribuído e
diariamente desde 30/06/2023: `nomeMinistroRelator`, `codigoOrgaoJulgador`
(T5/T6/S3/…), partes com tipo de polo e advogados com OAB.

Resolve a turma **sem inferência**, por junção direta pelo número do processo — muito
superior a um mapeamento gabinete→turma por período, que exigiria acertar as datas de
troca de composição. O mapeamento foi construído mesmo assim, como reserva para
processos anteriores à cobertura, e está em `data/processed/mapa_gabinete_turma.csv`.

## Resumo da decisão

| fonte | fundamento | partes | assunto TPU | turma | veredicto |
|---|:-:|:-:|:-:|:-:|---|
| DataJud | não | não | **sim** | não | frame processual |
| Íntegras STJ | — | — | — | — | não contém o objeto |
| SCON | — | — | — | — | bloqueado |
| PDPJ Data Lake | sim | sim | sim | ? | requer credencial |
| DJe do STJ | sim | sim | não | não | requer navegador |
| **DJEN** | **sim** | **sim** | não | não | **escolhida** |
| **Atas STJ** | não | sim | não | **sim** | **complementar** |
