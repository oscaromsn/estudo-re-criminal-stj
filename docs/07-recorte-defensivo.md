# 07 — Recorte defensivo

Mesma base, outra pergunta: em vez de "como a Vice-Presidência decide", **"o que a
defesa pode fazer a respeito"**. Gerado por `analise/defesa.py`
(`make defesa`), tabelas 07 a 12 em `resultados/`.

Base: **12.760 decisões criminais com a defesa recorrente**, 38 admitidas (0,30%),
12.200 desfavoráveis, 129 que mantêm o recurso vivo.

## Onde falha

| natureza da falha | n | % |
|---|---:|---:|
| Estrutural — tese fechada no STF | 8.584 | 70,4% |
| **Evitável** — erro processual ou de redação | 1.385 | 11,4% |
| Enquadramento — pediu o que o RE não entrega | 973 | 8,0% |
| não classificado | 1.258 | 10,3% |

Critério da classificação e suas fronteiras discutíveis: ADR-011.

### A maior perda evitável

| causa | n | % das derrotas |
|---|---:|---:|
| **Não esgotou a instância** (cabia agravo interno antes) | 822 | 6,7% |
| Intempestivo | 215 | 1,8% |
| Falta de prequestionamento | 158 | 1,3% |
| Fundamentação deficiente (Súmula 284) | 107 | 0,9% |
| Sem preliminar formal de repercussão geral | 94 | 0,8% |

Os 822 da Súmula 281 são recursos interpostos contra decisão monocrática quando cabia
agravo interno ou regimental primeiro. É desperdício puro e a maior oportunidade
isolada de melhoria por parte do recorrente.

### O diagnóstico mais importante: Tema 181

**7.768 recursos morrem no Tema 181** — pressupostos de admissibilidade de recurso da
competência de outro tribunal são matéria infraconstitucional. Ele **só incide quando
o STJ não chegou ao mérito**.

Em quase dois terços das derrotas, portanto, o RE ataca uma decisão que barrou o
REsp/AREsp na porta. **A causa já estava perdida uma instância antes.** O ponto de
intervenção defensiva não é o RE — é a admissibilidade do especial.

Depois vêm o Tema 339 (motivação *per relationem*, 4.929) e o Tema 660 (ofensa a
contraditório e ampla defesa dependente de norma infraconstitucional, 518). Os três
dizem a mesma coisa: não é questão constitucional.

## Onde passa

Das 38 admissões:

- **32 (84%) citam o art. 1.030, V, alínea "a"** — questão constitucional **ainda não
  submetida ao regime de repercussão geral**.
- **28 (74%) não citam tema de RG algum.**
- Classes: Recurso Especial 20, AREsp 9, RHC 3.

**A defesa vence exatamente onde ainda não existe tema.** Uma vez criado, a porta
fecha — e os temas existentes são justamente os que negam natureza constitucional às
alegações típicas da defesa. A variável decisiva não é a força do argumento, é o
**estado do catálogo de repercussão geral naquele momento**.

## Vitórias que a taxa de 0,30% esconde

**Retratação (art. 1.030, II): 37. Sobrestamento (III): 92.** São 129 recursos que
seguem vivos. Para a defesa, sobrestar pode valer mais que ser admitido — mantém o
processo aberto aguardando o STF.

## Representação

| | n | admitidos | taxa | falha evitável |
|---|---:|---:|---:|---:|
| Defensoria Pública | 336 | 4 | **1,2%** | 11,9% |
| Advocacia privada | 12.424 | 34 | **0,3%** | 11,0% |

A Defensoria admite 4,4× mais, com taxa de erro evitável praticamente igual. **n=336 e
4 admissões — frágil**, e confundido por matéria: a composição de crimes atendidos pela
Defensoria difere da atendida pela advocacia privada.

## Depois da derrota: o agravo interno

Um número que **não pode ser reportado agregado**. A taxa geral de reconsideração no
agravo do art. 1.030, § 2º é ~13%, o que parece uma porta aberta. Desagregada:

| polo | n | reconsiderados | taxa |
|---|---:|---:|---:|
| Ministério Público | 37 | 14 | **37,8%** |
| Defesa | 144 | 2 | **1,4%** |

A assimetria **se reproduz na revisão interna** (27×, contra 96× na via direta). Ainda
assim, 1,4% é cerca de 5× a via direta — o agravo interno vale a pena, mas não é o
atalho que o número agregado sugeria.

## O que falta para fechar este recorte

1. **Ligação com o STF.** Admissão não é vitória. Das 38 admitidas e dos 2.007 AREs
   remetidos, quantas viraram provimento? Sem isso, "sucesso" está definido pelo portão.
2. **A janela antes do tema.** Para questões que viraram tema de RG durante o biênio, a
   taxa de admissão da defesa era maior **antes** da afetação? Transformaria "existe
   tema?" em variável de *timing* recursal.
3. **Caso-controle sobre as 38.** Parear cada admissão com derrotas de mesma classe,
   assunto, turma e período, e ler os pares. Com N=38 é leitura integral viável.
4. **Minerar os 1.258 sem fundamento classificado** (10,3% das derrotas). Fundamentos
   raros são onde moram as brechas.
5. **Separar as duas defesas.** "Defesa" agrega réu preso em tráfico e executivo em
   crime tributário. Cruzar com assunto e número de advogados testa se é uma história
   ou duas.
6. **A qualidade da petição** — hipótese concorrente não testada. Exige o texto do
   recurso, não o da decisão. É a fronteira do que esta fonte alcança.
