#!/usr/bin/env python3
"""Rastreia o que a turma decidiu DEPOIS do juízo de retratação (art. 1.030, II).

O corpus principal mede o que a Vice-Presidência faz. Este módulo responde a
pergunta seguinte: quando ela devolve o processo à turma para retratação, a
turma efetivamente se retrata?

    python3 -m estudo_re.analise.retratacao [--polo defesa/particular]

Para cada caso, consulta o DJEN por número de processo (sem filtro de órgão,
porque a decisão da turma sai por coordenadoria diferente da que processa
recursos para o STF) e procura, depois da data da retratação:

  * `EMENTA / ACORDÃO`     -> a turma julgou
  * `DESPACHO / DECISÃO`   -> novo ato da Vice-Presidência

Classificação do acórdão pelo texto, com as mesmas cautelas do resto do
projeto: o rótulo vem do dispositivo, e o trecho que o gerou fica gravado
para auditoria.

CENSURA À DIREITA: casos decididos perto do fim da janela não tiveram tempo de
voltar da turma. São contados como `sem_tempo`, nunca como `manteve` — tratá-los
como derrota subestimaria a taxa de retratação.

RESULTADO DA PRIMEIRA EXECUÇÃO (2026-08-21): a pergunta NÃO pôde ser respondida.
Três obstáculos, todos documentados em docs/rastreamento-retratacao.md:

  1. O universo é minúsculo. Com assunto criminal confirmado pelo TPU, há
     **2 retratações em 5.025** decisões da defesa (0,04%).
  2. A latência mediana entre a retratação e o acórdão da turma é de ~240 dias,
     maior que a folga que a janela de observação deixa para a maioria dos casos.
  3. O DJEN indexa pelo número CNJ de ORIGEM, e vários recursos distintos do STJ
     compartilham o mesmo número de origem. Consultar por ele devolve acórdãos de
     processos alheios — foi assim que apareceram Itaú Unibanco e municípios
     catarinenses num rastreamento de casos criminais.

O módulo fica como infraestrutura: quando houver janela maior, ele responde.
Por ora, a resposta honesta é "não sei".
"""
import argparse, csv, html, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import date

BASE = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
HDRS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0",
        "Origin": "https://comunica.pje.jus.br", "Referer": "https://comunica.pje.jus.br/"}
FIM_JANELA = "2026-08-19"
DIAS_MINIMOS = 120   # mediana observada entre retratação e acórdão fica abaixo disso

# Desfechos possíveis do acórdão de retratação, na ordem de precedência.
RETRATOU = [
    ("retratou_provendo",   r"(?:dou|dá-se|deu-se|dar)\s+provimento|provejo|reconsider|em\s+retrata[çc][ãa]o"),
    ("retratou_anulando",   r"anul[oa]|declaro\s+a\s+nulidade|torn[oa]\w*\s+sem\s+efeito"),
    ("manteve",             r"mantenho|mantid[oa]|n[ãa]o\s+h[áa]\s+(?:o\s+que\s+)?retratar|inexist\w+\s+motivo\s+para\s+retrata|nego\s+provimento"),
]


def limpo(h):
    t = re.sub(r"<[^>]+>", " ", h or "")
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def consultar(numero, pausa, tentativas=5):
    u = BASE + "?" + urllib.parse.urlencode({"numeroProcesso": numero, "itensPorPagina": 200})
    espera = pausa
    for t in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=HDRS), timeout=180) as r:
                d = json.loads(r.read())
            time.sleep(pausa)
            return d.get("items") or []
        except Exception:
            espera = min(espera * 2, 120)
            sys.stderr.write(f"    retry {t+1} em {espera}s\n"); sys.stderr.flush()
            time.sleep(espera)
    return None


def classificar_acordao(texto):
    t = limpo(texto)
    m = re.search(r"(Ante o exposto|Diante do exposto|ACORDAM|Vistos)", t)
    seg = t[m.start():m.start() + 900] if m else t[-900:]
    for nome, rx in RETRATOU:
        if re.search(rx, seg, re.I):
            return nome, seg[:200]
    return "indefinido", seg[:200]


