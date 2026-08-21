#!/usr/bin/env python3
"""Recorte defensivo: onde o RE da defesa falha e onde passa.

    python3 -m estudo_re.analise.defesa [--saida resultados/]

Muda a pergunta de "como a Vice-Presidencia decide" para "o que a defesa pode
fazer a respeito". A distincao que organiza tudo e entre falha EVITAVEL (erro
processual ou de redacao, corrigivel pelo advogado), falha de ENQUADRAMENTO
(pediu ao RE o que ele nao entrega) e falha ESTRUTURAL (a tese ja esta fechada
no STF, e nenhuma peca resolveria).

Essa classificacao e NORMATIVA e contestavel — ver docs/03, ADR-011. Os grupos
estao declarados abaixo para que discordar seja facil.
"""
import argparse, collections, csv, gzip, os

# --- classificacao normativa da falha (ADR-011) ---
EVITAVEL = {
    "sum281_nao_esgotamento": "não esgotou a instância (cabia agravo interno antes)",
    "sum282_356_prequest":    "falta de prequestionamento",
    "sum284_deficiencia":     "fundamentação deficiente (Súmula 284)",
    "rg_preliminar_ausente":  "sem preliminar formal de repercussão geral",
    "intempestivo":           "intempestivo",
    "deserto_preparo":        "deserção / preparo",
}
ENQUADRAMENTO = {
    "sum279_reexame_prova":   "pediu reexame de prova (Súmula 279)",
    "ofensa_reflexa":         "ofensa reflexa — questão infraconstitucional",
    "sum286_sum7stj":         "esbarra na Súmula 7/STJ",
    "sum280_norma_local":     "interpretação de norma local",
    "sum283_fund_autonomo":   "fundamento autônomo não atacado",
}
DESFAVORAVEL = ("nega_seg_1030_I", "inadmite_1030_V")
# Desfechos que mantêm o recurso vivo — não são admissão, mas não são derrota.
PARCIAL = ("retratacao_1030_II", "sobresta_1030_III")


def natureza(fundamentos):
    f = set(fundamentos.split("|"))
    if f & set(EVITAVEL):        return "evitável"
    if f & set(ENQUADRAMENTO):   return "enquadramento"
    if "rg_tema_conformidade" in f: return "estrutural (tese fechada no STF)"
    return "não classificado"


def escrever(saida, nome, cab, linhas):
    with open(os.path.join(saida, nome), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cab); w.writerows(linhas)


