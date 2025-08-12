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
# Sync dependencies and update lock file
rm uv.lock # if already have or want to make change

uv sync

# Export requirements.txt for deployment
uv export --no-hashes --no-header --no-dev --no-emit-project --no-annotate --frozen -o .requirements.txt
```

---

## Setup (Windows)

```powershell
# Sync dependencies and update lock file
Remove-Item uv.lock # if already have or want to make change

uv sync

# Export requirements.txt for deployment and deploy
uv export --no-hashes --no-header --no-dev --no-emit-project --no-annotate --frozen -o .requirements.txt
if (!(Test-Path .requirements.txt) -or ((Get-Content .requirements.txt).Length -eq 0)) {
    uv export --no-hashes --no-header --no-dev --no-emit-project --frozen -o .requirements.txt
}
```

---

## Dependency & Deployment Flow

```
pyproject.toml
   │
   └──(uv sync)──▶ uv.lock
                        │
                        └──(uv export)──▶ requirements.txt
                                                        │
                                                        └──(uv run app/agent_engine_app.py)──▶ deploy agent engine
```


# Development 
```bash
cd deployment/terraform/cloud_run_function_chat

# 1 
uvicorn app_local:app --reload

# 2 spin up another terminal 
ngrok http 8000
```


# test ADK Agent
```bash
uv run adk web --reload_agents
```

# Deploy to agent engine
```bash
uv run app/agent_engine_app.py
```

# Reference
1.Google SDK: google-adk, agent-starter-pack<br>
2.https://www.youtube.com/watch?v=9pZUrx6HSmU (superman)<br>
3.https://www.youtube.com/watch?v=P4VFL9nIaIA&t=8440s (aiwithbrandon)<br>