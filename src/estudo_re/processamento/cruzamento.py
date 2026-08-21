#!/usr/bin/env python3
"""Cruza as tres fontes numa unica tabela analitica.

    DJEN      -> fundamento, dispositivo, partes, advogados  (o QUE foi decidido)
    DataJud   -> assunto TPU, classe, movimentos datados      (SOBRE O QUE)
    Atas      -> turma de origem e relator do acordao         (DE ONDE veio)

    python3 -m estudo_re.processamento.cruzamento \
        --taxonomia data/interim/taxonomia_completa.csv.gz \
        --datajud   data/raw/datajud_stj_re.jsonl.gz \
        --atas      data/raw/atas_indice.jsonl.gz \
        --saida     data/processed/criminais_3fontes.csv

Chave de juncao: numero CNJ so-digitos. O DJEN publica com mascara
(`0000000-00.0000.0.00.0000`) e o DataJud sem — normalizar e obrigatorio.

Cuidado com a turma: a ULTIMA distribuicao de um processo com RE e o "Registro"
a Vice-Presidencia, que a ata grava com `codigoOrgaoJulgador` NULO. A turma de
origem esta nas distribuicoes ANTERIORES.
"""
import argparse, collections, csv, gzip, json, re, sys, unicodedata
from pathlib import Path

TURMA = {"T5": "Quinta Turma", "T6": "Sexta Turma", "S3": "Terceira Seção",
         "T1": "Primeira Turma", "T2": "Segunda Turma", "T3": "Terceira Turma",
         "T4": "Quarta Turma", "S1": "Primeira Seção", "S2": "Segunda Seção",
         "CE": "Corte Especial"}
RAIZES_CRIMINAIS = [287, 1209, 11068, 11049]  # PENAL, PROC PENAL, e os militares

so_digitos = lambda s: re.sub(r"\D", "", s or "")


def abrir(caminho):
    p = Path(caminho)
    return gzip.open(p, "rt", encoding="utf-8") if p.suffix == ".gz" else open(p, encoding="utf-8")


def codigos_criminais(spec):
    """Descendentes das raizes criminais na arvore TPU de assuntos do CNJ."""
    with abrir(spec) as f:
        tpu = json.load(f)
    filhos = collections.defaultdict(list)
    for a in tpu:
        filhos[a.get("cod_item_pai")].append(a.get("cod_item"))
    vistos, pilha = set(), list(RAIZES_CRIMINAIS)
    while pilha:
        c = pilha.pop()
        if c in vistos:
            continue
        vistos.add(c)
        pilha.extend(x for x in filhos.get(c, []) if x is not None)
    return vistos


# --- reserva: quando nao ha evento de Distribuicao a uma turma ---
# Parte dos processos so tem eventos `forma="Registro"` (registro regimental a
# Presidencia/Vice), sem orgao julgador. Quando esse registro nomeia o ministro,
# a turma sai do mapa gabinete->turma, derivado das proprias Atas. E INFERENCIA,
# nao observacao — por isso a coluna `turma_fonte` distingue as duas origens.
_STOP = {"DO","DA","DE","DOS","DAS","MINISTRO","MINISTRA","GABINETE","DESEMBARGADOR",
         "DESEMBARGADORA","CONVOCADO","CONVOCADA","JUNIOR","NETO","FILHO"}
_INSTITUCIONAL = ("VICE-PRESIDENTE", "PRESIDENTE DO STJ", "PRESIDENTE DA")


def _tokens(s):
    s = unicodedata.normalize("NFKD", (s or "").upper()).encode("ascii", "ignore").decode()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^A-Z ]", " ", s)
    return {t for t in s.split() if t not in _STOP and len(t) > 2}


def carregar_mapa(caminho):
    try:
        return list(csv.DictReader(open(caminho, encoding="utf-8")))
    except FileNotFoundError:
        return []


def turma_por_relator(mapa, nome, aaaamm):
    """Turma do ministro na competencia dada. None se ambiguo ou desconhecido."""
    tn = _tokens(nome)
    if not tn:
        return None
    achados = set()
    for m in mapa:
        tm = _tokens(m["ministro_atas"])
        if tm and (tn <= tm or tm <= tn or len(tn & tm) >= 2):
            if m["inicio"] <= aaaamm <= m["fim"]:
                achados.add(m["turma"])
    return achados.pop() if len(achados) == 1 else None


