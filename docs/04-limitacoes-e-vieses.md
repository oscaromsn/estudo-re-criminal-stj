# 04 — Limitações e vieses

**Nenhum número deste projeto deve ser citado sem este documento.** As limitações
estão ordenadas por gravidade: as três primeiras podem alterar conclusões.

---

## 1. Cobertura temporal incompleta — faltam ~3 meses do biênio

O DJEN passa a cobrir o STJ em **fins de novembro de 2024**. O biênio começa em
**22/08/2024**. Agosto, setembro e outubro de 2024 estão **ausentes** — cerca de 14%
do período.

Não é ausência aleatória: é o **início do mandato**, quando o acervo herdado e a
formação da rotina de trabalho tornam o comportamento possivelmente atípico. Todas as
conclusões valem, com rigor, para **~21 dos 24 meses**.

*Como fechar:* o Diário do próprio STJ cobre o período, mas exige automação de
navegador (ver `01-viabilidade.md`).

---

## 2. Processos em segredo de justiça estão fora — e isso pesa no criminal

DJEN e DataJud excluem sigilosos por atacado, não redigem. O índice DataJud do STJ é
`nivelSigilo = 0` em 3.603.220 de 3.603.220 documentos.

Em matéria criminal isso não é detalhe: colaboração premiada, organização criminosa,
processos envolvendo menores e parte dos casos de crimes sexuais tramitam sob sigilo —
exatamente onde questões constitucionais de prova e devido processo são mais densas.
**A direção do viés é desconhecida.**

Um indício de que o buraco existe: 7,7% das decisões trazem partes anonimizadas por
iniciais, ou seja, com restrição parcial ainda assim publicadas. O que está sob sigilo
integral não aparece nem assim.

*Como dimensionar:* comparar a contagem de `tipo_documento=14` (vista para
contrarrazões de RE) no Diário do STJ com o número de decisões observadas. A diferença
é o limite superior do não observado.

---

## 3. Turma de origem: 72,6% por observação direta, e o resíduo não é aleatório

Das 6.819 decisões criminais cruzadas:

| procedência | n | % |
|---|---:|---:|
| observação direta nas Atas (evento de Distribuição com órgão) | 4.950 | 72,6% |
| inferida pelo mapa gabinete→turma | 371 | 5,4% |
| não resolvida | 1.498 | 22,0% |

**A cobertura das Atas foi esgotada** — todas as 641 atas relevantes estão indexadas.
O teto de 72,6% é **estrutural, não operacional**, e a razão é específica: 1.572 dos
não resolvidos aparecem nas Atas apenas com eventos `forma = "Registro"` (registro
regimental à Presidência/Vice-Presidência), **sem nunca terem tido um evento de
Distribuição a uma turma**. Não há turma a recuperar.

**O grupo inferido pelo mapa foi excluído da comparação entre turmas**, e por medida,
não por precaução: ele tem perfil estruturalmente distinto — **62% de inadmissão e 61%
de MP recorrente**, contra 15% e 18% no grupo observado diretamente. São processos de
natureza diferente (registrados, não distribuídos); misturá-los contaminaria a
comparação. Ficam na base com `turma_fonte = "mapa_relator"` para quem quiser usá-los
com essa consciência.

**O resíduo continua enviesado.** Os 1.498 não resolvidos têm 13,9% de admissão e
35,0% de MP recorrente, contra 4,7%/18,3% na Quinta e 9,5%/24,2% na Sexta. O que
ficou de fora é sistematicamente mais favorável ao recorrente e mais povoado pelo MP.

**Consequência prática:** os números por turma valem para os 72,6% em que a turma foi
*observada*, e essa subpopulação não representa o total. A comparação **entre** turmas
(Sexta 9,5% × Quinta 4,7%) é interna a essa base e provavelmente robusta — ambas
sofrem o mesmo recorte —, mas os **níveis** estão subestimados.

## 4. O DataJud subnotifica por fator próximo de 2

O DJEN registra **28.423** decisões de admissibilidade no biênio. O DataJud registrou
**10.573** desfechos terminais na Vice-Presidência no mesmo período.

O DataJud continua útil como esqueleto processual — é a única fonte de assunto TPU —
mas **não serve como frame populacional**. A junção DJEN × DataJud casa 55,3% dos
processos, e a análise por assunto criminal (6.819 casos) herda essa perda. Se a
subnotificação do DataJud não for aleatória entre assuntos, a tabela por assunto está
enviesada de forma não medida.

---

## 5. Dependência entre observações

Centenas de decisões compartilham o mesmo tema de repercussão geral e reproduzem texto
padronizado — só o Tema 181 aparece em 8.492 negativas. Elas **não são observações
independentes**. É a razão de ADR-010 (nenhum teste inferencial): qualquer intervalo de
confiança que ignore a dependência será falsamente estreito.

---

## 6. Classificação por regras, sem *gold set*

Dispositivo e fundamento saem de expressões regulares auditáveis, não de anotação
humana. As taxas de não classificação são baixas — 1,1% no dispositivo, 8,7% no
fundamento — mas **não há medida de concordância**: não sabemos a taxa de erro dentro
do que *foi* classificado.

A coluna `dispositivo_texto` guarda o trecho que gerou cada rótulo, o que torna a
auditoria barata. Falta fazê-la: ver `05-trabalhos-futuros.md`.

---

## 7. A assimetria é medida, a explicação é inferida

Que o MP tenha 96,8× mais admissões que a defesa é **observação direta**.

Que isso decorra do catálogo de repercussão geral do STF é **interpretação** — bem
sustentada, mas interpretação. O apoio: as negativas concentram-se em temas que negam
natureza constitucional à matéria (181, 339, 660); as admissões concentram-se num tema
substantivo (280, entrada forçada em domicílio); e o efeito aparece exatamente nos
crimes em que busca domiciliar ocorre (tráfico 19,4%, armas 15,2%) e some onde não
ocorre (ordem tributária 0,0%).

A explicação concorrente que **não foi testada**: as petições do MP podem ser
tecnicamente melhores — prequestionamento adequado, preliminar formal de repercussão
geral. Distinguir exigiria codificar a qualidade da petição, não da decisão.

---

## 8. Composição de temas varia no tempo

A taxa de admissão do MP oscila entre 15,4% e 47,7% por trimestre. A da defesa nunca
passa de 1,2%. A **razão** se mantém em todos os oito trimestres (13× a 530×), o que
sustenta o caráter estrutural. Mas o **nível** é episódico e acompanha quantos casos do
Tema 280 chegaram no período — 78% das admissões do MP são desse tema.

Séries de nível não devem ser lidas como mudança de postura sem controlar por tema.

---

## 9. Um viés que não se aplica

Vale registrar o que **não** é limitação aqui: a atribuição de quem decidiu. A
assinatura ao final de cada decisão é nominal, e separa perfeitamente os atos da
Vice-Presidência ("Vice-Presidente LUIS FELIPE SALOMÃO") dos da Presidência
("Presidente HERMAN BENJAMIN", competente nas decisões estrangeiras que tramitam pelo
mesmo órgão). Não há inferência envolvida.
