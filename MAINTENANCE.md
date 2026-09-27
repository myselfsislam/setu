# Setu upkeep calendar

| When | What to update | Where |
|---|---|---|
| 12 Oct 2026 | India CPI inflation (September figure) | `index.html` → `RATES`, `KEYCHANGES` |
| 5 Nov 2026 | Bank of England Bank Rate decision | `index.html` → `RATES`, `KEYCHANGES` |
| Every RBI policy meeting | RBI repo rate | `index.html` → `RATES`, `KEYCHANGES` |
| Monthly (mid-month) | UK CPI inflation | `index.html` → `RATES` |
| 6 April each year | UK tax bands, NI, ISA limits (cash ISA falls to £12,000 for under-65s from 6 Apr 2027) | `index.html` → `takeHome`, checklist text; `scripts/build_guides.py`; then `python scripts/build_guides.py` |
| 1 April each year | Indian tax rules for NRIs | checklist text, NRI guides |
| Weekly glance | News job ran (Actions → Refresh news shows green) | GitHub Actions |
| Before every release | Run `python tests/run_all.py` (all checks must pass) | `tests/` |

After any change to `index.html`, bump `VERSION` in `sw.js` so installed apps pick up the new version.
