#!/usr/bin/env python3
"""
Extrai a taxonomia das decisoes de admissibilidade de RE (DJEN, orgao 59696).

    python3 taxonomia.py djen_re.jsonl [--csv taxonomia.csv]

Tres eixos, deliberadamente separados (nao colapsar):
  1. DISPOSITIVO  — qual saida do art. 1.030 CPC
  2. FUNDAMENTO   — por que (sumulas, ofensa reflexa, RG, esgotamento...)
  3. PARTES       — quem recorreu (MP x defesa), advogado, classe

Regras sao explicitas e auditaveis de proposito: cada rotulo guarda o trecho
que o disparou, para conferencia manual. O que nao casar sai como
'nao_classificado' — nunca chuta.
"""
import argparse, csv, gzip, html, json, re, sys, collections
from pathlib import Path
try:
    from .partes import perfil
except ImportError:      # execucao direta, fora do pacote
    from partes import perfil

def texto_limpo(h):
    t = re.sub(r"<br\s*/?>", " ", h or "")
    t = re.sub(r"</t[dr]>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()

# ---------- eixo 0: tipo de ato (pelo prefixo do cabecalho) ----------
# O orgao 59696 processa decisoes estrangeiras E recursos para o STF; e dentro
# dos recursos ha atos distintos (admissibilidade do RE, retratacao no ARE do
# art. 1.042, recurso ordinario, embargos). Sem separar isso, o dispositivo do
# art. 1.030 fica "nao classificado" em atos que nunca o teriam.
TIPO_ATO = [
    ("AgInt_1030_p2", r"^\s*Ag(?:Int|Rg)\s+n[oa]s?\s+(?:EDcl\s+n[oa]s?\s+)?RE\b"),
    ("ARE_1042",   r"^\s*(?:EDcl\s+no\s+)?ARE\s+n[oa]s?\s"),
    ("EDcl_no_RE", r"^\s*EDcl\s+n[oa]s?\s+RE\b"),
    ("RO_const",   r"^\s*RO\s+n[oa]s?\s"),
    ("RE_admiss",  r"^\s*RE\s+n[oa]s?\s"),
    ("SE_CR",      r"^\s*(?:SEC|SE|CR|HDE)\s+\d|^\s*PET\s+na\s+HDE"),
    ("incid_PET",  r"^\s*PET\s+n[oa]s?\s"),
    ("pauta_desist", r"^\s*(?:RtPaut|DESIS|Acordo)\s+n[oa]s?\s"),
]

# ---------- eixo 1: dispositivo (art. 1.030 CPC) ----------
DISPOSITIVO = [
    # O DISCRIMINANTE E O VERBO, nao o artigo. O art. 1.030, V e o juizo de
    # admissibilidade em si — pode ser POSITIVO ("nos termos do art. 1.030, V,
    # c, admito o recurso extraordinario") ou negativo. Classificar pelo inciso
    # transformava admissoes em inadmissoes.
    ("inadmite_1030_V",      r"n[ãa]o\s+admito\s+o\s+recurso\s+extraordin|\binadmito\b"),
    ("admite",               r"(?<!n[ãa]o )\badmito\s+o\s+recurso\s+extraordin|recurso\s+extraordin\w*\s+(?:é|e)\s+admitido"),
    ("nega_seg_1030_I",      r"nego\s+seguimento\s+ao\s+recurso\s+extraordin"),
    ("retratacao_1030_II",   r"ju[íi]zo\s+de\s+retrata[çc][ãa]o|encaminho\s+.{0,40}[óo]rg[ãa]o\s+julgador|remetam?-se\s+.{0,40}retrata"),
    ("sobresta_1030_III",    r"sobrest|suspend[oa]\s+o\s+(?:tr[âa]mite|processo|feito)"),
    ("representativo_1030_IV", r"representativ[oa]\s+d[ae]\s+controv[ée]rsia"),
    ("are_remete_1042",      r"n[ãa]o\s+sendo\s+caso\s+de\s+retrata[çc][ãa]o.{0,60}remetam?-se|art\.?\s*1\.?042,?\s*§\s*4"),
    ("ro_encaminha_stf",     r"peti[çc][ãa]o\s+de\s+recurso\s+ordin[áa]rio.{0,120}encaminhem-se"),
    ("vista_contrarrazoes",  r"intima[çc][ãa]o\s+para\s+apresenta[çc][ãa]o\s+de\s+contrarraz|abra-se\s+vista"),
    ("transito_arquiva",     r"certifique-se\s+o\s+tr[âa]nsito|exaurida\s+a\s+jurisdi[çc][ãa]o|nada\s+h[áa]\s+a\s+apreciar"),
    ("intima_gratuidade",    r"art\.?\s*99,?\s*§\s*2|comprove\s+.{0,30}hipossufici"),
]

# inciso do art. 1.030 efetivamente citado no dispositivo (analitico, separado)
INCISO = re.compile(r"art\.?\s*1\.?030,?\s*(?:inciso\s*)?(I{1,3}|IV|V)\s*(?:,\s*([ab]))?", re.I)

# ---------- eixo 2: fundamento ----------
FUNDAMENTO = [
    ("sum279_reexame_prova",     r"S[úu]mula\s*n?\.?\s*279\b|reexame\s+de\s+(?:prova|mat[ée]ria\s+f[áa]tico)"),
    ("sum280_norma_local",       r"S[úu]mula\s*n?\.?\s*280\b"),
    ("sum281_nao_esgotamento",   r"S[úu]mula\s*n?\.?\s*281\b|n[ãa]o\s+esgotamento\s+d[ao]s?\s+inst[âa]nci"),
    ("sum282_356_prequest",      r"S[úu]mula[s]?\s*n?\.?s?\.?\s*(?:282|356)\b|(?:aus[êe]ncia|falta)\s+de\s+prequestionamento"),
    ("sum283_fund_autonomo",     r"S[úu]mula\s*n?\.?\s*283\b"),
    ("sum284_deficiencia",       r"S[úu]mula\s*n?\.?\s*284\b|defici[êe]ncia\s+na\s+fundamenta"),
    ("sum286_sum7stj",           r"S[úu]mula\s*n?\.?\s*286\b|S[úu]mula\s*n?\.?\s*7\s*(?:do|\/)\s*STJ"),
    ("ofensa_reflexa",           r"ofensa\s+(?:reflexa|indireta)|viola[çc][ãa]o\s+reflexa"),
    ("rg_preliminar_ausente",    r"preliminar\s+(?:formal\s+)?de\s+repercuss[ãa]o\s+geral|art\.?\s*1\.?035,?\s*§\s*2"),
    ("rg_tema_conformidade",     r"tema\s*n?\.?\s*\d{1,4}|repercuss[ãa]o\s+geral"),
    ("intempestivo",             r"intempestiv|fora\s+do\s+prazo"),
    ("deserto_preparo",          r"deser[çt]|preparo"),
    ("repetitivo_conformidade",  r"recursos?\s+repetitivos?"),
]
# ---------- segmentacao: isolar o paragrafo DISPOSITIVO ----------
# Medido no piloto: 99,4% das decisoes de admissibilidade tem um marcador forte,
# e o segmento entre ele e "Publique-se" tem mediana de 124 chars. Classificar
# so ai dentro elimina o falso positivo de decisoes que DISCUTEM um inciso e
# DECIDEM por outro.
MARCADOR = re.compile(r"(Ante o exposto|Diante do exposto|Em face do exposto|Pelo exposto|"
                      r"Isso posto|Isto posto|Posto isso|Do exposto|Nesses termos|Ex positis)", re.I)
ENCERRA  = re.compile(r"Publique-se|Publique\.|Intimem-se|Cumpra-se|Int\.\s", re.I)

def segmentar(t):
    """(dispositivo, razoes) — dispositivo e o trecho decisorio; razoes e o que
    vem antes dele (onde vive a ratio). Sem marcador, cai para a cauda antes do
    encerramento."""
    ms = list(MARCADOR.finditer(t))
    if ms:
        ini = ms[-1].start()
    else:
        mf = ENCERRA.search(t)
        ini = max(0, (mf.start() if mf else len(t)) - 400)
    mf = ENCERRA.search(t, ini)
    fim = mf.start() if mf else len(t)
    return t[ini:fim], t[:ini]

# atos que nao sao juizo de admissibilidade mas aparecem no mesmo balde
DISPOSITIVO_ESPECIAL = [
    ("prejudicado_perda_objeto", r"prejudicad|perda\s+superveniente\s+de\s+objeto"),
    ("intima_preparo",           r"comprove\s+o\s+pagamento\s+do\s+preparo|sob\s+pena\s+de\s+deser"),
    ("suspeicao_impedimento",    r"declaro\s+a\s+minha\s+(?:suspei|impedi)"),
    ("desistencia_homologada",   r"homolog\w*\s+.{0,30}desist"),
]

TEMA_RG = re.compile(r"[Tt]ema\s*n?\.?\s*(\d{1,4})")
ASSINATURA = re.compile(r"\b(Vice-Presidente|Presidente|Ministr[oa])\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ]{3,}(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,}){1,4})\s*$")
CABECALHO = re.compile(r"^\s*(RE|ARE|AREsp|REsp|HC|RHC|EDcl|AgRg)[^(]{0,60}\(([\d/\-]+)\)")
PAPEIS = ("RECORRENTE","RECORRIDO","AGRAVANTE","AGRAVADO","IMPETRANTE","IMPETRADO",
          "PACIENTE","INTERESSADO","EMBARGANTE","EMBARGADO","ADVOGADO","ADVOGADA",
          "DEFENSORIA","ASSISTENTE","RELATOR","REQUERENTE","REQUERIDO","AUTORIDADE",
          "SUSCITANTE","SUSCITADO","REPRESENTADO","VÍTIMA","CORRÉU","RÉU")
MP = re.compile(r"MINIST[ÉE]RIO\s+P[ÚU]BLICO|PROCURADORIA[- ]GERAL", re.I)
DEFENSORIA = re.compile(r"DEFENSORIA\s+P[ÚU]BLICA", re.I)

def campos_cabecalho(t):
    """Extrai os pares PAPEL : VALOR do cabecalho tabular."""
    out = collections.defaultdict(list)
    padrao = re.compile(r"\b(" + "|".join(PAPEIS) + r")\s*:\s*(.{2,160}?)(?=\s+(?:" + "|".join(PAPEIS) + r")\s*:|\s+DECIS[ÃA]O\b|$)")
    for m in padrao.finditer(t):
        out[m.group(1)].append(m.group(2).strip(" .;"))
    return out

def classificar(item):
    t = texto_limpo(item.get("texto"))
    cab = campos_cabecalho(t)
    disp = [n for n, rx in DISPOSITIVO if re.search(rx, t, re.I)]
    fund = [n for n, rx in FUNDAMENTO if re.search(rx, t, re.I)]
    temas = sorted(set(TEMA_RG.findall(t)))
    ass = ASSINATURA.search(t)
    pf = perfil(item.get("texto"), item.get("nomeClasse") or "")
    ato = next((n for n, rx in TIPO_ATO if re.search(rx, t, re.I)), "outro")
    seg, razoes = segmentar(t)
    disp_seg = [n for n, rx in DISPOSITIVO if re.search(rx, seg, re.I)]
    if not disp_seg:
        disp_seg = [n for n, rx in DISPOSITIVO_ESPECIAL if re.search(rx, seg, re.I)]
    # rotulo primario por precedencia (o ato decisorio mais especifico vence)
    ORDEM = ["inadmite_1030_V","admite","nega_seg_1030_I","retratacao_1030_II",
             "sobresta_1030_III","representativo_1030_IV","are_remete_1042",
             "are_retrata_1042","ro_encaminha_stf","prejudicado_perda_objeto",
             "intima_preparo","suspeicao_impedimento","desistencia_homologada",
             "vista_contrarrazoes","transito_arquiva","intima_gratuidade"]
    prim = next((x for x in ORDEM if x in disp_seg), (disp_seg[0] if disp_seg else "nao_classificado"))
    # combinacao legitima: nega seguimento quanto a uma tese e inadmite quanto a outra
    if {"inadmite_1030_V", "nega_seg_1030_I"} <= set(disp_seg):
        prim = "misto_I_e_V"
    # fundamento: ancorado (dispositivo + 800 chars anteriores ~ ratio) x mencionado
    ancora = razoes[-1500:] + " " + seg
    fund_anc = [n for n, rx in FUNDAMENTO if re.search(rx, ancora, re.I)]
    return {
        "id": item.get("id"),
        "tipo_ato": ato,
        "data": item.get("data_disponibilizacao"),
        "processo": item.get("numeroprocessocommascara"),
        "classe": item.get("nomeClasse"),
        "tipoDocumento": item.get("tipoDocumento"),
        "dispositivo": prim,
        "dispositivo_multi": "|".join(disp_seg) or "nao_classificado",
        "n_dispositivos": len(disp_seg),
        "dispositivo_texto": seg[:200],
        "inciso_citado": (lambda m: (m.group(1).upper() + (", " + m.group(2).lower() if m.group(2) else "")) if m else "")(INCISO.search(seg)),
        "fundamentos": "|".join(fund_anc) or "nao_classificado",
        "fundamentos_mencionados": "|".join(fund) or "nao_classificado",
        "temas_rg": ",".join(temas),
        "polo_recorrente": pf["polo_recorrente"],
        "criminal": pf["criminal"],
        "tipo_recorrente": pf["tipo_recorrente"],
        "n_advogados": pf["n_advogados"],
        "anonimizado": pf["parte_anonimizada"],
        "recorrente": pf["recorrentes"],
        "recorrido": pf["recorridos"],
        "advogado": pf["advogado_1"],
        "defensoria": pf["com_defensoria"],
        "assinatura": (f"{ass.group(1)} {ass.group(2).strip()}" if ass else ""),
        "n_chars": len(t),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada"); ap.add_argument("--csv", default="taxonomia.csv")
    a = ap.parse_args()
    p = Path(a.entrada)
    abrir = (lambda: gzip.open(p, "rt", encoding="utf-8")) if p.suffix == ".gz" else (lambda: open(p, encoding="utf-8"))
    with abrir() as fh:
        linhas = [classificar(json.loads(l)) for l in fh if l.strip()]
    if not linhas: sys.exit("nada a processar")
    with open(a.csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys())); w.writeheader(); w.writerows(linhas)

    dec = [r for r in linhas if r["tipoDocumento"] == "DESPACHO / DECISÃO"]
    print(f"comunicacoes: {len(linhas)}  |  DESPACHO/DECISAO: {len(dec)}\n")
    def tab(rot, campo, base, split=False):
        c = collections.Counter()
        for r in base:
            v = r[campo]
            for x in (v.split("|") if split else [v]):
                if x: c[x] += 1
        print(f"--- {rot} (n={len(base)}) ---")
        for k, v in c.most_common(14):
            print(f"   {v:>6}  {100*v/len(base):5.1f}%  {k}")
        print()
    tab("TIPO DE DOCUMENTO", "tipoDocumento", linhas)
    tab("TIPO DE ATO (cabecalho)", "tipo_ato", dec)
    adm = [r for r in dec if r["tipo_ato"] == "RE_admiss"]
    tab("DISPOSITIVO (rotulo unico, ancorado no paragrafo final)", "dispositivo", adm)
    multi = [r for r in adm if int(r["n_dispositivos"]) > 1]
    print(f"   >> decisoes com mais de um dispositivo no segmento: {len(multi)} "
          f"({100*len(multi)/max(1,len(adm)):.1f}%)\n")
    tab("FUNDAMENTO ancorado (ratio: dispositivo + 1500 chars anteriores)", "fundamentos", adm, split=True)
    tab("FUNDAMENTO apenas mencionado em qualquer ponto (p/ comparacao)", "fundamentos_mencionados", adm, split=True)
    tab("POLO DO RECORRENTE (todas as materias)", "polo_recorrente", adm)
    tab("TIPO DO RECORRENTE", "tipo_recorrente", adm)
    crim = [r for r in adm if str(r["criminal"]) == "True"]
    print(f">>> feitos criminais: {len(crim)}/{len(adm)} ({100*len(crim)/max(1,len(adm)):.1f}%)\n")
    tab("POLO — SO CRIMINAIS", "polo_recorrente", crim)
    print("--- TAXA DE ADMISSAO por polo (so criminais) ---")
    for pl in ("MP", "defesa/particular"):
        sub = [r for r in crim if r["polo_recorrente"] == pl]
        a = sum(1 for r in sub if r["dispositivo"] == "admite")
        if sub: print(f"   {pl:<22} {a:>4} / {len(sub):<5} = {100*a/len(sub):5.1f}%")
    print()
    tab("ASSINATURA", "assinatura", dec)
    tab("CLASSE", "classe", adm)
    temas = collections.Counter(x for r in adm for x in r["temas_rg"].split(",") if x)
    print(f"--- TEMAS DE RG citados (top) ---")
    for k, v in temas.most_common(10): print(f"   {v:>6}  Tema {k}")
    nc = [r for r in adm if r["dispositivo"] == "nao_classificado"]
    print(f"\nnao classificados no dispositivo (dentro de RE_admiss): {len(nc)} ({100*len(nc)/max(1,len(adm)):.1f}%)")

if __name__ == "__main__":
    main()
