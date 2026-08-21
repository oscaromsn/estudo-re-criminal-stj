"""Testes de fumaça: travam os contratos que já quebraram uma vez.

    python3 -m unittest discover -s tests -t .

Não cobrem a coleta (dependeria de rede). Cobrem a classificação, que é onde os
erros silenciosos moram.
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estudo_re.processamento.partes import parse_cabecalho, perfil, tipo_parte, anonimizado

CABECALHO = """<html><body><table>
<tr><td colspan="3"><b>RE no AREsp 1234567/SP (2025/0000000-0)</b></td></tr>
<tr><td>RELATOR</td><td>:</td><td>MINISTRO VICE-PRESIDENTE DO STJ</td></tr>
<tr><td>RECORRENTE</td><td>:</td><td>FULANO DE TAL</td></tr>
<tr><td>ADVOGADOS</td><td>:</td><td>PRIMEIRO ADVOGADO - SP000001</td></tr>
<tr><td></td><td></td><td>SEGUNDO ADVOGADO - SP000002</td></tr>
<tr><td>RECORRIDO</td><td>:</td><td>MINISTÉRIO PÚBLICO DO ESTADO DE SÃO PAULO</td></tr>
</table>DECISÃO Ante o exposto, com fundamento no art. 1.030, V, do Código de
Processo Civil, não admito o recurso extraordinário. Publique-se.
Vice-Presidente LUIS FELIPE SALOMÃO</body></html>"""


class TestPartes(unittest.TestCase):
    def test_continuacao_de_papel(self):
        """Célula de papel vazia continua o papel anterior — o bug do ADR-004."""
        _, pares = parse_cabecalho(CABECALHO)
        advs = [v for p, v in pares if p.startswith("ADVOGADO")]
        self.assertEqual(len(advs), 2, "perdeu a segunda linha de ADVOGADOS")

    def test_polo_e_criminal(self):
        p = perfil(CABECALHO, "AGRAVO EM RECURSO ESPECIAL")
        self.assertEqual(p["polo_recorrente"], "defesa/particular")
        self.assertTrue(p["criminal"], "MP no polo passivo deve marcar criminal")
        self.assertEqual(p["n_advogados"], 2)

    def test_tipos(self):
        self.assertEqual(tipo_parte("MINISTÉRIO PÚBLICO FEDERAL"), "MP")
        self.assertEqual(tipo_parte("DIRECIONAL ENGENHARIA S/A"), "pessoa_juridica")
        self.assertEqual(tipo_parte("DEFENSORIA PÚBLICA DA UNIÃO"), "Defensoria")
        self.assertEqual(tipo_parte("ESTADO DE SÃO PAULO"), "ente_publico")
        self.assertEqual(tipo_parte("FULANO DE TAL"), "pessoa_fisica")

    def test_anonimizado(self):
        self.assertTrue(anonimizado("P O P S"))
        self.assertTrue(anonimizado("M T DA S F"))
        self.assertFalse(anonimizado("FULANO DE TAL"))


class TestDispositivo(unittest.TestCase):
    """Trava o ADR-003: o verbo decide, não o inciso."""

    def setUp(self):
        from estudo_re.processamento import taxonomia as t
        self.t = t

    def _classificar(self, texto):
        item = {"texto": f"<html><body>RE no AREsp 1/SP (2025/0-0) {texto}</body></html>",
                "nomeClasse": "", "id": 1, "data_disponibilizacao": "2025-01-01",
                "numeroprocessocommascara": "", "tipoDocumento": "DESPACHO / DECISÃO"}
        return self.t.classificar(item)["dispositivo"]

    def test_nao_admito_nao_e_admissao(self):
        """'não admito' contém 'admito' — 99 inadmissões viraram admissões uma vez."""
        d = self._classificar("Ante o exposto, com fundamento no art. 1.030, V, do CPC, "
                              "não admito o recurso extraordinário. Publique-se.")
        self.assertEqual(d, "inadmite_1030_V")

    def test_inciso_V_pode_ser_positivo(self):
        """art. 1.030, V é o juízo de admissibilidade — pode ADMITIR."""
        d = self._classificar("Ante o exposto, nos termos do art. 1.030, V, c, do CPC, "
                              "admito o recurso extraordinário. Publique-se.")
        self.assertEqual(d, "admite")

    def test_nega_seguimento(self):
        d = self._classificar("Ante o exposto, com amparo no art. 1.030, I, a, do CPC, "
                              "nego seguimento ao recurso extraordinário. Publique-se.")
        self.assertEqual(d, "nega_seg_1030_I")

    def test_ancoragem_ignora_discussao_anterior(self):
        """Discutir o inciso I e decidir pelo V deve render só o V (ADR-002)."""
        d = self._classificar("A parte sustenta a aplicação do art. 1.030, I, a, e o tema 181. "
                              "Contudo, é caso de nego seguimento? Não. "
                              "Ante o exposto, com fundamento no art. 1.030, V, do CPC, "
                              "não admito o recurso extraordinário. Publique-se.")
        self.assertEqual(d, "inadmite_1030_V")


class TestNaturezaDaFalha(unittest.TestCase):
    """Trava a classificação normativa do ADR-011."""

    def setUp(self):
        from estudo_re.analise.defesa import natureza
        self.natureza = natureza

    def test_evitavel_vence_estrutural(self):
        """Se há causa evitável, ela é o diagnóstico — mesmo com tema de RG junto."""
        self.assertEqual(self.natureza("rg_tema_conformidade|sum281_nao_esgotamento"), "evitável")

    def test_enquadramento_vence_estrutural(self):
        self.assertEqual(self.natureza("rg_tema_conformidade|ofensa_reflexa"), "enquadramento")

    def test_estrutural(self):
        self.assertEqual(self.natureza("rg_tema_conformidade"),
                         "estrutural (tese fechada no STF)")

    def test_sem_fundamento(self):
        self.assertEqual(self.natureza("nao_classificado"), "não classificado")


if __name__ == "__main__":
    unittest.main()
