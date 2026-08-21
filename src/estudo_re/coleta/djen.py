#!/usr/bin/env python3
"""
Coletor DJEN — decisoes de admissibilidade de RE do STJ.

Baixa as comunicacoes do orgao 59696 ("SPF COORDENADORIA DE PROCESSAMENTO DE
DECISOES ESTRANGEIRAS E RECURSOS PARA O STF") dia a dia, com pacing e backoff,
gravando JSONL incremental. E RETOMAVEL: relanca e ele pula os dias ja feitos.

    python3 coletor_djen.py [--inicio 2024-08-22] [--fim 2026-08-19]
                            [--orgao 59696] [--saida djen_re.jsonl]
                            [--pausa 5] [--limite-dias N]

Contrato da API (verificado 2026-08-20 — a doc do puxaproc esta desatualizada):
  * envelope {status, message, count, items} — NAO ha 'dadosResposta'
  * paginacao: pagina (1-based) + itensPorPagina (200 ok)
  * count satura em 10000 -> por isso fatiamos por DIA
  * parametro nao reconhecido e IGNORADO em silencio e devolve o diario
    nacional inteiro. O filtro de orgao e 'orgaoId' (nao 'idOrgao').
  * 422 se itensPorPagina>5 sem um destes: siglaTribunal, texto, nomeParte,
    nomeAdvogado, numeroOab, numeroProcesso. Por isso mandamos siglaTribunal
    SEMPRE junto com orgaoId.
  * rate limit: rajadas devolvem 500 "O sistema esta muito ocupado"
"""
import argparse, json, os, sys, time, urllib.request, urllib.parse
from datetime import date, timedelta

BASE = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
HDRS = {"Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
        "Origin": "https://comunica.pje.jus.br",
        "Referer": "https://comunica.pje.jus.br/"}

def buscar(params, pausa, tentativas=7):
    url = BASE + "?" + urllib.parse.urlencode(params)
    espera = pausa
    for t in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=300) as r:
                d = json.loads(r.read())
            time.sleep(pausa)
            return d.get("count"), d.get("items") or []
        except Exception as e:
            if hasattr(e, "read"):
                try: e.read()
                except Exception: pass
            espera = min(espera * 2, 180)
            sys.stderr.write(f"      retry {t+1}/{tentativas} em {espera}s ({type(e).__name__})\n")
            sys.stderr.flush()
            time.sleep(espera)
    return None, []

def dias_uteis(ini, fim):
    d = date.fromisoformat(ini); f = date.fromisoformat(fim)
    while d <= f:
        if d.weekday() < 5: yield d.isoformat()
        d += timedelta(days=1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", default="2024-08-22")
    ap.add_argument("--fim", default="2026-08-19")
    ap.add_argument("--orgao", type=int, default=59696)
    ap.add_argument("--tribunal", default="STJ")
    ap.add_argument("--saida", default="djen_re.jsonl")
    ap.add_argument("--pausa", type=float, default=5.0)
    ap.add_argument("--limite-dias", type=int, default=0)
    a = ap.parse_args()

    estado = a.saida + ".dias"
    feitos = set()
    if os.path.exists(estado):
        feitos = {l.strip() for l in open(estado) if l.strip()}
    alvo = [d for d in dias_uteis(a.inicio, a.fim) if d not in feitos]
    if a.limite_dias: alvo = alvo[:a.limite_dias]
    print(f"dias uteis pendentes: {len(alvo)} (ja concluidos: {len(feitos)})", flush=True)

    saida = open(a.saida, "a", encoding="utf-8")
    marca = open(estado, "a")
    total = 0
    for n, dia in enumerate(alvo, 1):
        base = {"siglaTribunal": a.tribunal, "orgaoId": a.orgao, "dataDisponibilizacaoInicio": dia,
                "dataDisponibilizacaoFim": dia, "itensPorPagina": 200}
        pag, no_dia = 1, 0
        while True:
            cnt, itens = buscar({**base, "pagina": pag}, a.pausa)
            if cnt is None:
                sys.stderr.write(f"   !! {dia} falhou apos retries — NAO marcado, rode de novo\n")
                break
            for it in itens:
                saida.write(json.dumps(it, ensure_ascii=False) + "\n")
            no_dia += len(itens)
            if len(itens) < 200: 
                marca.write(dia + "\n"); marca.flush()
                break
            pag += 1
        saida.flush()
        total += no_dia
        print(f"[{n}/{len(alvo)}] {dia}: {no_dia} comunicacoes (acum {total})", flush=True)
    saida.close(); marca.close()
    print(f"\nconcluido. {total} comunicacoes novas em {a.saida}", flush=True)

if __name__ == "__main__":
    main()
