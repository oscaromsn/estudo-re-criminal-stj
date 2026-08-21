# 06 — Dicionário de dados

---

## `data/processed/decisoes_admissibilidade.csv` — 28.423 linhas

Uma linha por **decisão de admissibilidade de RE publicada** no DJEN. Universo do
estudo antes de qualquer recorte por matéria.

| coluna | tipo | descrição |
|---|---|---|
| `id` | int | identificador da comunicação no DJEN |
| `data` | data | disponibilização no diário (AAAA-MM-DD) |
| `processo` | texto | número CNJ com máscara |
| `classe` | texto | classe processual, como o DJEN informa |
| `criminal` | bool | feito criminal, derivado das partes (ADR-005) |
| `dispositivo` | categoria | **rótulo único**, ancorado no parágrafo dispositivo (ADR-002/003) |
| `inciso_citado` | texto | inciso do art. 1.030 citado no dispositivo — analítico, **não** decisório |
| `fundamentos` | multi | fundamentos **ancorados**, separados por `\|` (ADR-009) |
| `temas_rg` | texto | números de tema de repercussão geral citados, separados por vírgula |
| `polo_recorrente` | categoria | `MP` · `defesa/particular` · `sem MP no feito` |
| `tipo_recorrente` | categoria | `MP` · `Defensoria` · `ente_publico` · `pessoa_juridica` · `pessoa_fisica` · `anonimizado` |
| `n_advogados` | int | advogados constituídos no cabeçalho |
| `defensoria` | bool | Defensoria Pública atuando |
| `anonimizado` | bool | parte grafada por iniciais (sigilo parcial) |
| `assinatura` | texto | quem assinou — `Vice-Presidente LUIS FELIPE SALOMÃO` ou `Presidente HERMAN BENJAMIN` |

### Valores de `dispositivo`

| valor | significado | n |
|---|---|---:|
| `nega_seg_1030_I` | nega seguimento — conformidade com entendimento do STF | 22.290 |
| `inadmite_1030_V` | inadmite no juízo de admissibilidade | 3.234 |
| `admite` | admite e remete ao STF | 740 |
| `sobresta_1030_III` | sobresta por tema afetado | 660 |
| `retratacao_1030_II` | encaminha ao órgão julgador para retratação | 442 |
| `transito_arquiva` · `prejudicado_perda_objeto` · `intima_gratuidade` · `intima_preparo` · `misto_I_e_V` · `suspeicao_impedimento` · `desistencia_homologada` | atos processuais diversos | 738 |
| `nao_classificado` | nenhuma regra casou (1,1%) | 312 |

### Valores de `fundamentos`

`rg_tema_conformidade` · `sum279_reexame_prova` · `sum280_norma_local` ·
`sum281_nao_esgotamento` · `sum282_356_prequest` · `sum283_fund_autonomo` ·
`sum284_deficiencia` · `sum286_sum7stj` · `ofensa_reflexa` ·
`rg_preliminar_ausente` · `repetitivo_conformidade` · `intempestivo` ·
`deserto_preparo` · `nao_classificado`

---

## `data/processed/criminais_3fontes.csv` — 6.819 linhas

Decisões **criminais** que casaram com o DataJud, enriquecidas com assunto TPU e turma
de origem. Base da análise por matéria e por órgão.

Herda as colunas acima e acrescenta:

| coluna | fonte | descrição |
|---|---|---|
| `assunto_criminal` | DataJud | primeiro assunto TPU dentro da árvore criminal |
| `assuntos_todos` | DataJud | todos os assuntos do processo |
| `turma_origem` | Atas | Quinta Turma · Sexta Turma · Terceira Seção · … · `nao resolvida` |
| `turma_fonte` | derivado | como a turma foi obtida: `ata_direta` (evento de Distribuição com órgão — observação) · `mapa_relator` (inferida pelo mapa gabinete→turma) · `nao resolvida` |
| `relator_origem` | Atas | ministro relator do acórdão recorrido |

**Atenção:** filtre por `turma_fonte == "ata_direta"` para qualquer análise por turma.
O grupo `mapa_relator` é inferido e tem perfil estruturalmente distinto; o grupo
`nao resolvida` (22%) não é aleatório. Ver limitação 3.

---

## `data/interim/taxonomia_completa.csv.gz` — 64.046 linhas

Todos os tipos de ato do órgão 59696, não só admissibilidade. Acrescenta:

| coluna | descrição |
|---|---|
| `tipo_ato` | `RE_admiss` · `SE_CR` · `ARE_1042` · `RO_const` · `AgInt_1030_p2` · `EDcl_no_RE` · `incid_PET` · `pauta_desist` · `outro` |
| `tipoDocumento` | tipo declarado pelo DJEN — `DESPACHO / DECISÃO`, vistas, editais |
| `dispositivo_texto` | **trecho decisório que gerou o rótulo** — usar para auditoria |
| `dispositivo_multi` | todos os rótulos que casaram, antes da precedência |
| `n_dispositivos` | quantos casaram (>1 indica caso a revisar) |
| `fundamentos_mencionados` | fundamentos em qualquer ponto do texto — só para comparação |

Filtrar por `tipo_ato == "RE_admiss"` **e** `tipoDocumento == "DESPACHO / DECISÃO"`
reproduz `decisoes_admissibilidade.csv`.

---

## `data/raw/` — corpora brutos

| arquivo | conteúdo |
|---|---|
| `djen_comunicacoes.jsonl.gz` | 106.553 comunicações do DJEN, como vieram da API |
| `datajud_stj_re.jsonl.gz` | 32.513 processos do DataJud com movimento de admissibilidade |
| `atas_indice.jsonl.gz` | 11.981 referências processo→(órgão, relator) das Atas |
| `djen_dias_coletados.txt` · `atas_coletadas.txt` | checkpoints — apagar força recoleta |

---

## `resultados/` — tabelas do estudo

`01_dispositivo` · `02_assimetria_polo` · `03_serie_trimestral` · `04_por_assunto` ·
`05_por_turma` · `05b_procedencia_turma` · `06_temas_rg` — por `make analise`.

`07_defesa_natureza_da_falha` · `08_defesa_falhas_evitaveis` ·
`09_defesa_temas_que_barram` · `10_defesa_perfil_das_admissoes` ·
`11_defesa_por_representacao` · `12_agravo_interno_por_polo` — por `make defesa`
(ver `docs/07-recorte-defensivo.md`).

Nenhuma delas deve ser editada à mão.
