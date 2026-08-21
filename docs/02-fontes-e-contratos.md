# 02 — Fontes e contratos das APIs

Comportamento **verificado empiricamente** em 20–21/08/2026. Onde a documentação
oficial ou de terceiros diverge do observado, o observado prevalece e a divergência
está anotada. Todas as armadilhas abaixo custaram tempo ou produziram resultado
errado antes de serem descobertas.

---

## DJEN — Diário de Justiça Eletrônico Nacional

```
GET https://comunicaapi.pje.jus.br/api/v1/comunicacao
Origin:  https://comunica.pje.jus.br
Referer: https://comunica.pje.jus.br/
```

Sem autenticação. Implementado em `src/estudo_re/coleta/djen.py`.

**Parâmetros usados:** `siglaTribunal`, `orgaoId`, `dataDisponibilizacaoInicio`,
`dataDisponibilizacaoFim`, `pagina`, `itensPorPagina`, `numeroProcesso` (com máscara).

**Órgão-alvo:** `orgaoId=59696` — *SPF Coordenadoria de Processamento de Decisões
Estrangeiras e Recursos para o STF*. Outros órgãos do STJ no DJEN: 106757
(Classificação e Distribuição), 59758 (Direito Privado), 59761 (Execução Judicial),
59760 (Direito Público), 59632 (Direito Penal), 59759 (Julgamento Colegiado da 3ª
Turma), 59841 (Corte Especial).

### Armadilhas

**Parâmetro desconhecido é ignorado em silêncio.** `idOrgao` e `nomeOrgao` **não
existem**; o correto é `orgaoId`. Passar o nome errado não gera erro — a consulta
devolve o diário nacional inteiro (`count=10000`) com aparência de resultado legítimo.
Confirmado lado a lado: com `orgaoId`, 100% dos itens vêm do órgão pedido; com
`idOrgao`, vinham varas do trabalho e centrais de perícia.

**`count` satura em 10000.** É teto, não total. Qualquer contagem sobre janela ampla
está truncada — daí o recorte por dia no coletor.

**Regra 422.** Com `itensPorPagina > 5` é obrigatório enviar ao menos um de
`siglaTribunal`, `texto`, `nomeParte`, `nomeAdvogado`, `numeroOab` ou `numeroProcesso`.
`orgaoId` sozinho devolve 422. O coletor manda `siglaTribunal=STJ` sempre.

**Paginação existe** — `pagina` (base 1) e `itensPorPagina` (200 testado). Uma
referência de terceiros consultada durante o projeto afirma que não há paginação e que
o envelope é `{dadosResposta:{count, items}}`; ambas as afirmações estão
desatualizadas. O envelope real é `{status, message, count, items}`.

**Rate limiting.** Rajadas devolvem `500 {"message":"O sistema está muito ocupado"}`.
O coletor usa pausa de 4 s e backoff exponencial até 180 s; na coleta completa do
biênio foram 23 retries em 459 dias.

### Estrutura do item

`texto` (HTML), `tipoDocumento`, `nomeClasse`/`codigoClasse`, `nomeOrgao`/`idOrgao`,
`numeroprocessocommascara`, `data_disponibilizacao`, `destinatarios[{nome, polo}]`,
`destinatarioadvogados`, `link`, `hash`, `id`.

O `texto` é uma tabela HTML de três colunas — `[papel] [:] [valor]` — seguida do corpo
da decisão. **Célula de papel vazia significa continuação** do papel anterior (vários
advogados, vários recorrentes). Parsear a tabela é obrigatório; regex sobre o texto
achatado perde as continuações (ver ADR-004).

`tipoDocumento` separa os atos: `DESPACHO / DECISÃO` são as decisões;
`VISTA à(s) parte(s) recorrida(s) para contrarrazões de Recurso Extraordinário (RE)`
marca a **interposição** e fornece o denominador.

### Cobertura

**O STJ entra no DJEN em fins de novembro de 2024.** Agosto, setembro e outubro de
2024 devolvem `count=0`; novembro já traz 1.241 comunicações. Coletamos de 01/11/2024
a 19/08/2026: 459 dias úteis, **106.553 comunicações**.

---

## DataJud — API Pública do CNJ

```
POST https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search
Authorization: APIKey <chave pública do CNJ>
```

A chave é publicada pelo próprio CNJ e é idêntica para todos os consumidores — não é
credencial de ninguém. Implementado em `src/estudo_re/coleta/datajud.py`.

### Armadilhas

