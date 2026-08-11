# Operating loop for the panel. The deployed app reads the *committed* CSVs
# in data/ - a local refresh is invisible to it until the data is pushed.
#
#   make refresh    fetch the latest data locally (prints a freshness report)
#   make publish    commit refreshed data/ and push (updates the deployed site)
#   make update     refresh + publish in one go
#   make app        run the Streamlit app locally

PYTHON ?= .venv/bin/python

.PHONY: refresh publish update app

refresh:
	$(PYTHON) -m fetch.run_all

publish:
	@if [ -n "$$(git status --porcelain -- data/)" ]; then \
		git add data/ && \
		git commit -m "data: refresh $$(date +%Y-%m-%d)" -- data/ && \
		git push; \
	else \
		echo "data/ unchanged - nothing to publish"; \
	fi

update: refresh publish

app:
	$(PYTHON) -m streamlit run app/streamlit_app.py
