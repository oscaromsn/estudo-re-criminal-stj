#!/usr/bin/env python3
"""Gera as tabelas de resultado do estudo a partir da base cruzada.

    python3 -m estudo_re.analise.resultados \
        --decisoes  data/processed/decisoes_admissibilidade.csv \
        --criminais data/processed/criminais_3fontes.csv \
        --saida     resultados/

Cada tabela sai em CSV (para reuso) e e impressa (para leitura). Nenhuma
estatistica inferencial aqui de proposito: o desenho ainda e descritivo, e
qualquer teste exigiria tratar a dependencia entre decisoes do mesmo tema de
repercussao geral (ver docs/04-limitacoes-e-vieses.md).
"""
import argparse, collections, csv, os


def escrever(saida, nome, cabecalho, linhas):
    with open(os.path.join(saida, nome), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cabecalho); w.writerows(linhas)


def bloco(titulo, cabecalho, linhas, larguras):
    print(f"\n--- {titulo} ---")
    print("".join(f"{c:>{w}}" if i else f"{c:<{w}}" for i, (c, w) in enumerate(zip(cabecalho, larguras))))
    for l in linhas:
        print("".join(f"{v:>{w}}" if i else f"{str(v):<{w}}" for i, (v, w) in enumerate(zip(l, larguras))))