def achatar(a, saida=None):
    """`assuntos` as vezes vem como lista de listas — normaliza para lista de dicts."""
    saida = [] if saida is None else saida
    if isinstance(a, dict):
        saida.append(a)
    elif isinstance(a, list):
        for x in a:
            achatar(x, saida)
    return saida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--taxonomia", default="data/interim/taxonomia_completa.csv.gz")
    ap.add_argument("--datajud", default="data/raw/datajud_stj_re.jsonl.gz")
    ap.add_argument("--atas", default="data/raw/atas_indice.jsonl.gz")
    ap.add_argument("--tpu", default="data/referencia/tpu-assuntos.json.gz")
    ap.add_argument("--mapa", default="data/processed/mapa_gabinete_turma.csv")
    ap.add_argument("--saida", default="data/processed/criminais_3fontes.csv")
    ap.add_argument("--saida-decisoes", default="data/processed/decisoes_admissibilidade.csv")
    a = ap.parse_args()

    crim = codigos_criminais(a.tpu)
    print(f"codigos TPU criminais: {len(crim)}")

    dj = {}
    with abrir(a.datajud) as f:
        for l in f:
            s = json.loads(l)
            dj[so_digitos(s["numeroProcesso"])] = s
    print(f"DataJud: {len(dj)} processos")

    atas = collections.defaultdict(list)
    with abrir(a.atas) as f:
        for l in f:
            r = json.loads(l)
            atas[r["cnj"]].append(r)
    print(f"Atas: {len(atas)} processos indexados")

    # Projecao enxuta de TODAS as decisoes de admissibilidade (todas as materias),
    # independente de casarem com o DataJud. E a base de `analise/resultados.py` e
    # `analise/defesa.py`. Antes era gerada por script avulso — o que a deixava
    # desatualizada sempre que a taxonomia era reprocessada.
    COLS_DEC = ["id", "data", "processo", "classe", "criminal", "dispositivo",
                "inciso_citado", "fundamentos", "temas_rg", "polo_recorrente",
                "tipo_recorrente", "n_advogados", "defensoria", "anonimizado", "assinatura"]
    n_dec = 0
    with abrir(a.taxonomia) as f, open(a.saida_decisoes, "w", newline="", encoding="utf-8") as g:
        w = csv.DictWriter(g, fieldnames=COLS_DEC)
        w.writeheader()
        for r in csv.DictReader(f):
            if r["tipo_ato"] == "RE_admiss" and r["tipoDocumento"] == "DESPACHO / DECISÃO":
                w.writerow({c: r.get(c, "") for c in COLS_DEC}); n_dec += 1
    print(f"decisões de admissibilidade: {n_dec} -> {a.saida_decisoes}")

    mapa = carregar_mapa(a.mapa)
    linhas, casou = [], 0
    origem_turma = collections.Counter()
    with abrir(a.taxonomia) as f:
        for r in csv.DictReader(f):
            if r["tipo_ato"] != "RE_admiss" or r["tipoDocumento"] != "DESPACHO / DECISÃO":
                continue
            cnj = so_digitos(r["processo"])
            s = dj.get(cnj)
            if not s:
                continue
            casou += 1
            ass = achatar(s.get("assuntos"))
            cods = {x.get("codigo") for x in ass if isinstance(x.get("codigo"), int)}
            if not (cods & crim):
                continue
            # 1) observacao direta: evento de Distribuicao com orgao julgador
            regs = [x for x in atas.get(cnj, []) if x.get("orgao") in TURMA]
            regs.sort(key=lambda x: x["data"])
            if regs:
                turma, relator = TURMA[regs[-1]["orgao"]], regs[-1].get("relator") or ""
                fonte = "ata_direta"
            else:
                # 2) reserva: registro que nomeia o ministro + mapa gabinete->turma
                nom = [x for x in atas.get(cnj, [])
                       if x.get("relator") and not any(k in x["relator"] for k in _INSTITUCIONAL)]
                nom.sort(key=lambda x: x["data"])
                turma = relator = ""
                fonte = "nao resolvida"
                if nom and mapa:
                    t = turma_por_relator(mapa, nom[-1]["relator"], nom[-1]["data"][:6])
                    if t:
                        # o mapa grava em caixa alta; normalizar para nao criar
                        # categorias duplicadas na analise
                        turma, relator, fonte = t.title(), nom[-1]["relator"], "mapa_relator"
                if not turma:
                    turma = "nao resolvida"
            origem_turma[fonte] += 1
            linhas.append({
                "processo": r["processo"], "data": r["data"],
                "classe": (s.get("classe") or {}).get("nome", ""),
                "assunto_criminal": next((x.get("nome") for x in ass if x.get("codigo") in crim), ""),
                "assuntos_todos": "; ".join(x.get("nome", "") for x in ass),
                "turma_origem": turma,
                "turma_fonte": fonte,
                "relator_origem": relator,
                "dispositivo": r["dispositivo"], "inciso_citado": r["inciso_citado"],
                "fundamento": r["fundamentos"], "temas_rg": r["temas_rg"],
                "polo_recorrente": r["polo_recorrente"],
                "tipo_recorrente": r["tipo_recorrente"],
                "n_advogados": r["n_advogados"], "defensoria": r["defensoria"],
                "parte_anonimizada": r["anonimizado"], "assinatura": r["assinatura"],
            })
    with open(a.saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    print(f"\ndecisoes casadas com DataJud: {casou}")
    print(f"criminais (TPU): {len(linhas)}")
    res = sum(v for k, v in origem_turma.items() if k != "nao resolvida")
    print(f"  turma de origem resolvida: {res} ({100*res/max(1,len(linhas)):.1f}%)")
    for k, v in origem_turma.most_common():
        print(f"    {k}: {v}")
    print(f"escrito: {a.saida}")


if __name__ == "__main__":
    main()
