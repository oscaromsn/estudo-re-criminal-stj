# Rastreamento do juízo de retratação — e por que a pergunta ficou sem resposta

**Pergunta:** quando a Vice-Presidência devolve o processo à turma para juízo de retratação (art. 1.030, II), a turma efetivamente se retrata?

**Resposta:** não sei, e este documento explica por quê. O módulo `analise/retratacao.py` (`make retratacao`) fica como infraestrutura para quando houver janela maior.

O caminho até o "não sei" produziu três achados que valem mais que a resposta pretendida — inclusive uma **correção a uma validação anterior deste estudo**.

---

## Achado 1 — o flag `criminal` tem 94,9% de precisão, não 99,5%

O ADR-005 registrava concordância de **99,5%** entre o flag `criminal` derivado das partes e a classificação por assunto TPU do DataJud. **Essa medida era unilateral** e, portanto, enganosa: comparava apenas os casos em que o TPU dizia "criminal", medindo revocação, não precisão. Nunca perguntei quantos dos marcados como criminais eram, na verdade, cíveis.

Validação bilateral, sobre as 15.912 decisões que casam com o DataJud:

| | TPU: criminal | TPU: cível |
|---|---:|---:|
| **flag: criminal** | 6.766 | **361** |
| **flag: cível** | 53 | 8.732 |

- **Precisão: 94,9%** — dos marcados criminais, 5,1% são cíveis
- **Revocação: 99,2%** — dos criminais reais, 99,2% são capturados

A causa do falso positivo: **o Ministério Público é parte em ação civil**. Improbidade administrativa, ação civil pública, saúde, meio ambiente, consumidor. O flag dispara pela presença do MP e não distingue.

Acrescentei ao `partes.py` uma exclusão para improbidade — o caso mais frequente e identificável (`improbidade`, `Lei 8.429`, `ato ímprobo`) —, preservando a prevalência de papel criminal explícito, porque um crime pode ser discutido em ação conexa. Isso não elimina os falsos positivos restantes; apenas o subconjunto mais volumoso.

### Efeito nos números publicados

| | antes | depois |
|---|---:|---:|
| Decisões criminais da defesa | 12.760 | 12.419 |
| Admitidas | 38 (0,30%) | **32 (0,26%)** |
| **Razão MP / defesa** | 96,8× | **111,4×** |
| Retratações | 37 | **14** |
| Sobrestamentos | 92 | 87 |

Os números principais mal se movem — a assimetria, aliás, **aumenta**, porque a improbidade contribuía com 6 das admissões da defesa. Mas os **desfechos raros mudam de patamar**: a retratação cai de 37 para 14. Era ali que a contaminação estava concentrada — 23 dos 37 casos citavam o **Tema 1199**, que é retroatividade da Lei 14.230/2021 em improbidade, não matéria criminal.

**Lição metodológica:** validação unilateral cria falsa confiança, e o erro se manifesta primeiro nos eventos raros. Uma taxa agregada robusta pode conviver com um bucket pequeno inteiramente contaminado.

---

## Achado 2 — o DJEN indexa pelo número de ORIGEM

Ao consultar o DJEN por `numeroProcesso` para rastrear o que veio depois da retratação, apareceram acórdãos de **processos alheios**: Itaú Unibanco contra o MPF, Estado do Rio de Janeiro, municípios catarinenses em causa ambiental — num rastreamento de casos criminais.

A razão é estrutural: **o `numeroProcesso` do DJEN é o CNJ de origem**, e vários recursos distintos do STJ compartilham o mesmo número de origem. Consultar por ele devolve a linha do tempo do *processo de origem*, não a do recurso específico.

Consequência prática para quem for construir rastreamento processual sobre o DJEN: a chave de junção é o **número de registro no STJ** (formato `2023/0377726-0`), não o CNJ de origem. Ele não é campo estruturado da API — está dentro do texto, no cabeçalho, e precisa ser extraído.

---

## Achado 3 — a latência supera a janela

Entre a retratação e o acórdão da turma, a mediana observada é de **~240 dias**, com casos chegando a 297. A janela do estudo termina em 19/08/2026, e as retratações se concentram no último ano.

Resultado: para a maioria dos casos, o desfecho na turma simplesmente **ainda não aconteceu** quando o corpus foi coletado. É censura à direita clássica, e o módulo a marca como `sem_tempo` em vez de contá-la como manutenção — tratá-la como derrota subestimaria a taxa de retratação.

---

## O universo real

Restringindo aos casos com **assunto criminal confirmado pelo TPU** — o recorte defensável, dado o achado 1:

**2 retratações em 5.025 decisões criminais da defesa. 0,04%.**

| processo | data | classe | assunto | tema |
|---|---|---|---|---|
| 0024875-24.2014.4.03.0000 | 28/10/2025 | AREsp | Crimes da Lei de licitações | 339 |
| 5000224-43.2021.8.24.0139 | 22/04/2026 | AREsp | Tráfico de drogas | 660, 712 |

Com n=2, e ambos sem acórdão de retratação localizável, **não há taxa a reportar**. Qualquer número que eu produzisse aqui seria ruído com aparência de medida.

O intervalo honesto para o universo do biênio é **entre 2 e 14** casos — 2 confirmados pelo TPU, 14 pelo flag após a exclusão de improbidade —, e a diferença se deve aos 45% de decisões que não casam com o DataJud e cujo assunto, portanto, não é verificável.

---

## O que fica

O módulo funciona e é reutilizável: consulta o DJEN por processo, isola comunicações posteriores à retratação, localiza `EMENTA / ACORDÃO` e classifica o dispositivo, tratando censura à direita explicitamente.

Para responder à pergunta original seriam necessários:

1. **Janela maior** — estender a coleta para além de agosto de 2026, dando aos casos os ~8 meses de latência que a turma consome.
2. **Chave de junção correta** — extrair o número de registro do STJ do cabeçalho e usá-lo no lugar do CNJ de origem.
3. **População maior** — incluir as retratações do Ministério Público (195 no biênio, contra 14 da defesa). A pergunta "a turma se retrata?" não precisa ser restrita à defesa, e com n=195 seria respondível hoje.

O item 3 é o caminho mais curto, e inverte o desenho de forma útil: mede-se a eficácia do art. 1.030, II onde ele é efetivamente usado.

---

*Gerado por `make retratacao`. Tabela: `resultados/13_retratacao_rastreamento.csv`.*