def pct(n, d):
    return f"{100*n/d:.1f}%" if d else "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisoes", default="data/processed/decisoes_admissibilidade.csv")
    ap.add_argument("--criminais", default="data/processed/criminais_3fontes.csv")
    ap.add_argument("--saida", default="resultados")
    a = ap.parse_args()
    os.makedirs(a.saida, exist_ok=True)

    dec = list(csv.DictReader(open(a.decisoes, encoding="utf-8")))
    crm = list(csv.DictReader(open(a.criminais, encoding="utf-8")))
    print(f"decisoes de admissibilidade: {len(dec)}   |   criminais cruzadas: {len(crm)}")

    # 1. dispositivo geral
    c = collections.Counter(r["dispositivo"] for r in dec)
    linhas = [(k, v, pct(v, len(dec))) for k, v in c.most_common()]
    escrever(a.saida, "01_dispositivo.csv", ["dispositivo", "n", "pct"], linhas)
    bloco("DISPOSITIVO (todas as materias)", ["dispositivo", "n", "%"], linhas, [30, 8, 9])

    # 2. assimetria MP x defesa (usa o flag criminal do proprio DJEN)
    cri = [r for r in dec if r.get("criminal") == "True"]
    linhas = []
    for polo in ("MP", "defesa/particular"):
        sub = [r for r in cri if r["polo_recorrente"] == polo]
        adm = sum(1 for r in sub if r["dispositivo"] == "admite")
        linhas.append((polo, adm, len(sub), pct(adm, len(sub))))
    escrever(a.saida, "02_assimetria_polo.csv", ["polo", "admitidos", "total", "taxa"], linhas)
    bloco("TAXA DE ADMISSAO POR POLO (criminais)", ["polo", "admitidos", "total", "taxa"], linhas, [24, 11, 8, 9])
    if len(linhas) == 2 and linhas[1][2]:
        tm = linhas[0][1] / linhas[0][2] if linhas[0][2] else 0
        td = linhas[1][1] / linhas[1][2] if linhas[1][2] else 0
        print(f"   razao MP/defesa = {tm/td:.1f}x" if td else "   razao indefinida")

    # 3. serie trimestral da assimetria
    def tri(d):
        return f"{d[:4]}-T{(int(d[5:7])-1)//3+1}" if d else "?"
    ser = collections.defaultdict(collections.Counter)
    for r in cri:
        s = ser[tri(r["data"])]
        s[r["polo_recorrente"] + "_t"] += 1
        if r["dispositivo"] == "admite":
            s[r["polo_recorrente"] + "_a"] += 1
    linhas = []
    for k in sorted(ser):
        s = ser[k]
        linhas.append((k, s["MP_a"], s["MP_t"], pct(s["MP_a"], s["MP_t"]),
                       s["defesa/particular_a"], s["defesa/particular_t"],
                       pct(s["defesa/particular_a"], s["defesa/particular_t"])))
    escrever(a.saida, "03_serie_trimestral.csv",
             ["trimestre", "mp_adm", "mp_tot", "mp_taxa", "def_adm", "def_tot", "def_taxa"], linhas)
    bloco("SERIE TRIMESTRAL", ["trim", "MPadm", "MPtot", "MP%", "Dadm", "Dtot", "D%"], linhas, [10, 8, 8, 9, 8, 8, 9])

    # 4. por assunto criminal
    by = collections.defaultdict(collections.Counter)
    for r in crm:
        b = by[r["assunto_criminal"]]; b["t"] += 1
        if r["dispositivo"] == "admite": b["a"] += 1
        if r["polo_recorrente"] == "MP": b["mp"] += 1
    linhas = [(k, v["t"], pct(v["a"], v["t"]), pct(v["mp"], v["t"]))
              for k, v in sorted(by.items(), key=lambda x: -x[1]["t"]) if v["t"] >= 100]
    escrever(a.saida, "04_por_assunto.csv", ["assunto", "n", "taxa_admissao", "pct_mp_recorrente"], linhas)
    bloco("POR ASSUNTO CRIMINAL (n>=100)", ["assunto", "n", "%adm", "%MP"], linhas, [46, 7, 9, 9])

    # 5. por turma de origem — SOMENTE observacao direta nas Atas.
    # O grupo resolvido pelo mapa gabinete->turma tem perfil estruturalmente
    # distinto (processos que so tiveram "Registro", sem Distribuicao a turma):
    # ~62% de inadmissao e ~61% de MP recorrente, contra ~15% e ~18% no grupo
    # direto. Misturar contamina a comparacao entre turmas.
    direto = [r for r in crm if r.get("turma_fonte") == "ata_direta"]
    by = collections.defaultdict(collections.Counter)
    for r in direto:
        b = by[r["turma_origem"]]; b["t"] += 1
        b[r["dispositivo"]] += 1
        if r["polo_recorrente"] == "MP": b["mp"] += 1
    linhas = [(k, v["t"], pct(v["admite"], v["t"]), pct(v["nega_seg_1030_I"], v["t"]),
               pct(v["inadmite_1030_V"], v["t"]), pct(v["mp"], v["t"]))
              for k, v in sorted(by.items(), key=lambda x: -x[1]["t"])]
    # procedencia da resolucao de turma — observacao direta x inferencia pelo mapa
    proc = collections.Counter(r.get("turma_fonte", "?") for r in crm)
    escrever(a.saida, "05b_procedencia_turma.csv", ["fonte", "n", "pct"],
             [(k, v, pct(v, len(crm))) for k, v in proc.most_common()])
    escrever(a.saida, "05_por_turma.csv",
             ["turma", "n", "taxa_admissao", "pct_nega_seguimento", "pct_inadmite", "pct_mp"], linhas)
    bloco("POR TURMA DE ORIGEM (só observação direta nas Atas)",
          ["turma", "n", "%adm", "%negaseg", "%inadm", "%MP"], linhas, [22, 7, 9, 10, 9, 8])
    print(f"   base: {len(direto)} de {len(crm)} decisões criminais "
          f"({pct(len(direto), len(crm))}); ver docs/04, limitação 3")

    # 6. temas de repercussao geral
    neg = collections.Counter(x for r in crm if r["dispositivo"] == "nega_seg_1030_I"
                              and r["polo_recorrente"] == "defesa/particular"
                              for x in r["temas_rg"].split(",") if x)
    adm = collections.Counter(x for r in crm if r["dispositivo"] == "admite"
                              and r["polo_recorrente"] == "MP"
                              for x in r["temas_rg"].split(",") if x)
    linhas = ([("negativa a defesa", f"Tema {k}", v) for k, v in neg.most_common(8)] +
              [("admissao do MP", f"Tema {k}", v) for k, v in adm.most_common(8)])
    escrever(a.saida, "06_temas_rg.csv", ["contexto", "tema", "n"], linhas)
    bloco("TEMAS DE REPERCUSSAO GERAL", ["contexto", "tema", "n"], linhas, [22, 14, 8])

    print(f"\ntabelas escritas em {a.saida}/")


if __name__ == "__main__":
    main()
