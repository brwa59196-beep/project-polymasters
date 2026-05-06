# Project Polymasters

Utilities for detecting option arbitrage opportunities.


## Local setup

Create a virtual environment and install the package in editable mode before
running tests. First change into the project folder that contains `pyproject.toml`;
otherwise `python -m pip install -e . pytest` will fail with "neither setup.py nor
pyproject.toml found". Use the activation command for your shell:

### Windows Command Prompt

```bat
cd C:\path\to\project-polymasters
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e . pytest
pytest -q
```

### Windows PowerShell

```powershell
cd C:\path\to\project-polymasters
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . pytest
pytest -q
```

If PowerShell blocks activation scripts, run this once for the current user and
then activate the environment again:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### macOS / Linux / Git Bash

```bash
cd /path/to/project-polymasters
python -m venv .venv
source .venv/bin/activate
python -m pip install -e . pytest
pytest -q
```

## Working from your GitHub repository

If the repository is on GitHub and you are working from your own computer, clone
the repository first, then run all Python commands inside the cloned folder. Do
not run `pip install -e .` from `C:\Users\shtik` unless that folder itself
contains `pyproject.toml`.

From Windows Command Prompt:

```bat
cd C:\Users\shtik
git clone https://github.com/YOUR_USER/YOUR_REPO.git optionbot_codex
cd optionbot_codex
dir pyproject.toml
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e . pytest
pytest -q
```

If you already cloned the repository to `C:\Users\shtik\optionbot_codex`, skip
`git clone` and just run:

```bat
cd C:\Users\shtik\optionbot_codex
dir pyproject.toml
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e . pytest
pytest -q
```

If you downloaded a patch from GitHub instead of cloning the branch, apply the
patch inside the cloned repository folder with `git apply name-of-patch.txt`
before installing and testing.

## If you downloaded a `.txt` patch

A patch text file is not directly runnable. You must apply it to a Git checkout
so the project folder contains files such as `pyproject.toml`, `src/`, `tests/`,
and `scripts/`. If your patch file is in `C:\Users\shtik\optionbot_codex`, run
these commands from Windows Command Prompt after replacing the patch file name:

```bat
cd C:\Users\shtik\optionbot_codex
git status
git apply name-of-patch.txt
dir pyproject.toml
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e . pytest
pytest -q
```

If `git apply name-of-patch.txt` says the patch does not apply, you probably only
have the patch file and not the repository checkout, or the patch was downloaded
with extra text around the diff. In that case, clone or download the repository
first, then apply the patch inside that repository folder.

## Call-call arbitrage scanner

The `polymasters.call_call_arbitrage` module checks European call quotes for
same-underlying and same-expiry no-arbitrage relationships:

- call prices must be non-increasing as strike increases;
- vertical call spread value must not exceed the discounted strike difference;
- call prices must be convex across strikes.

```python
from polymasters.call_call_arbitrage import CallQuote, find_call_call_arbitrage

quotes = [
    CallQuote(strike=90, price=14.0),
    CallQuote(strike=100, price=15.5),
]

opportunities = find_call_call_arbitrage(quotes, discount_factor=1.0)
for opportunity in opportunities:
    print(opportunity.kind, opportunity.net_credit)
```

## Latency expectations

Python is acceptable for research, monitoring, and slower retail/API execution,
but it is not a guarantee for a "risk-free" exchange arbitrage bot. The current
scanner uses O(n log n) work including sorting and O(n) checks after the quotes
are ordered, so scanning a single option chain can fit into millisecond budgets
on normal hardware. End-to-end trading latency is different: market data parsing,
network hops, broker/exchange throttles, order placement, fills, cancels, and
risk checks often dominate the local calculation time.

For production arbitrage:

- keep Python as the strategy/orchestration layer only;
- move the hot execution path to Rust, C++, Java, Go, or colocated exchange SDKs
  if sub-millisecond or deterministic latency is required;
- benchmark on the same machine, feed, broker, and order route you will trade;
- never treat a screen-detected arbitrage as risk-free until fill risk, stale
  quotes, transaction costs, margin, and exchange rejection paths are modeled.

You can measure local scan time with:

```bash
python scripts/benchmark_call_call.py --quotes 500 --iterations 1000
```
