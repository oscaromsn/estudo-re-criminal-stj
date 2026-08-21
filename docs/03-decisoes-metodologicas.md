# 03 — Decisões metodológicas

Formato de registro de decisão (ADR): cada entrada traz o **contexto**, a **decisão**
e a **consequência**. Duas delas (ADR-002 e ADR-003) corrigem erros que já estavam
produzindo números publicáveis e errados — ficam registradas por isso.

---

## ADR-001 — Unidade de análise é a decisão, não o processo

**Contexto.** Um processo pode receber mais de um ato da Vice-Presidência: sobresta,
depois decide; ou nega seguimento a uma tese e inadmite outra. Contar movimentos
infla; contar processos apaga atos distintos.

**Decisão.** A unidade é a **decisão publicada** (uma comunicação do DJEN com
`tipoDocumento = DESPACHO / DECISÃO`). Para as análises do DataJud, onde só há
movimentos, a unidade é o processo e o desfecho é o **último movimento terminal na
janela**.

**Consequência.** As duas bases não são diretamente somáveis. Onde comparamos —
como na taxa de admissão — a comparação é declarada como convergência de estimativas
independentes, não como identidade.

---

## ADR-002 — O dispositivo é lido no parágrafo dispositivo, não no texto inteiro

**Contexto.** A primeira versão aplicava as expressões regulares ao texto inteiro.
Resultado: 51,8% de não classificados e rótulos somando mais de 100%, porque uma
decisão que **discute** o inciso I e **decide** pelo inciso V recebia os dois rótulos.

**Decisão.** Segmentar o texto no último marcador dispositivo — "Ante o exposto"
(46,5% dos casos), "Diante do exposto", "Isso posto", "Ex positis" e variantes — e
classificar **apenas** o trecho entre ele e o encerramento ("Publique-se"). Medição:
**99,4%** das decisões têm marcador forte, e o segmento tem mediana de **124
caracteres**.

**Consequência.** Multi-rótulo caiu de 21,8% para **0,2%**; não classificados, de
51,8% para **0,5%**. As 0,6% sem marcador são atos distintos (prejudicado por perda
de objeto, intimação de preparo, suspeição), que ganharam rótulos próprios.

O texto integral do segmento fica na coluna `dispositivo_texto` para auditoria — toda
classificação é conferível sem reprocessar.

---

## ADR-003 — O discriminante do dispositivo é o verbo, nunca o inciso

**Contexto.** A versão anterior tratava a citação do `art. 1.030, V` como inadmissão.
**Isso é juridicamente errado.** O inciso V é o juízo de admissibilidade em si, e pode
ser **positivo**: encontramos decisões dizendo "*reconsidero a decisão... nos termos do
art. 1.030, V, c, do CPC, **admito** o recurso extraordinário*".

Um segundo erro, mais banal e igualmente grave: `"não admito o recurso extraordinário"`
**contém** a subcadeia `"admito o recurso extraordinário"`. Sem *lookbehind* negativo,
99 inadmissões foram contadas como admissões.

**Decisão.** Classificar pelo **verbo do dispositivo** — `admito` (com lookbehind
negativo), `não admito`, `nego seguimento`, `sobresto`, `retratação`. O inciso citado
vira coluna analítica separada (`inciso_citado`), útil mas não decisória.

**Consequência.** Este é o erro mais perigoso encontrado no projeto: produzia números
plausíveis e invertidos. Qualquer reimplementação deve começar por aqui.

---

## ADR-004 — Partes vêm da tabela HTML, não do texto achatado

**Contexto.** A extração inicial usava regex sobre o texto corrido, perdendo as
continuações de papel (a segunda linha de "ADVOGADOS" não tem rótulo) e confundindo o
limite entre rótulo e valor. Resultado: 6,6% sem polo extraído.

**Decisão.** Parsear a tabela `<tr>`/`<td>` do cabeçalho, tratando célula de papel
vazia como continuação. Implementado em `processamento/partes.py`, que também
classifica o **tipo** da parte: MP, Defensoria, ente público, pessoa jurídica,
pessoa física e **anonimizado** (partes sob sigilo aparecem como iniciais — "P O P S").

**Consequência.** Não extraídos foram a **zero**.

---

## ADR-005 — "Sem MP no feito" não é falha de extração

**Contexto.** Um balde de 42% rotulado "outro/indefinido" parecia falha da extração.
Inspecionados, eram **feitos cíveis** — `DIRECIONAL ENGENHARIA S/A`, `BK
INFRAESTRUTURA LTDA`. O órgão 59696 processa todos os REs do STJ, não só criminais.

**Decisão.** Derivar um flag `criminal` explícito (papéis PACIENTE / RÉU / ACUSADO,
presença do MP em algum polo, ou classe habeas corpus) e aplicar o eixo MP × defesa
**somente** aos criminais.

**Consequência.** 52,4% das decisões de admissibilidade são criminais.
**Validação independente:** confrontado com a classificação por assunto TPU do
DataJud — construção inteiramente distinta —, o flag concorda em **99,5%** dos 6.819
casos cruzados.

---

## ADR-006 — Matéria criminal pela árvore TPU, não por palavra-chave

**Contexto.** A triagem exploratória usava palavras-chave nos nomes de assunto
("Tráfico", "Homicídio", "Pena"), o que erra nos dois sentidos.

**Decisão.** Expandir a árvore de assuntos do CNJ a partir das raízes 287 (Direito
Penal), 1209 (Direito Processual Penal), 11068 (Penal Militar) e 11049 (Processual
Penal Militar) — 1.077 códigos — e classificar por pertencimento.

