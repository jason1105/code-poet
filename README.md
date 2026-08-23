# 代码诗集 · Code Poet

> 每一次 git push，皆留一首诗。  
> *Every commit deserves a verse.*

A GitHub Pages project that uses Claude AI to write a poem inspired by your code changes on every `git push`. The poems accumulate into a beautiful, searchable collection page styled after ink-and-paper Chinese literary aesthetics.

---

## How It Works

1. You push code to `main`
2. GitHub Actions runs `write-poem.yml`
3. The workflow extracts the diff, commit message, and author
4. It sends a crafted prompt to Claude (Haiku model — fast and cheap)
5. Claude returns a structured JSON poem: type, title, body, programmer insight
6. The poem is prepended to `poems/collection.json` (capped at 50)
7. The bot commits and pushes the updated collection
8. GitHub Pages serves `index.html`, which fetches the collection and renders it

---

## Add Code Poet to ANY Repository

You can point this workflow at any repo — your own projects, your team's monorepo, an open-source library. The poems will still be published to **this** GitHub Pages repo.

### Step 1 — Fork or clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/code-poet.git
cd code-poet
```

Enable GitHub Pages on the repo: **Settings → Pages → Source: Deploy from branch → main → / (root)**.

### Step 2 — Add the OPENROUTER_API_KEY secret

In **this** `code-poet` repo:

```
Settings → Secrets and variables → Actions → New repository secret
Name:  OPENROUTER_API_KEY
Value: sk-ant-...
```

Get a key at [openrouter.ai/keys](https://openrouter.ai/keys).

### Step 3 — Trigger the workflow from another repo

In the **target repo** (the one whose commits you want to poeticize), add a workflow that calls a `repository_dispatch` event on the code-poet repo:

```yaml
# .github/workflows/trigger-poem.yml  (in YOUR project repo)
name: Trigger Code Poet

on:
  push:
    branches: [main]

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Dispatch to code-poet
        uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.POEM_REPO_TOKEN }}
          repository: YOUR_USERNAME/code-poet
          event-type: new-commit
          client-payload: |
            {
              "repo": "${{ github.repository }}",
              "sha":  "${{ github.sha }}",
              "ref":  "${{ github.ref }}"
            }
```

Then update `write-poem.yml` in this repo to also handle:

```yaml
on:
  push:
    branches: [main]
  repository_dispatch:
    types: [new-commit]
```

And in the Python step, check out the triggering repo:

```python
import os
payload = json.loads(os.environ.get("CLIENT_PAYLOAD", "{}"))
target_repo = payload.get("repo", "")  # e.g. "myorg/myproject"
target_sha  = payload.get("sha", "HEAD")
```

> For the simplest setup, just use code-poet **in the same repo** — paste the `write-poem.yml` workflow directly into your project and point GitHub Pages at that repo.

### Step 4 — Enable GitHub Pages

In this (`code-poet`) repo:
```
Settings → Pages
Source: Deploy from a branch
Branch: main  /  (root)
```

Your poetry collection will be live at:
```
https://YOUR_USERNAME.github.io/code-poet/
```

---

## Configuration

| Variable in workflow | Default | Purpose |
|---|---|---|
| `OPENROUTER_API_KEY` | *(required secret)* | Authenticate with OpenRouter |
| `OPENROUTER_MODEL` | *(optional variable)* | Any OpenRouter model ID; defaults to `deepseek/deepseek-chat` |
| Max poems | `50` | Rolling window kept in `collection.json` |
| Diff limit | `3000` chars | Keeps prompt tokens reasonable |

### Change the poem style

Edit the prompt inside `write-poem.yml`. For example, to always request a 七言绝句:

```python
prompt = f"""... 请严格创作七言绝句（四句，每句七字）..."""
```

Or to write in English:

```python
prompt = f"""You are a poet who finds beauty in code.
Write a short poem (haiku or free verse) inspired by this diff.
Return JSON: {{"type": "...", "title": "...", "poem": "...", "insight": "..."}}
Diff: {diff}"""
```

---

## Cost Estimate

Claude Haiku pricing (as of mid-2026):

| | Tokens | Cost |
|---|---|---|
| Input prompt | ~800 tokens | ~$0.0001 |
| Output poem | ~200 tokens | ~$0.00005 |
| **Per commit** | | **< $0.001** |

A busy team pushing 20 times/day spends less than **$0.60/month**.

---

## File Structure

```
code-poet/
├── .github/
│   └── workflows/
│       └── write-poem.yml   ← GitHub Actions workflow
├── poems/
│   └── collection.json      ← Append-only poem archive (auto-updated)
├── index.html               ← The poetry collection page
├── .nojekyll                ← Tells GitHub Pages not to use Jekyll
└── README.md                ← This file
```

---

## Philosophy

Code is already a kind of poetry: it has rhythm (indentation), metaphor (variable names), and narrative (commit history). This project makes that implicit poetry explicit — a record not just of *what* changed, but of the human experience of changing it.

The poems live alongside the code, a parallel timeline of feeling running next to the timeline of function.

---

*Built with Claude AI · GitHub Actions · GitHub Pages*