def dias(a, b):
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def main():
    ap = argparse.ArgumentParser()
    # Default no arquivo com assunto TPU confirmado: o flag `criminal` derivado
    # das partes tem precisão de 94,9% (ver ADR-005), e os 5,1% de falsos
    # positivos se concentram justamente nos desfechos raros como este.
    ap.add_argument("--decisoes", default="data/processed/criminais_3fontes.csv")
    ap.add_argument("--polo", default="defesa/particular")
    ap.add_argument("--pausa", type=float, default=4.0)
    ap.add_argument("--saida", default="resultados/13_retratacao_rastreamento.csv")
    a = ap.parse_args()

    casos = [r for r in csv.DictReader(open(a.decisoes, encoding="utf-8"))
             if r.get("criminal", "True") == "True" and r["polo_recorrente"] == a.polo
             and r["dispositivo"] == "retratacao_1030_II"]
    print(f"casos de retratação a rastrear: {len(casos)}\n", flush=True)

    linhas = []
    for i, c in enumerate(casos, 1):
        itens = consultar(c["processo"], a.pausa)
        if itens is None:
            print(f"[{i}/{len(casos)}] {c['processo']}: FALHA na consulta", flush=True)
            continue
        depois = sorted([x for x in itens
                         if (x.get("data_disponibilizacao") or "") > c["data"]
                         and x.get("siglaTribunal") == "STJ"],
                        key=lambda z: z["data_disponibilizacao"])
        acordaos = [x for x in depois if (x.get("tipoDocumento") or "").startswith("EMENTA")]
        despachos = [x for x in depois if (x.get("tipoDocumento") or "") == "DESPACHO / DECISÃO"]

        if acordaos:
            desfecho, trecho = classificar_acordao(acordaos[0].get("texto"))
            data_ac = acordaos[0]["data_disponibilizacao"]
            latencia = dias(c["data"], data_ac)
        elif dias(c["data"], FIM_JANELA) < DIAS_MINIMOS:
            desfecho, trecho, data_ac, latencia = "sem_tempo", "", "", ""
        else:
            desfecho, trecho, data_ac, latencia = "sem_acordao_localizado", "", "", ""

        linhas.append({
            "processo": c["processo"], "classe": c["classe"], "data_retratacao": c["data"],
            "temas_rg": c["temas_rg"], "data_acordao": data_ac, "dias_ate_acordao": latencia,
            "desfecho_turma": desfecho, "n_comunicacoes_depois": len(depois),
            "n_despachos_depois": len(despachos), "trecho": trecho,
        })
        print(f"[{i}/{len(casos)}] {c['processo']} ({c['data']}) -> {desfecho}"
              f"{f' em {latencia}d' if latencia != '' else ''}", flush=True)

    os.makedirs(os.path.dirname(a.saida), exist_ok=True)
    with open(a.saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys())); w.writeheader(); w.writerows(linhas)

    import collections
    c = collections.Counter(r["desfecho_turma"] for r in linhas)
    print(f"\n=== DESFECHO NA TURMA (n={len(linhas)}) ===")
    for k, v in c.most_common():
        print(f"   {v:>4}  {100*v/len(linhas):5.1f}%  {k}")
    julgados = [r for r in linhas if r["desfecho_turma"].startswith(("retratou", "manteve"))]
    ret = sum(1 for r in julgados if r["desfecho_turma"].startswith("retratou"))
    if julgados:
        print(f"\n   entre os efetivamente julgados ({len(julgados)}): "
              f"retratou {ret} = {100*ret/len(julgados):.1f}%")
    lat = [int(r["dias_ate_acordao"]) for r in linhas if r["dias_ate_acordao"] != ""]
    if lat:
        lat.sort()
        print(f"   latência até o acórdão: mediana {lat[len(lat)//2]} dias "
              f"(min {lat[0]}, max {lat[-1]})")
    print(f"\nescrito: {a.saida}")


if __name__ == "__main__":
    main()
