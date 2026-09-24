# SAMUDRA
**S**ynthetic **A**perture **M**onitoring for **U**nified **D**etection and **R**apid **A**ssessment

> SIH 2026 — Maritime oil-spill forensics platform.

| Engine | Module | Role |
|--------|--------|------|
| E1 | `app/engines/engine1/detection.py` | SAR slick polygon extraction |
| E2 | `app/engines/engine2/hindcast.py` | Lagrangian backward drift |
| E3 | `app/engines/engine3/attribution.py` | AIS forensics + dark vessel radar fusion |

## Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Prototype (standalone, no server)
```bash
python backend/prototypes/engine3_prototype.py
```
