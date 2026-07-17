.PHONY: install generate-pdfs ingest api test lint clean

install:
	pip install -r requirements.txt
	cd src/web && npm install

generate-pdfs:
	python src/ingestion/generate_sample_pdfs.py

ingest:
	python src/ingestion/ingest_documents.py

api:
	python src/api/main.py

web:
	cd src/web && npm run dev

test:
	python3 -m compileall src/ -q && PYTHONPATH=src pytest tests/ -v

lint:
	python3 -m flake8 src/ tests/ --max-line-length=120 --ignore=E501,W503

clean:
	rm -rf sample-docs/*.pdf
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

help:
	@echo "Available commands:"
	@echo "  make install        - Install Python and Node.js dependencies"
	@echo "  make generate-pdfs  - Generate synthetic sample PDFs in sample-docs/"
	@echo "  make ingest         - Ingest documents into Azure AI Search"
	@echo "  make api            - Start the backend API server (http://localhost:8000)"
	@echo "  make web            - Start the React frontend (http://localhost:5173)"
	@echo "  make test           - Run all tests"
	@echo "  make lint           - Run Python linters"
	@echo "  make clean          - Remove generated files"
