## Day 19 — Vector Store + Feature Store lab.
## Two paths: lightweight (default, no Docker) and full Docker.

VENV := .venv

# Detect OS (Windows vs Unix/macOS) to set proper venv binary paths
ifeq ($(OS),Windows_NT)
    VENV_BIN := $(VENV)/Scripts
    PY_SYS   := python
    PY       := $(VENV_BIN)/python.exe
    PIP      := $(VENV_BIN)/pip.exe
    JUPYTER  := $(VENV_BIN)/jupyter.exe
    JUPYTEXT := $(VENV_BIN)/jupytext.exe
    UVICORN  := $(VENV_BIN)/uvicorn.exe
    PYTEST   := $(VENV_BIN)/pytest.exe
else
    VENV_BIN := $(VENV)/bin
    PY_SYS   := python3
    PY       := $(VENV_BIN)/python
    PIP      := $(VENV_BIN)/pip
    JUPYTER  := $(VENV_BIN)/jupyter
    JUPYTEXT := $(VENV_BIN)/jupytext
    UVICORN  := $(VENV_BIN)/uvicorn
    PYTEST   := $(VENV_BIN)/pytest
endif

export PYTHONUTF8 := 1
export PYTHONIOENCODING := utf-8
export PYTHONUNBUFFERED := 1

.DEFAULT_GOAL := help

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nLightweight path (default):\n"} \
	      /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST) 2>/dev/null || \
	$(PY_SYS) -c "import re; lines=open('Makefile', encoding='utf-8').readlines(); print('\nUsage:\n  make <target>\n'); [print(f'  {m.group(1):<16} {m.group(2)}') for line in lines if (m := re.match(r'^([a-zA-Z_-]+):.*?##\s*(.*)$$', line))]"

# ─────────────────────────────────────────────────────────────
# Lightweight path (default) — no Docker, in-process Qdrant
# ─────────────────────────────────────────────────────────────

setup-lite: ## [lite] Create venv + install + seed corpus + smoke test
	@bash setup-lite.sh 2>/dev/null || $(PY_SYS) -c "import subprocess, sys; subprocess.run(['uv', 'venv', '$(VENV)'], check=False) or subprocess.run([sys.executable, '-m', 'venv', '$(VENV)']); subprocess.run(['$(PIP)', 'install', '-r', 'requirements.txt'], check=True); subprocess.run(['$(PY)', 'scripts/seed_corpus.py'], check=True); subprocess.run(['$(PY)', 'scripts/gen_agent_queries.py'], check=True); subprocess.run(['$(PY)', 'scripts/gen_spend.py'], check=True); subprocess.run(['$(PY)', 'scripts/verify_lite.py'], check=True)"

verify-lite: ## [lite] 5-second smoke test (Qdrant memory + BM25 + Feast SQLite)
	@$(PY) scripts/verify_lite.py

seed: ## [both] (Re)generate data/corpus_vn.jsonl + data/golden_set.jsonl
	@$(PY) scripts/seed_corpus.py

api: ## [lite] Start FastAPI /search on http://localhost:8000
	@$(UVICORN) app.main:app --reload --port 8000

lab: ## [lite] Open Jupyter Lab on http://localhost:8888
	@$(JUPYTEXT) --to notebook --update notebooks/[0-9]*.py 2>/dev/null || true
	@$(JUPYTER) lab --notebook-dir=notebooks --ServerApp.token='' --no-browser

benchmark: ## [both] Precision@10 (keyword/semantic/hybrid) + P99 latency table
	@$(PY) scripts/benchmark.py

test: ## [both] Run pytest (app + scripts + tests)
	@$(PYTEST) -q

gen-advanced: ## [both] Generate data for the advanced missions (NB6 + NB8)
	@$(PY) scripts/gen_agent_queries.py
	@$(PY) scripts/gen_spend.py

notebooks: ## [both] Execute ALL notebooks headless (what the grader runs)
	@$(JUPYTEXT) --to notebook --update notebooks/[0-9]*.py 2>/dev/null || true
	@$(PY) scripts/run_notebooks.py

clean-lite: ## [lite] Wipe venv + data + Feast registry
	@$(PY_SYS) -c "import shutil, glob, os; paths=['$(VENV)', 'data/corpus_vn.jsonl', 'data/golden_set.jsonl', 'data/qdrant_storage', 'data/agent_queries.jsonl', 'data/spend_monthly.parquet', 'app/feast_repo/data', 'app/feast_repo/registry.db', 'app/feast_repo/online_store.db', 'app/feast_repo_ondemand/data', 'app/feast_repo_ondemand/registry.db', 'app/feast_repo_ondemand/online_store.db', 'notebooks/*.ipynb', 'notebooks/.ipynb_checkpoints']; [shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else (os.remove(p) if os.path.exists(p) else None) for pattern in paths for p in glob.glob(pattern)]"

# ─────────────────────────────────────────────────────────────
# Docker path (full stack: Qdrant + Redis + Postgres)
# ─────────────────────────────────────────────────────────────

setup-docker: ## [docker] Bring up Docker stack + venv + seed + smoke test
	@bash setup-docker.sh

runtime-check: ## [docker] Report docker / podman / apple-container versions + capabilities
	@bash scripts/runtime-check.sh

container-up: ## [apple] Start the 3 services with Apple container (no compose)
	@bash scripts/container-up.sh

container-down: ## [apple] Stop the Apple container stack (add ARGS=--wipe to drop volumes)
	@bash scripts/container-down.sh $(ARGS)

verify-docker: ## [docker] Verify all 3 services reachable + Feast wired
	@$(PY) scripts/verify_docker.py

docker-up: ## [docker] Just bring services up (no venv changes)
	docker compose up -d

docker-down: ## [docker] Stop services (data persists)
	docker compose down

docker-clean: ## [docker] Stop AND wipe Qdrant + Redis + Postgres volumes
	docker compose down -v

.PHONY: help setup-lite verify-lite seed gen-advanced notebooks api lab benchmark test clean-lite \
        setup-docker verify-docker docker-up docker-down docker-clean \
        runtime-check container-up container-down

