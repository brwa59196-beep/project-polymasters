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

From Windows Command Prompt, using your Windows user folder and the
`optionbot_codex` project name:

```bat
cd C:\Users\shtik
git clone https://github.com/shtik/optionbot_codex.git optionbot_codex
cd optionbot_codex
dir pyproject.toml
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e . pytest
pytest -q
```

If GitHub says `Repository not found`, open your repository page in the browser,
click **Code**, copy the HTTPS URL, and replace only this part:

```bat
git clone https://github.com/shtik/optionbot_codex.git optionbot_codex
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

## Publishing the code to GitHub

The code appears on GitHub only after it is pushed from a Git checkout that has
permission to write to the repository. If you are running commands on your own
Windows computer and are logged in to GitHub there, use:

```bat
cd C:\Users\shtik\optionbot_codex
git status
git add .
git commit -m "Add call-call arbitrage scanner"
git push origin main
```

If Git says there is nothing to commit, the files are already committed locally;
just run:

```bat
git push origin main
```

If Git asks for credentials, sign in with GitHub in your terminal or install
GitHub CLI and run `gh auth login`. Access granted in a browser or screenshot is
not automatically available to another machine or terminal session.

### Authorizing this Linux/Codex terminal

Browser access to GitHub is not enough for this terminal. To let this terminal
push code, create a GitHub token and cache it for Git commands in the current
repository checkout. Do not paste the token into chat messages; provide it only
as a terminal environment variable or secret.

1. Open the direct token page in your browser:
   `https://github.com/settings/personal-access-tokens/new`.
   If you prefer clicking through the UI: profile picture -> **Settings** -> scroll
   to the bottom of the left sidebar -> **Developer settings** -> **Personal
   access tokens** -> **Fine-grained tokens** -> **Generate new token**.
2. Fill the token form:
   - **Token name**: `codex-project-polymasters`.
   - **Expiration**: choose a short expiration while testing, for example 7 or
     30 days.
   - **Resource owner**: `brwa59196-beep`.
   - **Repository access**: **Only select repositories**.
   - **Selected repositories**: `project-polymasters`.
   - **Repository permissions** -> **Contents**: **Read and write**.
3. Click **Generate token** and copy the token once. GitHub will not show it
   again.
4. Send the token to Codex as an environment secret named `GITHUB_TOKEN`, or
   paste it into the Codex terminal only if your interface exposes a secure
   terminal input. Here, "this terminal" means the remote Linux shell where Codex
   runs commands for the task, not Windows Command Prompt and not GitHub's web
   page. In this workspace the repository path is `/workspace/project-polymasters`.

Once `GITHUB_TOKEN` exists in the Codex terminal environment, Codex can run:

```bash
cd /workspace/project-polymasters
scripts/configure_github_auth.sh
git ls-remote --heads origin
git push origin HEAD:codex/write-code-for-call-option-arbitrage
```

The helper configures `origin`, caches the token for Git's credential helper, and
prints the exact push command for the current Codex branch. If there is no way to
provide a secret to the Codex terminal, then this environment cannot push
directly; the fallback is to run the Windows helper from your local clone.

### One-command publish helper for Windows

After the repository exists on your computer, you should not copy every new file
by hand. Run the included helper script from the repository root; it stages all
changed files, creates a commit when needed, and pushes to GitHub:

```bat
cd C:\Users\shtik\optionbot_codex
scripts\publish_to_github.bat main
```

The script still needs GitHub authentication once. If the push asks for login or
fails with a credentials error, install GitHub CLI, run `gh auth login`, and then
run the script again.

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