def pct(n, d):
    return f"{100*n/d:.1f}%" if d else "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisoes", default="data/processed/decisoes_admissibilidade.csv")
    ap.add_argument("--completa", default="data/interim/taxonomia_completa.csv.gz")
    ap.add_argument("--saida", default="resultados")
    a = ap.parse_args()
    os.makedirs(a.saida, exist_ok=True)

    todas = list(csv.DictReader(open(a.decisoes, encoding="utf-8")))
    d = [r for r in todas if r["criminal"] == "True"
         and r["polo_recorrente"] == "defesa/particular"]
    adm = [r for r in d if r["dispositivo"] == "admite"]
    desf = [r for r in d if r["dispositivo"] in DESFAVORAVEL]
    parc = [r for r in d if r["dispositivo"] in PARCIAL]
    print(f"decisões criminais com a defesa recorrente: {len(d)}")
    print(f"  admitidas: {len(adm)} ({100*len(adm)/len(d):.2f}%)")
    print(f"  desfavoráveis: {len(desf)}   |   mantêm o recurso vivo: {len(parc)}\n")

    # 1. natureza da falha
    c = collections.Counter(natureza(r["fundamentos"]) for r in desf)
    linhas = [(k, v, pct(v, len(desf))) for k, v in c.most_common()]
    escrever(a.saida, "07_defesa_natureza_da_falha.csv", ["natureza", "n", "pct"], linhas)
    print("--- NATUREZA DA FALHA ---")
    for k, v, p in linhas: print(f"   {v:>6}  {p:>6}  {k}")

    # 2. detalhe das evitáveis — o que é corrigível pelo advogado
    ev = collections.Counter()
    for r in desf:
        for k in r["fundamentos"].split("|"):
            if k in EVITAVEL: ev[k] += 1
    linhas = [(EVITAVEL[k], v, pct(v, len(desf))) for k, v in ev.most_common()]
    escrever(a.saida, "08_defesa_falhas_evitaveis.csv", ["causa", "n", "pct_das_derrotas"], linhas)
    print("\n--- FALHAS EVITÁVEIS ---")
    for k, v, p in linhas: print(f"   {v:>6}  {p:>6}  {k}")

    # 3. temas que barram
    tem = collections.Counter(x for r in desf if "rg_tema_conformidade" in r["fundamentos"]
                              for x in r["temas_rg"].split(",") if x)
    linhas = [(f"Tema {k}", v) for k, v in tem.most_common(12)]
    escrever(a.saida, "09_defesa_temas_que_barram.csv", ["tema", "n"], linhas)
    print("\n--- TEMAS DE RG QUE BARRAM A DEFESA ---")
    for k, v in linhas[:6]: print(f"   {v:>6}  {k}")

    # 4. perfil das admissões — onde a defesa passa
    perf = {
        "inciso_citado": collections.Counter(r["inciso_citado"] for r in adm),
        "classe": collections.Counter(r["classe"] for r in adm),
        "com_tema_rg": collections.Counter("sem tema" if not r["temas_rg"] else "com tema" for r in adm),
    }
    linhas = [(dim, k, v, pct(v, len(adm))) for dim, cc in perf.items() for k, v in cc.most_common()]
    escrever(a.saida, "10_defesa_perfil_das_admissoes.csv", ["dimensao", "valor", "n", "pct"], linhas)
    print(f"\n--- PERFIL DAS {len(adm)} ADMISSÕES ---")
    for dim, cc in perf.items():
        print(f"   {dim}: {', '.join(f'{k or 'vazio'}={v}' for k, v in cc.most_common(4))}")

    # 5. Defensoria x advocacia privada
    linhas = []
    for flag, rot in (("True", "Defensoria Pública"), ("False", "advocacia privada")):
        sub = [r for r in d if r["defensoria"] == flag]
        aa = sum(1 for r in sub if r["dispositivo"] == "admite")
        evd = sum(1 for r in sub if natureza(r["fundamentos"]) == "evitável")
        linhas.append((rot, len(sub), aa, pct(aa, len(sub)), pct(evd, len(sub))))
    escrever(a.saida, "11_defesa_por_representacao.csv",
             ["representacao", "n", "admitidos", "taxa_admissao", "pct_falha_evitavel"], linhas)
    print("\n--- REPRESENTAÇÃO ---")
    for l in linhas: print(f"   {l[0]:<20} n={l[1]:<7} admite {l[2]:>3} ({l[3]})  evitável {l[4]}")

    # 6. agravo interno — DESAGREGADO POR POLO.
    # A taxa agregada (~13%) é puxada pelo MP; reportar sem desagregar induz a erro.
    ag = []
    with gzip.open(a.completa, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["tipo_ato"] == "AgInt_1030_p2" and r["tipoDocumento"] == "DESPACHO / DECISÃO" \
               and r["criminal"] == "True":
                ag.append(r)
    linhas = []
    for polo in ("MP", "defesa/particular"):
        sub = [r for r in ag if r["polo_recorrente"] == polo]
        aa = sum(1 for r in sub if r["dispositivo"] == "admite")
        linhas.append((polo, len(sub), aa, pct(aa, len(sub))))
    escrever(a.saida, "12_agravo_interno_por_polo.csv",
             ["polo", "n", "reconsiderados", "taxa"], linhas)
    print(f"\n--- AGRAVO INTERNO art. 1.030 §2º (criminais, n={len(ag)}) ---")
    for l in linhas: print(f"   {l[0]:<20} n={l[1]:<6} reconsiderados {l[2]:>3} ({l[3]})")
    base = len(adm) / len(d)
    sub = [r for r in ag if r["polo_recorrente"] == "defesa/particular"]
    if sub and base:
        t = sum(1 for r in sub if r["dispositivo"] == "admite") / len(sub)
        print(f"   defesa: via direta {100*base:.2f}% → via agravo interno {100*t:.2f}% ({t/base:.0f}x)")
    print(f"\ntabelas escritas em {a.saida}/")


if __name__ == "__main__":
    main()
