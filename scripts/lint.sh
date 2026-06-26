#!/bin/bash
set -euo pipefail

echo "Running flake8..."
python -m flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203,W503

echo "Running isort check..."
python -m isort src/ tests/ --check-only --diff

echo "Linting complete."
