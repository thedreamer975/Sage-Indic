# SAGE-Indic

**A Linguistically-Aware, Safe and Evidence-Grounded LLM Framework for Indic Languages**

---

## 1. Project Overview

**SAGE-Indic** is a research-oriented NLP/LLM framework focused initially on Telugu across three primary input forms:
1. **Native Telugu** (Telugu script)
2. **Romanized Telugu** (Latin script)
3. **Telugu-English Code-Mixed text**

The core goal of this project is to investigate the quality–efficiency–safety–factuality trade-off of a linguistically-aware LLM pipeline.

---

## 2. Repository Structure

```text
Sage-Indic/
├── configs/          # Configuration files (YAML / JSON)
├── data/             # Datasets (raw and processed data)
├── docs/             # Documentation and Product Requirements Document (PRD.md)
├── experiments/      # Reproducible experiment configurations and outputs
├── notebooks/        # Exploratory analysis and visualization notebooks
├── scripts/          # Utility and verification scripts
├── src/
│   └── sage_indic/   # Core library source code
│       ├── __init__.py
│       ├── config.py # Environment and settings management
│       └── logging.py# Logging configuration
├── tests/            # Automated test suite (pytest)
├── .env.example      # Template for environment variables
├── .gitignore        # Git ignore rules for research artifacts
├── AGENTS.md         # Non-negotiable research rules and agent guidelines
├── pyproject.toml    # Python project configuration, dependencies, pytest & ruff settings
└── README.md         # Project documentation
```

---

## 3. Getting Started

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- `pip` or virtual environment manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd Sage-Indic
   ```

2. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # Linux/macOS
   source .venv/bin/activate
   ```

3. **Install the package in editable mode:**
   ```bash
   pip install -e .
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

---

## 4. Development & Testing

### Running Tests
Execute the pytest suite:
```bash
pytest
```

### Running Linter & Formatter
Run Ruff for linting and code formatting checks:
```bash
ruff check .
ruff format --check .
```

### Verify Environment & Setup
Run the setup verification script:
```bash
python scripts/verify_setup.py
```

---

## 5. Research Guidelines

This project strictly adheres to the research discipline and non-negotiable rules defined in `AGENTS.md`:
- **Research Integrity**: No fabricated results, benchmarks, or citations. Clear distinction between hypothesis, implementation, experiment, measured results, and limitations.
- **Telugu First**: Primary language scope is Native Telugu, Romanized Telugu, and Code-Mixed Telugu-English.
- **Separation of Concerns**: Data, tokenization, safety, retrieval, generation, claim extraction, verification, and evaluation remain modular and decoupled.
- **Reproducibility**: Experiments must be controlled, parameterized via configuration, and independently verifiable.
