#!/usr/bin/env python3
"""
Testa se o caminho Jus.br/PDPJ serve para obter o INTEIRO TEOR de decisões
de admissibilidade de RE em processos do STJ nos quais o requisitante
NAO e parte — a pergunta que decide o estudo jurimetrico.

Uso:
    PDPJ_TOKEN="eyJ..." python3 probe-stj-integra.py

Como obter o token (conta gov.br-federada, 8h de validade):
    1. Abra https://portaldeservicos.pdpj.jus.br/consulta e faça login gov.br
    2. DevTools > Network > qualquer request para /api/v2/processos
    3. Copie o header Authorization (sem o prefixo "Bearer ")

Somente GETs. Nao faz login, nao gasta lockout budget.
"""
import json, os, sys, urllib.request, urllib.error

TOKEN = os.environ.get("PDPJ_TOKEN", "").strip().replace("Bearer ", "")
if not TOKEN:
    sys.exit("erro: defina PDPJ_TOKEN (veja o cabecalho deste arquivo)")

PORTAL = "https://portaldeservicos.pdpj.jus.br/api/v2"
LAKE   = "https://api-processo.data-lake.pdpj.jus.br/processo-api/api/v1"
H = {
    "authorization": f"Bearer {TOKEN}",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "accept": "application/json, text/plain, */*",
    "accept-language": "pt-BR,pt;q=0.9",
    "origin": "https://portaldeservicos.pdpj.jus.br",
    "referer": "https://portaldeservicos.pdpj.jus.br/consulta",
    "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin",
}

def get(url, accept_json=True):
    req = urllib.request.Request(url, headers=H)
    try:
        r = urllib.request.urlopen(req, timeout=60)
        body = r.read()
        if accept_json:
            try: return r.status, json.loads(body)
            except Exception: return r.status, body[:400].decode("utf-8", "replace")
        return r.status, body
    except urllib.error.HTTPError as e:
        raw = e.read()[:400].decode("utf-8", "replace")
        return e.code, raw
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"

def rotulo(status, body):
    t = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)[:300]
    if "não possui acesso" in t or "nao possui acesso" in t: return "SEM LEGITIMIDADE"
    if status == 0 or "<html" in t.lower(): return "BLOQUEADO (WAF/rede)"
    if status in (401, 403): return "TOKEN REJEITADO"
    if status == 200: return "OK"
    return f"HTTP {status}"

# quem e o token
try:
    import base64
    p = TOKEN.split(".")[1]; p += "=" * (-len(p) % 4)
    c = json.loads(base64.urlsafe_b64decode(p))
    print(f"token: cpf={c.get('preferred_username')} exp={c.get('exp')} scope={c.get('scope')}\n")
except Exception:
    print("token: (nao decodificavel)\n")

alvos = json.load(open(os.path.join(os.path.dirname(__file__), "alvos.json")))

print("=" * 78)
print("TESTE 1 — capa/documentos de processo do STJ em que voce NAO e parte")
print("=" * 78)
achou_doc = None
for a in alvos[:4]:
    st, body = get(f"{PORTAL}/processos?numeroProcesso={a['cnj']}")
    r = rotulo(st, body)
    n_docs = 0
    if r == "OK" and isinstance(body, (list, dict)):
        conteudo = body.get("content", body) if isinstance(body, dict) else body
        if isinstance(conteudo, list) and conteudo:
            tram = conteudo[0].get("tramitacoes") or conteudo[0].get("tramitacaoAtual") or {}
            tram = tram[0] if isinstance(tram, list) and tram else tram
            docs = (tram or {}).get("documentos") or []
            n_docs = len(docs)
            if docs and not achou_doc:
                achou_doc = (a["cnj"], docs)
    print(f"  {a['cnj']}  {a['classe'][:28]:<28} {a['desfecho']:<15} -> {r:<18} docs={n_docs}")
    if r != "OK":
        print(f"      resposta: {str(body)[:180]}")

print()
print("=" * 78)
print("TESTE 2 — INTEIRO TEOR de um documento (Data Lake)")
print("=" * 78)
if not achou_doc:
    print("  pulado: nenhum processo devolveu lista de documentos no teste 1")
else:
    cnj, docs = achou_doc
    for d in docs[:3]:
        href = d.get("hrefTexto") or ""
        uuid = href.rstrip("/").split("/")[-1] if href else None
        nome = (d.get("nome") or d.get("tipo", {}).get("nome") or "?")[:40]
        if not uuid:
            print(f"  {nome:<40} sem hrefTexto"); continue
        st, body = get(f"{LAKE}/processos/{cnj}/documentos/{uuid}/texto"
                       f"?numeroProcesso={cnj}&idDocumento={uuid}", accept_json=False)
        if st == 200:
            txt = body.decode("utf-8", "replace") if isinstance(body, bytes) else str(body)
            print(f"  {nome:<40} OK  {len(txt)} chars")
            print(f"      inicio: {' '.join(txt.split())[:220]}")
        else:
            print(f"  {nome:<40} {rotulo(st, body)}  {str(body)[:150]}")

print()
print("=" * 78)
print("TESTE 3 — busca em massa no Data Lake (o premio: dispensaria o DJe)")
print("=" * 78)
for nome, url in [
    ("por tribunal",  f"{LAKE}/processos?tribunal=STJ&size=1"),
    ("contagem",      f"{LAKE}/processos:contar?tribunal=STJ"),
    ("um processo",   f"{LAKE}/processos/{alvos[0]['cnj']}"),
    ("documentos",    f"{LAKE}/processos/{alvos[0]['cnj']}/documentos"),
    ("possui-acesso", f"{LAKE}/processos/{alvos[0]['cnj']}/possui-acesso"),
]:
    st, body = get(url)
    print(f"  {nome:<15} -> {rotulo(st, body):<18} {str(body)[:170]}")