**Consequência.** Classificação auditável e estável. O primeiro número exploratório
de assimetria (15,5% × 3,1%) foi produzido com palavra-chave e corpus parcial; não
deve ser citado.

---

## ADR-007 — Sem dependências externas

**Contexto.** O pipeline faz requisições HTTP, lê JSON e CSV e agrega contagens.
Nada disso exige pandas, requests ou similares.

**Decisão.** Biblioteca padrão do Python apenas.

**Consequência.** O projeto roda em qualquer Python 3.10+ sem ambiente virtual,
resolução de dependências ou risco de quebra por versão — o que importa mais que
conveniência num artefato que precisa ser reexecutável anos depois. O custo é código
um pouco mais verboso na agregação.

---

## ADR-008 — Turma de origem por junção direta, com mapeamento como reserva

**Contexto.** O DataJud não registra turma. Duas saídas: mapear gabinete→turma por
período, ou juntar diretamente com as Atas de Distribuição.

**Decisão.** Junção direta pelo número do processo. O mapeamento gabinete→turma foi
construído mesmo assim — derivado de 61 atas amostradas — e fica em
`data/processed/mapa_gabinete_turma.csv` como reserva para processos anteriores a
30/06/2023.

**Consequência.** A junção evita o problema de acertar datas de troca de composição.
O mapeamento tem limite conhecido: quatro ministros que entraram nas turmas criminais
em 2025–2026 (Marchionatti, Maria Marluce Caldas, Carlos Pires Brandão, Nilsoni de
Freitas) **não aparecem como órgão julgador em nenhum dos 32.513 processos do corpus
DataJud** — para eles, só a junção direta funciona.

**Adendo (após esgotar a coleta de atas).** A junção direta resolve 72,6% e o mapa de
reserva acrescentaria 5,4%. Mantivemos os dois na base, mas com uma coluna de
procedência (`turma_fonte`), e **a comparação entre turmas usa apenas a observação
direta**: o grupo inferido tem 62% de inadmissão e 61% de MP recorrente, contra 15% e
18% no grupo observado — são processos que só tiveram "Registro" à Vice-Presidência,
sem distribuição a turma, e portanto população distinta. Marcar a procedência permitiu
descobrir isso; um rótulo único de turma teria escondido.

Validação lateral agradável: a composição derivada mostra **Og Fernandes entrando na
Sexta Turma em setembro de 2024**, exatamente quando deixou a Vice-Presidência. O
método reproduz sozinho a fronteira do biênio, sem ter sido informado dela.

---

## ADR-009 — Fundamento reportado é o ancorado, não o mencionado

**Contexto.** Uma súmula pode aparecer no texto por três razões: ser a razão de
decidir, estar citada no acórdão recorrido, ou constar das razões da parte. Contar
menções mistura as três.

**Decisão.** Reportar o fundamento **ancorado** — presente no segmento dispositivo ou
nos 1.500 caracteres que o precedem. A contagem de menções em qualquer ponto fica na
coluna `fundamentos_mencionados`, só para comparação.

**Consequência.** A diferença é grande e justifica a decisão: a Súmula 286/Súmula 7 do
STJ aparece em 39,5% dos textos mas em 1,9% das razões de decidir. Sem a ancoragem, o
estudo reportaria como fundamento dominante algo que é, em regra, citação.

---

## ADR-010 — Descritivo, sem inferência

**Contexto.** A assimetria observada (96,8×) tenta o teste de hipótese.

**Decisão.** Nenhuma estatística inferencial nesta versão.

**Consequência.** As decisões não são independentes — centenas compartilham o mesmo
tema de repercussão geral e reproduzem texto padronizado. Um teste que ignore essa
dependência produz intervalos falsamente estreitos. O desenho inferencial adequado
está esboçado em `05-trabalhos-futuros.md`.

---

## ADR-011 — A classificação evitável / enquadramento / estrutural é normativa

**Contexto.** O recorte defensivo (`analise/defesa.py`) agrupa os fundamentos de
derrota em três naturezas. Diferente das demais classificações do projeto — que só
leem o que o texto diz —, esta **atribui um juízo**: se a derrota era corrigível pelo
advogado.

**Decisão.** Manter a classificação, com os três grupos declarados explicitamente no
topo do módulo, e marcá-la como contestável aqui.

- **Evitável** — Súmula 281 (não esgotamento), Súmulas 282/356 (prequestionamento),
  Súmula 284 (deficiência), ausência de preliminar formal de RG, intempestividade,
  deserção. São defeitos da peça ou do momento processual.
- **Enquadramento** — Súmula 279 (reexame de prova), ofensa reflexa, Súmula 7/STJ,
  Súmula 280, Súmula 283. A peça pode estar impecável; o pedido é que não cabe no RE.
- **Estrutural** — conformidade com tema de repercussão geral. Nenhuma redação
  resolveria: a tese está fechada.

**Consequência e contestação.** As fronteiras são discutíveis, e duas em particular:

1. A **Súmula 279** está em "enquadramento", mas há leitura de que seja evitável — um
   recurso bem redigido pode converter matéria fática em tese jurídica. Quem discordar
   move a linha e 600 casos (4,9%) mudam de grupo.
2. O **Tema 181** está em "estrutural", e é o maior grupo isolado (7.768). Mas ele só
   incide quando o STJ não apreciou o mérito — o que significa que a causa foi perdida
   na fase anterior. É *estrutural para o RE* e possivelmente *evitável no REsp*. A
   classificação é correta no recorte deste estudo e enganosa se lida como "não havia
   nada a fazer".

Por isso o módulo grava as tabelas com os fundamentos originais ao lado da natureza
atribuída: quem quiser reclassificar não precisa reprocessar nada.
