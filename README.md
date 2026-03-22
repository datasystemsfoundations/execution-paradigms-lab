# Query Execution Models: Iterator vs Vectorized vs JIT

Hands-on lab exploring the three fundamental query execution models used by modern databases. Builds working implementations of each model, benchmarks them head-to-head, and shows why vectorized execution (DuckDB, Snowflake) and JIT compilation (Spark Tungsten, HyPer) dramatically outperform the classical iterator model (PostgreSQL, SQLite) on analytical workloads.

## Files

| File | Purpose |
|------|---------|
| `setup.sh` | Installs all dependencies (one-time) |
| `lab_query_exec.ipynb` | The lab notebook — run this |
| `query_viz.py` | Graphviz visualizer for execution models, operator trees, CPU cache behavior |
| `.gitignore` | Keeps generated files out of the repo |

All generated artifacts (images) are written to `_output/` at runtime.

## Setup

```bash
# 1. Install dependencies
bash setup.sh

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Open the lab
jupyter notebook lab_query_exec.ipynb
```

## Prerequisites

- Python 3.10+
- macOS or Linux
