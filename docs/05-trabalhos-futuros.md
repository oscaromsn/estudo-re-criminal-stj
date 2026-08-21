# 05 — Trabalhos futuros

Ordenado por razão entre valor e esforço. Os quatro primeiros fecham limitações
conhecidas; os demais abrem linhas novas.

---

## Fechamento de limitações

### 1. Completar a cobertura das Atas — ~20 minutos

`python3 -m estudo_re.coleta.atas --max 500` indexa as 418 atas restantes e leva a
turma de origem de 58% para perto de 95%. **Pré-requisito para publicar qualquer
número por turma** (limitação 3).

### 2. Gold set anotado e medida de concordância — 2 a 3 dias

Amostrar 400 decisões estratificadas por dispositivo e por polo, anotar à mão o
dispositivo e o fundamento determinante, e reportar concordância (κ de Cohen) contra a
classificação automática. A coluna `dispositivo_texto` já guarda o trecho decisório, o
que torna a anotação rápida.

Sem isso não há medida de erro dentro do que foi classificado (limitação 6). É o item
que mais aumenta a defensabilidade do estudo por unidade de esforço.

### 3. Os três meses ausentes — 1 a 2 semanas

22/08 a ~25/11/2024 só existem no Diário do próprio STJ, que exige automação de
navegador. Os filtros já estão mapeados (`orgao=5`, `tipo_documento=6`). Fecha a
limitação 1 e permite afirmar o biênio completo.

### 4. Denominador real — 1 dia

Coletar `tipoDocumento = VISTA ... contrarrazões de Recurso Extraordinário (RE)` no
DJEN, que marca a **interposição**. Hoje as taxas são condicionais a ter havido
decisão. Com o denominador, é possível medir tempo entre interposição e decisão, e
estimar quanto do acervo ficou sem decisão no biênio.

---

## Extensões analíticas

### 5. Ligação com o STF — critério externo de acerto

Dos REs admitidos e dos agravos do art. 1.042, o que o STF decidiu. Os dados abertos
do STF registram o número de origem, que é a chave. É a única forma de obter um
**critério externo** para o filtro: taxa de provimento do agravo mede a taxa de erro da
inadmissão. Hoje o estudo descreve dispositivos; com isso, avalia acertos.

### 6. Agravo interno do art. 1.030, § 2º — reforma interna

O corpus já contém 362 decisões classificadas como `AgInt_1030_p2` — agravo interno
contra a própria decisão de admissibilidade. Permite medir com que frequência o
colegiado reforma o filtro, **sem sair do STJ**. Análise barata, dados já coletados.

### 7. Qualidade da petição como explicação concorrente

A limitação 7 aponta a hipótese não testada: as petições do MP podem ser tecnicamente
melhores. Testar exigiria codificar atributos da **petição** — prequestionamento
explícito, preliminar formal de repercussão geral, indicação de dispositivo
constitucional. Parte disso é inferível do texto da decisão, que costuma apontar o
defeito. Se a assimetria sobreviver ao controle por qualidade técnica, a tese
estrutural fica muito mais forte.

### 8. Desenho comparativo entre Vice-Presidências

Og Fernandes (2022–2024) → Salomão (2024–2026) → Mauro Campbell (2026–). O fluxo de
entrada é razoavelmente exógeno a quem ocupa o cargo, o que aproxima de um experimento
natural com descontinuidade em 22/08/2024.

Dois cuidados: a cobertura do DJEN só começa em nov/2024, o que impede olhar o mandato
anterior por esta fonte; e temas de repercussão geral julgados no intervalo mudam a
linha de base mecanicamente — o número do tema precisa entrar como controle, não como
descritivo.

### 9. Modelo com dependência tratada

Retomar ADR-010 com o desenho adequado: modelo hierárquico com efeito aleatório por
tema de repercussão geral e por relator de origem, tendo como desfecho a admissão. É o
caminho para intervalos honestos sobre a assimetria.

### 10. Segunda fonte para MP × defesa

As Atas de Distribuição trazem `partes` com `descTipoParte` e `advogados` com
`codigoOAB` — uma derivação do polo **independente** da que fizemos pelo cabeçalho do
DJEN. Cruzá-las mede o erro da extração de partes sem anotação manual.

### 11. Concentração de advocacia

`n_advogados`, `advogado_1` e o flag `defensoria` já estão na base e não foram
explorados. Perguntas ao alcance: a taxa de admissão da defesa varia entre Defensoria
Pública e advocacia privada? Há escritórios recorrentes? O número de advogados
constituídos correlaciona com desfecho?

### 12. Análise textual dos 8,7% sem fundamento ancorado

Podem ser fundamentos fora da taxonomia atual — ou decisões que simplesmente não
enunciam razão. A distinção importa: a segunda hipótese é achado sobre padronização,
não falha de extração.
