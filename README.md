# Admissibilidade de recursos extraordinários criminais no STJ

Estudo jurimétrico sobre **como a Vice-Presidência do Superior Tribunal de Justiça
decidiu os recursos extraordinários interpostos contra decisões criminais da própria
Corte** (Quinta Turma, Sexta Turma e Terceira Seção) durante o biênio de
**Luis Felipe Salomão** como Vice-Presidente — **22/08/2024 a 19/08/2026**.

A pergunta central é sobre **fundamentos**: quais razões sustentam a não admissão,
quais sustentam a admissão, e o que ocorre nas decisões intermediárias
(sobrestamento, juízo de retratação, seleção como representativo da controvérsia).

## Enquadramento

A decisão estudada é **filtragem recursal**, não julgamento de matéria penal. O
art. 1.030 do CPC dá à Vice-Presidência cinco saídas distintas, com recorribilidades
diferentes: a inadmissão pelo inciso V desafia agravo do art. 1.042; a negativa de
seguimento pelo inciso I desafia agravo interno (art. 1.030, § 2º). Tratá-las como
uma categoria única mede coisa nenhuma — a separação é o primeiro compromisso
metodológico do projeto.

Segundo enquadramento, igualmente deliberado: o objeto é o **comportamento
institucional da Vice-Presidência**, com o ministro como marcador de período. Há
uma assessoria dedicada à admissibilidade (a ARP, órgão 718 no Diário do STJ) e o
volume — mais de 28 mil decisões no biênio — implica produção padronizada. Ler o
agregado como disposição pessoal de um julgador seria erro de categoria.

## Principais resultados

Sobre **28.423 decisões de admissibilidade de RE** no biênio, das quais **14.897
criminais**:

| Dispositivo (art. 1.030 CPC) | % |
|---|---:|
| Nega seguimento (inciso I) | 78,4% |
| Inadmite (inciso V) | 11,4% |
| Admite | 2,6% |
| Sobresta (inciso III) | 2,3% |
| Juízo de retratação (inciso II) | 1,6% |

**Assimetria acusação × defesa (criminais):** Ministério Público 611/2.120 = **28,8%**
de admissão; defesa 38/12.760 = **0,30%**. Razão **96,8×**, presente nos oito
trimestres do biênio (mínimo 13×, máximo 530×).

**O mecanismo não é preferência do julgador — é o catálogo de repercussão geral do
STF.** As negativas à defesa concentram-se nos Temas 181 (8.492 ocorrências), 339
(5.650) e 660 (958), todos afirmando que a matéria não é constitucional. As admissões
do MP concentram-se no Tema 280 (478 de 611, ou 78%) — entrada forçada em domicílio,
RE 603.616 —, tese vinculante substantiva. Por assunto, o efeito aparece exatamente
onde busca domiciliar acontece: tráfico de drogas admite 19,4% e crimes do Sistema
Nacional de Armas 15,2%, contra 0,8% em roubo majorado e 0,0% em crimes contra a
ordem tributária.

**Por turma de origem** (4.950 casos com turma observada nas Atas): decisões da Sexta
Turma são admitidas **9,5%** das vezes contra **4,7%** da Quinta; a Terceira Seção
registra 0,9% em 218 casos.

Detalhamento e ressalvas em [`docs/04-limitacoes-e-vieses.md`](docs/04-limitacoes-e-vieses.md).
Nenhum número deste projeto deve ser citado sem ler esse documento.

## Estrutura

```
docs/
  01-viabilidade.md            fontes testadas e descartadas, com a evidência
  02-fontes-e-contratos.md     contratos das APIs e armadilhas verificadas
  03-decisoes-metodologicas.md ADRs — o racional de cada escolha
  04-limitacoes-e-vieses.md    LEIA ANTES DE CITAR QUALQUER NÚMERO
  05-trabalhos-futuros.md      o que fechar e o que abrir
  06-dicionario-de-dados.md    colunas, tipos e valores possíveis
  07-recorte-defensivo.md      onde o RE da defesa falha e onde passa
src/estudo_re/
  coleta/       djen.py · datajud.py · atas.py
  processamento/ partes.py · taxonomia.py · cruzamento.py
  analise/      resultados.py
data/
  raw/          corpora brutos, como vieram das APIs (comprimidos)
  interim/      classificação completa, todos os tipos de ato
  processed/    tabelas analíticas prontas
resultados/     tabelas do estudo, geradas por analise/resultados.py
```

## Reprodução

Requer apenas Python 3.10+ e biblioteca padrão — sem dependências externas, por
decisão (ver [ADR-007](docs/03-decisoes-metodologicas.md)).

```bash
make analise      # regera as tabelas a partir de data/processed  (segundos)
make defesa       # recorte defensivo                               (segundos)
make cruzamento   # refaz o cruzamento das três fontes            (~1 min)
make taxonomia    # reclassifica o corpus inteiro                 (~8 min)
make coleta       # rebaixa tudo das APIs                         (~3 h)
```

`make coleta` é retomável: os coletores mantêm arquivo de checkpoint e pulam o que já foi
feito.

**O corpus não acompanha o repositório.** Ele contém nome civil de acusados em processos
criminais e advogados com OAB — dados públicos, vindos do Diário de Justiça Eletrônico
Nacional, mas republicá-los em massa, estruturados e indexáveis, seria passo diferente de
estarem dispersos no diário. Versionamos código, documentação e as tabelas agregadas de
`resultados/`; quem quiser reproduzir roda `make coleta` e obtém o mesmo corpus direto da
fonte oficial, sem autenticação.

Para regerar tudo do zero:

```bash
make coleta && make atas && make taxonomia && make cruzamento && make analise && make defesa
```

## Fontes

| fonte | o que entrega | autenticação |
|---|---|---|
| **DJEN** (`comunicaapi.pje.jus.br`) | texto integral das decisões, partes, advogados | nenhuma |
| **DataJud** (`api-publica.datajud.cnj.jus.br`) | classe, assuntos TPU, movimentos datados | chave pública do CNJ |
| **Atas de Distribuição** (CKAN do STJ) | turma de origem e relator do acórdão recorrido | nenhuma |

O caminho até essas três — e por que as alternativas óbvias não serviram — está em
[`docs/01-viabilidade.md`](docs/01-viabilidade.md).

## Licença

[MIT](LICENSE).

Cobre o código, a documentação e as tabelas agregadas deste repositório. **Não se
estende aos dados de origem**: as decisões vêm do Diário de Justiça Eletrônico Nacional
e as tabelas de referência do CNJ, cada um sob seus próprios termos. Quem regenerar o
corpus com `make coleta` está obtendo dados públicos direto da fonte oficial e responde
pelo uso que fizer deles — inclusive quanto à LGPD, já que o corpus contém nome civil de
acusados em processos criminais.
