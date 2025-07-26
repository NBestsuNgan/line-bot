# Linebot

A cross-platform bot framework for chat automation and agent deployment.

---

## Prerequisites
- Python 3.12
- [uv](https://github.com/astral-sh/uv) (dependency manager)
- Virtual environment (recommended)

---

## Setup (macOS/Linux)

```sh
# Activate virtual environment (if using venv)
source .venv/bin/activate

# Sync dependencies and update lock file
rm uv.lock
uv sync

# Export requirements.txt for deployment
uv export --no-hashes --no-header --no-dev --no-emit-project --no-annotate --frozen -o .requirements.txt
# Or, with annotation:
uv export --no-hashes --no-header --no-dev --no-emit-project --frozen -o .requirements.txt

# test ADK Agent
uv run adk web

# Deploy to agent engine
uv run app/agent_engine_app.py
```

---

## Setup (Windows)

```powershell
# Activate virtual environment (PowerShell)
.venv\Scripts\Activate.ps1

# Sync dependencies and update lock file
Remove-Item uv.lock
uv sync

# Export requirements.txt for deployment and deploy
uv export --no-hashes --no-header --no-dev --no-emit-project --no-annotate --frozen -o .requirements.txt
if (!(Test-Path .requirements.txt) -or ((Get-Content .requirements.txt).Length -eq 0)) {
    uv export --no-hashes --no-header --no-dev --no-emit-project --frozen -o .requirements.txt
}
uv run app/agent_engine_app.py
```

---

## Dependency & Deployment Flow

```
pyproject.toml
   │
   └──(uv sync)──▶ uv.lock
                        │
                        └──(uv export)──▶ requirements.txt
```


# Development 
```bash
cd bot-framework

# 1 
uvicorn app_local:app --reload

# 2 spin up another terminal 
ngrok http 8000
```


# Reference

1.Google SDK: google-adk, agent-starter-pack<br>
2.https://www.youtube.com/watch?v=9pZUrx6HSmU (superman)<br>
3.https://www.youtube.com/watch?v=P4VFL9nIaIA&t=8440s (aiwithbrandon)<br>