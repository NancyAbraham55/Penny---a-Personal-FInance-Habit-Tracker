# Penny 🌳

A gamified personal savings tracker built with Python and Streamlit. Log small financial wins, earn XP, and grow a named tree — with full multi-currency support calibrated by purchasing power parity.

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-app-red) 

---

## What it does

Most savings apps show you a number going up. Penny frames saving as a series of small, repeatable decisions — skipping a takeout order, logging an investment transfer, resisting an impulse buy — and rewards each one with XP that grows a named tree through seven visual stages, from Seed to Ancient Tree.

The tree mechanic is intentional: a portfolio bar going from 0% to 1% feels invisible. A tree growing from a sprout to a sapling feels like progress.

**Core mechanics:**
- Log quick actions (skip coffee, cook at home, add to investment) or define custom ones
- XP is awarded automatically based on PPP-adjusted USD equivalent — so SAR, AED, and INR users earn XP at a fair rate, not a converted one
- Trees grow through 10 levels across 7 named stages; fully grown trees join a visual forest grid
- Five ecosystems unlock as the forest expands (City Park → Tropical Rainforest → Mountain Forest → Desert Oasis → Island Mangrove)
- Savings timeline with daily, weekly, and monthly area/line charts
- Per-currency activity tracking — switching currencies shows a separate tree and history

---

## Why PPP matters

A $5 coffee in New York is not equivalent to SAR 19 in Riyadh in terms of local purchasing effort. Penny uses estimated PPP conversion rates so the XP threshold feels proportionate regardless of where you are:

| Currency | PPP units per USD equivalent |
|----------|------------------------------|
| USD | 1.0 |
| EUR | 0.9 |
| GBP | 0.8 |
| SAR | 2.7 |
| AED | 2.9 |
| INR | 23.0 |

Every 5 USD-equivalent saved earns 10 XP. The math adjusts per currency — no manual conversion needed.

---

## Tech stack

- **Python** — core logic, data aggregation, XP and level calculations
- **Streamlit** — UI, session state management, charting (area and line charts)
- **JSON** — lightweight local persistence
- **Custom CSS** — styled hero card, cover screen, and finance-note components

---

## Run locally

```bash
# 1. Clone the repo
git clone https://github.com/NancyAbraham55/penny.git
cd penny

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
streamlit run main.py
```

---

## App structure

```
penny/
├── main.py           # Full app: data model, XP logic, UI
├── penny_data.json   # Auto-generated on first run (gitignored)
├── requirements.txt
└── README.md
```

All logic lives in `main.py` — data loading, XP calculation, tree state derivation, aggregation, and rendering. No external database or API dependency.

---

## Roadmap

- [ ] Savings goal-setting with projected completion dates
- [ ] Streak tracking (consecutive days with at least one logged action)
- [ ] Export to CSV
- [ ] Hosted demo (Streamlit Community Cloud)

---

## Background

Built as part of a personal finance portfolio alongside [The Well-Balanced Sheet](https://nancyabrahamfor.substack.com) — a Substack on money, data, and financial systems.
