# Makefile for Drone Traffic Visualizer

.PHONY: help install demo server frontend test clean

help:
	@echo "Drone Traffic Visualizer - Available commands:"
	@echo ""
	@echo "  make install   - Install all dependencies (backend + frontend)"
	@echo "  make demo      - Generate demo scenario data"
	@echo "  make server    - Start FastAPI backend server"
	@echo "  make frontend  - Start React frontend dev server"
	@echo "  make test      - Run all unit tests"
	@echo "  make clean     - Remove generated files and caches"
	@echo ""

install:
	@echo "Installing backend dependencies..."
	pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd src/web && npm install
	@echo "Installation complete!"

demo:
	@echo "Generating demo scenario..."
	python3 src/scenarios/generate_demo.py
	@echo "Demo scenario generated!"

server:
	@echo "Starting FastAPI server on http://localhost:8000..."
	python3 -m uvicorn src.server.app:app --reload --port 8000

frontend:
	@echo "Starting React frontend on http://localhost:3000..."
	cd src/web && npm run dev

test:
	@echo "Running unit tests..."
	python3 -m pytest tests/ -v

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage
	@echo "Cleanup complete!"
