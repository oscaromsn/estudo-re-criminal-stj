"""Extracao de partes do cabecalho tabular do DJEN (STJ).

O cabecalho e uma tabela de 3 colunas: [papel] [:] [valor]. Celula de papel
vazia = continuacao do papel anterior (varios advogados, varios recorrentes).
Parsear a tabela e muito mais robusto que regex sobre o texto achatado, que
perdia continuacoes e confundia limites entre papel e valor.
"""
import re, html, unicodedata

LINHA = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
CELULA = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)

def _txt(h):
    t = re.sub(r"<[^>]+>", " ", h or "")
    return re.sub(r"\s+", " ", html.unescape(t)).strip()

def parse_cabecalho(bruto):
    """-> (titulo, [(papel, valor), ...]) na ordem em que aparecem."""
    titulo, pares, papel_atual = "", [], None
    for tr in LINHA.findall(bruto or ""):
        cels = [_txt(c) for c in CELULA.findall(tr)]
        if len(cels) == 1:
            if not titulo: titulo = cels[0]
            continue
        if len(cels) < 3: continue
        papel, valor = cels[0].strip(" :"), cels[2].strip()
        if papel: papel_atual = papel
        if valor and papel_atual: pares.append((papel_atual, valor))
    return titulo, pares

# ---------- classificacao do tipo de parte ----------
MP   = re.compile(r"MINIST[ÉE]RIO\s+P[ÚU]BLICO|PROCURADORIA[- ]GERAL\s+D[EA]\s+JUSTI", re.I)
DPU  = re.compile(r"DEFENSORIA\s+P[ÚU]BLICA", re.I)
ENTE = re.compile(r"\b(UNI[ÃA]O|ESTADO\s+D[EO]|MUNIC[ÍI]PIO|DISTRITO\s+FEDERAL|INSS|"
                  r"INSTITUTO\s+NACIONAL|FAZENDA\s+(?:NACIONAL|P[ÚU]BLICA)|AG[ÊE]NCIA\s+NACIONAL|"
                  r"CAIXA\s+ECON[ÔO]MICA|BANCO\s+CENTRAL|AUTARQUIA)\b", re.I)
PJ   = re.compile(r"\b(S/?A|S\.A\.?|LTDA|EIRELI|EPP|ME|COMPANHIA|CIA\.?|BANCO|SEGUROS?|"
                  r"EMPREENDIMENTOS|PARTICIPA[ÇC][ÕO]ES|ASSOCIA[ÇC][ÃA]O|SINDICATO|"
                  r"COOPERATIVA|FUNDA[ÇC][ÃA]O|INCORPORA)\b", re.I)

def anonimizado(nome):
    """Partes sob sigilo vem como iniciais: 'P O P S', 'M T DA S F'."""
    toks = [t for t in re.split(r"\s+", nome) if t not in ("DA","DE","DO","DAS","DOS","E")]
    return bool(toks) and all(len(t) <= 2 for t in toks)

def tipo_parte(nome):
    if not nome: return "vazio"
    if MP.search(nome):   return "MP"
    if DPU.search(nome):  return "Defensoria"
    if ENTE.search(nome): return "ente_publico"
    if PJ.search(nome):   return "pessoa_juridica"
    if anonimizado(nome): return "anonimizado"
    return "pessoa_fisica"

# papeis que identificam o recorrente do RE e o polo passivo
P_ATIVO  = ("RECORRENTE", "AGRAVANTE", "EMBARGANTE", "IMPETRANTE", "REQUERENTE", "SUSCITANTE")
P_PASSIVO= ("RECORRIDO", "AGRAVADO", "EMBARGADO", "IMPETRADO", "REQUERIDO", "SUSCITADO")
P_ADV    = ("ADVOGADO", "ADVOGADA", "ADVOGADOS", "ADVOGADAS")
# marcadores de que o feito e criminal
CRIM_PAPEL = ("PACIENTE", "R[ÉE]U", "ACUSADO", "INDICIADO", "CORR[ÉE]U", "V[ÍI]TIMA",
              "ASSISTENTE DE ACUSA", "SENTENCIADO")
# Sinal de que o feito e de improbidade administrativa — civel, apesar do MP.
IMPROBIDADE = re.compile(r"improbidade|lei\s*n?\.?\s*8\.?429|ato[s]?\s+[íi]mprobo", re.I)

def perfil(bruto, classe=""):
    titulo, pares = parse_cabecalho(bruto)
    def pega(chaves):
        return [v for p, v in pares
                if any(p.upper().startswith(c.rstrip("S")) for c in chaves)]
    ativos   = pega(P_ATIVO)
    passivos = pega(P_PASSIVO)
    advs     = pega(P_ADV)
    papeis   = " ".join(p.upper() for p, _ in pares)
    # O MP e parte em improbidade administrativa, e a presenca dele disparava o
    # flag numa acao CIVIL. A contaminacao era de 2,4% no geral, mas concentrada
    # em desfechos raros: 23 dos 37 casos de retratacao eram improbidade (Tema
    # 1199, retroatividade da Lei 14.230/2021), nao materia criminal. Papel
    # criminal explicito (PACIENTE, REU, ACUSADO) ou classe habeas corpus
    # prevalecem sobre a exclusao — um crime pode ser discutido em ACP conexa.
    crim_explicito = (bool(re.search("|".join(CRIM_PAPEL), papeis))
                      or "HABEAS CORPUS" in (classe or "").upper())
    criminal = (crim_explicito
                or (bool(MP.search(" ".join(ativos + passivos)))
                    and not (IMPROBIDADE.search(bruto or "") and not crim_explicito)))
    t_at = [tipo_parte(x) for x in ativos]
    if "MP" in t_at:                           polo = "MP"
    elif any(MP.search(x) for x in passivos):  polo = "defesa/particular"
    elif t_at:                                 polo = "sem MP no feito"
    else:                                      polo = "nao extraido"
    return {
        "titulo": titulo,
        "n_pares": len(pares),
        "recorrentes": " ; ".join(ativos)[:120],
        "recorridos": " ; ".join(passivos)[:120],
        "tipo_recorrente": t_at[0] if t_at else "vazio",
        "tipos_recorrente_todos": "|".join(sorted(set(t_at))),
        "n_advogados": len(advs),
        "advogado_1": (advs[0] if advs else "")[:60],
        "com_defensoria": any(DPU.search(x) for x in ativos + advs),
        "parte_anonimizada": any(anonimizado(x) for x in ativos + passivos),
        "criminal": criminal,
        "polo_recorrente": polo,
    }
