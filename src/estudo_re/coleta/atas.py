#!/usr/bin/env python3
"""Indexa Atas de Distribuicao do STJ para recuperar a TURMA DE ORIGEM.

As Atas (dados abertos do STJ, CKAN) trazem, por processo distribuido,
`codigoOrgaoJulgador` (T5/T6/S3/...) e `nomeMinistroRelator`. E a unica fonte que
resolve a turma de origem sem inferencia — o DataJud registra orgao por gabinete
de ministro, nunca por turma.

    python3 -m estudo_re.coleta.atas [--max 500]

Baixa apenas as atas que cobrem os processos criminais do estudo, em ordem de
densidade (mais processos-alvo por ata primeiro), e guarda somente 5 campos.
Retomavel: pula as atas ja indexadas.

ARMADILHA CENTRAL: a ULTIMA distribuicao de um processo com RE e o "Registro" a
Vice-Presidencia, que a ata grava com `codigoOrgaoJulgador` NULO. A turma esta nas
distribuicoes ANTERIORES — por isso varremos todas as datas de distribuicao do
processo, nao so a ultima.
"""
import argparse, collections, gzip, json, os, re, sys, urllib.request
from pathlib import Path

CKAN = ("https://dadosabertos.web.stj.jus.br/api/3/action/"
        "package_show?id=atas-de-distribuicao")
so_dig = lambda s: re.sub(r"\D", "", s or "")


def abrir(caminho):
    p = Path(caminho)
    return gzip.open(p, "rt", encoding="utf-8") if p.suffix == ".gz" else open(p, encoding="utf-8")


def catalogo(cache):
    """Lista de recursos do CKAN, com cache local (o pacote tem ~1000 recursos)."""
    if os.path.exists(cache):
        return json.load(open(cache, encoding="utf-8"))
    d = json.loads(urllib.request.urlopen(CKAN, timeout=180).read())
    res = d["result"]["resources"]
    json.dump(res, open(cache, "w", encoding="utf-8"))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=500, help="quantas atas baixar nesta rodada")
    ap.add_argument("--datajud", default="data/raw/datajud_stj_re.jsonl.gz")
    ap.add_argument("--criminais", default="data/processed/criminais_3fontes.csv")
    ap.add_argument("--saida", default="data/raw/atas_indice.jsonl.gz")
    ap.add_argument("--checkpoint", default="data/raw/atas_coletadas.txt")
    ap.add_argument("--cache", default="data/raw/ckan_atas_recursos.json")
    a = ap.parse_args()

    url = {m.group(1): x["url"] for x in catalogo(a.cache)
           if (m := re.match(r"ata(\d{8})\.json$", x.get("name") or ""))}
    print(f"catalogo CKAN: {len(url)} atas disponiveis")

    # alvos: os processos criminais do estudo
    import csv
    with open(a.criminais, encoding="utf-8") as f:
        alvo = {so_dig(r["processo"]) for r in csv.DictReader(f)}
    print(f"processos-alvo: {len(alvo)}")

    # datas de distribuicao de cada alvo, vindas do DataJud (movimento 26)
    dens = collections.Counter()
    with abrir(a.datajud) as f:
        for l in f:
            s = json.loads(l)
            c = so_dig(s["numeroProcesso"])
            if c not in alvo:
                continue
            for m in (s.get("movimentos") or []):
                if m.get("codigo") == 26:
                    d = (m.get("dataHora") or "")[:10].replace("-", "")
                    if d >= "20230630" and d in url:
                        dens[d] += 1

    feitas = set()
    if os.path.exists(a.checkpoint):
        feitas = {l.strip() for l in open(a.checkpoint) if l.strip()}
    fila = [d for d, _ in dens.most_common() if d not in feitas][: a.max]
    print(f"atas relevantes: {len(dens)} | ja indexadas: {len(feitas)} | nesta rodada: {len(fila)}")
    if not fila:
        print("nada a fazer — cobertura ja completa para os alvos atuais")
        return

    saida = gzip.open(a.saida, "at", encoding="utf-8")
    marca = open(a.checkpoint, "a")
    for i, d in enumerate(fila, 1):
        try:
            data = json.loads(urllib.request.urlopen(url[d], timeout=300).read())
        except Exception as e:
            sys.stderr.write(f"  !! {d} falhou ({type(e).__name__}) — nao marcado\n")
            continue
        n = 0
        for r in data:
            cnj = so_dig(r.get("numeroUnico"))
            if cnj in alvo:
                saida.write(json.dumps({"cnj": cnj, "data": d,
                    "orgao": r.get("codigoOrgaoJulgador"),
                    "relator": r.get("nomeMinistroRelator"),
                    "forma": r.get("descFormaDistribuicao")}, ensure_ascii=False) + "\n")
                n += 1
        saida.flush()
        marca.write(d + "\n"); marca.flush()
        print(f"[{i}/{len(fila)}] {d}: {n} alvos ({len(data)} registros)", flush=True)
    saida.close(); marca.close()
    print("concluido")


if __name__ == "__main__":
    main()
