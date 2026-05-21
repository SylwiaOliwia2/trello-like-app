### Pre-commit hook (auto-format)
One-time setup:
- `python3 -m pip install --user pre-commit`
- if `pre-commit` command is not found, add local Python bin to PATH:
  - `export PATH="$HOME/.local/bin:$PATH"`
- `pre-commit install`

On every `git commit` auto-formats Python (ruff) + JS/Vue/JSON/MD (prettier).
Run on all files manually: `pre-commit run --all-files`.
