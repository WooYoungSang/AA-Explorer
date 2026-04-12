---
name: bootstrap
description: "Initialize the AA Explorer project, install dependencies, and verify the setup"
allowed-tools: Read Grep Glob Bash
---

# Skill: Bootstrap — AA Explorer

> **Trigger**: "bootstrap", "setup", "init", "environment setup"
> **Scope**: project initialization + dependency installation + verification
> **Time**: ~10 minutes

## Procedure

### Phase 1: Check the environment
```bash
node --version    # >= 18 required
python --version  # >= 3.11 required
which poetry && poetry --version
which pnpm && pnpm --version
```

### Phase 2: Create the directory layout
```bash
mkdir -p aa-explorer/{backend/{app/{routers,services,models},tests,migrations},frontend,docs/bets,.claude/{skills,agents},.codex/agents}
cd aa-explorer
git init
```

### Phase 3: Install the backend
```bash
cd backend
poetry env use python3.11
poetry install --with dev
poetry run python -c "import fastapi; import web3; print('✅ Backend deps OK')"
```

### Phase 4: Install the frontend
```bash
cd ../frontend
npx create-next-app@14 . --typescript --tailwind --eslint --app --src-dir --no-import-alias
npm install recharts swr clsx
npx next build 2>&1 | tail -3
```

### Phase 5: Create skeleton tests
```bash
cd ../backend
poetry run pytest -q
```

### Phase 6: Place the agent harness
```bash
cd ..
# Copy files into .claude/skills/
# Copy files into .claude/agents/
# Copy files into .codex/agents/
```
