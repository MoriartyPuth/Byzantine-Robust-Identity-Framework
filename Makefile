# Byzantine-Robust Identity Framework
# Requires: GNU Make (available in Git Bash / WSL on Windows)

PYTHON  = python
PYTEST  = pytest
PIP     = pip

.PHONY: install run-baseline run-byzantine run-dp run-reputation run-full \
        dashboard test coverage clean

# ── Setup ──────────────────────────────────────────────────────────────────
install:
	$(PIP) install -r requirements.txt

# ── Experiments ────────────────────────────────────────────────────────────
run-baseline:
	$(PYTHON) main.py --mode baseline

run-byzantine:
	$(PYTHON) main.py --mode byzantine

run-dp:
	$(PYTHON) main.py --mode dp

run-reputation:
	$(PYTHON) main.py --mode reputation

run-full:
	$(PYTHON) main.py --mode full

# ── Dashboard ──────────────────────────────────────────────────────────────
dashboard:
	streamlit run dashboard.py

# ── Testing ────────────────────────────────────────────────────────────────
test:
	$(PYTEST) tests/ -v

coverage:
	$(PYTEST) tests/ --cov=core --cov=data --cov-report=term-missing

# ── Cleanup ────────────────────────────────────────────────────────────────
clean:
	rm -rf logs/*.csv logs/*.log reports/report.html reports/report.pdf
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