**`movimentos` não é `nested`.** Combinar `movimentos.codigo` com um `range` em
`movimentos.dataHora` na mesma cláusula casa campos de **movimentos diferentes** —
falso positivo silencioso. Toda filtragem por data é feita no cliente.

**Ordenação.** `sort` por `_id` é recusado (fielddata desabilitado). Use
`id.keyword`: o campo `id` é `TRIBUNAL_CLASSE_GRAU_ORGAO_NUMERO`, único e estável,
o que torna o cursor `search_after` confiável.

**Agregações funcionam** — não documentado em nenhum código do workspace. Permite
exploração barata antes de baixar qualquer coisa.

**Mojibake.** O índice tem UTF-8 duplamente codificado: `VICE-PRESIDÃNCIA`,
`SEÃÃO`. Recuperável com `s.encode("latin-1").decode("utf-8")` — o byte de controle
é preservado.

**Sigilo.** O índice inteiro é `nivelSigilo = 0` (3.603.220 de 3.603.220). Processos
em segredo de justiça são excluídos por atacado, não redigidos.

### Descontinuidade de codificação — importante

O código TPU **15621** ("negado seguimento ao RE, tema RG") **só aparece a partir de
outubro de 2025**. Os códigos 429, 432 e 265 cobrem 2014–2026 continuamente. Antes de
out/2025 essa saída estava agregada em outro código.

**Consequência:** qualquer série temporal que misture 429/432/15621 ao longo do biênio
compara categorias diferentes. Para comparação temporal dentro do DataJud, a base
comparável é apenas 429+432.

### Códigos TPU relevantes

| código | movimento | presidenteVice |
|---:|---|:-:|
| 429 | RE admitido | S |
| 432 | RE não admitido | S |
| 15621 | Negado seguimento ao RE (tema RG) | S |
| 265 | Suspenso por RE com repercussão geral | S |
| 26 | Distribuição | — |

Fonte: `_CNJ - OpenAPI specs and payloads/2 - sample payloads/tpu-movimentos.json`.

---

## Atas de Distribuição — CKAN do STJ

```
GET https://dadosabertos.web.stj.jus.br/api/3/action/package_show?id=atas-de-distribuicao
```

Um arquivo JSON por dia útil desde 30/06/2023, 5–9 MB cada. Sem autenticação.
Implementado em `src/estudo_re/coleta/atas.py`, que baixa apenas as atas que cobrem
os processos-alvo e guarda somente quatro campos.

**Campos usados:** `numeroUnico`, `codigoOrgaoJulgador` (T1–T6, S1–S3, CE),
`nomeMinistroRelator`, `descFormaDistribuicao`. O conjunto também traz `partes` com
`descTipoParte` e `advogados` com `codigoOAB` — uma segunda fonte independente para
o eixo MP × defesa, ainda não explorada (ver `05-trabalhos-futuros.md`).

### Armadilha central

**A última distribuição de um processo com RE é o "Registro" à Vice-Presidência, e a
ata a grava com `codigoOrgaoJulgador` NULO.** Numa amostra de 103 processos, 89% dos
registros casados vinham nulos por essa razão. A turma de origem está nas
**distribuições anteriores** — é preciso varrer todas as datas de distribuição do
processo, não apenas a última.

O campo `nomeMinistroRelator` grava `PRESIDENTE DO STJ` e `VICE-PRESIDENTE DO STJ`
como rótulos institucionais, não nomes — coerente com o enquadramento do estudo.

---

## Uma armadilha de parsing que corrompeu números

O STJ escreve temas de repercussão geral com separador de milhar: **"Tema n. 1.392"**.
Uma regex ingênua (`Tema\s*n?\.?\s*(\d{1,4})`) captura só o `1` — e "Tema 1" aparecia
como um dos mais citados do corpus, quando era a soma de dezenas de temas 1.xxx
distintos. O padrão correto está em `taxonomia.py`: `(\d{1,2}\.\d{3}|\d{1,4})`, com
remoção do ponto depois.

## Normalização entre fontes

A chave de junção é o número CNJ **somente dígitos**. O DJEN publica com máscara
(`0000000-00.0000.0.00.0000`), o DataJud sem. Nomes de ministros divergem entre
fontes: o DataJud trunca (`ROGERIO SCHIETTI` contra `ROGERIO SCHIETTI CRUZ` nas Atas)
e alterna `MARLUCE CALDAS` / `MARIA MARLUCE CALDAS`. Casar por igualdade perde
registros; use subconjunto de tokens.
