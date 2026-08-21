# Pipeline do estudo. Cada alvo depende do anterior, mas os dados intermediários
# estão versionados — normalmente basta `make analise`.
PY := python3
export PYTHONPATH := src

.PHONY: analise defesa cruzamento taxonomia coleta atas teste limpar ajuda

ajuda:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-14s %s\n",$$1,$$2}'

analise: ## Regera as tabelas de resultado (segundos)
	$(PY) -m estudo_re.analise.resultados

defesa: ## Recorte defensivo — onde o RE da defesa falha e onde passa
	$(PY) -m estudo_re.analise.defesa

cruzamento: ## Refaz o cruzamento das três fontes (~1 min)
	$(PY) -m estudo_re.processamento.cruzamento

taxonomia: ## Reclassifica o corpus DJEN inteiro (~8 min)
	$(PY) -m estudo_re.processamento.taxonomia data/raw/djen_comunicacoes.jsonl.gz \
		--csv data/interim/taxonomia_completa.csv
	@# cruzamento lê o .gz — sem recomprimir aqui, ele consumiria a versão anterior
	gzip -f -k data/interim/taxonomia_completa.csv

coleta: ## Rebaixa DJEN e DataJud das APIs (~3 h, retomável)
	$(PY) -m estudo_re.coleta.djen --inicio 2024-11-01 --fim 2026-08-19 --pausa 4
	$(PY) -m estudo_re.coleta.datajud

atas: ## Indexa mais atas para elevar a cobertura de turma de origem
	$(PY) -m estudo_re.coleta.atas --max 500

teste: ## Testes de fumaça da classificação
	$(PY) -m unittest discover -s tests -t .

limpar: ## Remove apenas artefatos regeráveis
	rm -f resultados/*.csv data/interim/taxonomia_completa.csv
