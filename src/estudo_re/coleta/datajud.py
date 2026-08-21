#!/usr/bin/env python3
"""Coleta o esqueleto processual no DataJud (API Publica do CNJ, indice do STJ).

Baixa todos os processos que tenham ao menos um movimento de admissibilidade de
recurso extraordinario. Serve de FRAME PROCESSUAL (classe, assuntos TPU,
movimentos datados) — nao traz texto de decisao nem partes.

    python3 -m estudo_re.coleta.datajud --saida data/raw/datajud_stj_re.jsonl

Contrato da API (verificado 2026-08-20):
  * POST https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search
  * header `Authorization: APIKey <chave publica do CNJ>` — a chave e publicada
    pelo proprio CNJ, identica para todos; nao e credencial de ninguem.
  * Elasticsearch DSL. Paginacao por cursor `search_after` (sem offset).
  * `movimentos` NAO e mapeado como `nested`: combinar `movimentos.codigo` com
    `range` em `movimentos.dataHora` na mesma bool casa campos de movimentos
    DIFERENTES. Por isso filtramos data no cliente, nunca na query.
  * `sort` por `id.keyword` e estavel e unico (o `id` e
    TRIBUNAL_CLASSE_GRAU_ORGAO_NUMERO); ordenar por `_id` e recusado.
  * agregacoes funcionam (util para exploracao barata).
"""
import argparse, json, sys, time, urllib.request

CHAVE = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
URL = "https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search"

# Codigos TPU com flag `presidenteVice` na tabela do CNJ. Fonte de verdade:
# `_CNJ - OpenAPI specs and payloads/2 - sample payloads/tpu-movimentos.json`.
MOVIMENTOS = {
    429: "RE admitido",
    432: "RE nao admitido",
    15621: "Negado seguimento ao RE (tema RG)",
    265: "Sobrestado por RE com repercussao geral",
}


def buscar(payload, tentativas=5):
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode(),
        headers={"Authorization": f"APIKey {CHAVE}", "Content-Type": "application/json"})
    for t in range(tentativas):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except Exception as e:
            sys.stderr.write(f"   retry {t+1}: {type(e).__name__}\n")
            time.sleep(5 * (t + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="data/raw/datajud_stj_re.jsonl")
    ap.add_argument("--tamanho", type=int, default=500)
    a = ap.parse_args()

    depois, total = None, 0
    with open(a.saida, "w", encoding="utf-8") as f:
        while True:
            corpo = {"size": a.tamanho, "sort": [{"id.keyword": "asc"}],
                     "query": {"terms": {"movimentos.codigo": list(MOVIMENTOS)}}}
            if depois:
                corpo["search_after"] = depois
            r = buscar(corpo)
            if r is None:
                sys.exit("falha apos retries — relance para retomar do inicio")
            hits = r["hits"]["hits"]
            if not hits:
                break
            for h in hits:
                f.write(json.dumps(h["_source"], ensure_ascii=False) + "\n")
            total += len(hits)
            print(f"  {total} processos", flush=True)
            if len(hits) < a.tamanho:
                break
            depois = hits[-1]["sort"]
    print(f"concluido: {total} processos em {a.saida}")


if __name__ == "__main__":
    main()
