# Contributing to AE Sentinel

Thank you for your interest in contributing! 🎉

> **Note:** Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before participating. All contributors are expected to adhere to it.

## How to Contribute

### 🐛 Bug Reports
1. Search [existing issues](https://github.com/mgj10086/AEPD-Sentinel/issues) first
2. Use the **Bug Report** template
3. Include: environment (OS, Python version), steps to reproduce, expected vs actual behavior

### 💡 Feature Requests
1. Check if it aligns with the project's clinical trial safety focus
2. Use the **Feature Request** template
3. Describe the use case and expected outcome

### 🔧 Pull Requests
1. Fork the repo and create a feature branch: `git checkout -b feat/your-feature`
2. Keep changes focused — one feature/fix per PR
3. Follow existing code style (see [CLAUDE.md](CLAUDE.md) conventions)
4. Run `python test_e2e.py` before submitting
5. Update documentation if needed

### 🏗️ Development Setup
```bash
# Backend
pip install -r requirements.txt
python run.py

# Frontend
cd frontend && npm install && npm run dev

# Docker
docker-compose up -d
```

## Priority Areas

| Area | Difficulty | Impact |
|------|-----------|--------|
| LLM Integration (Zhipu/Qwen) | Medium | High |
| i18n / English translation | Easy | High |
| Real Fisher's exact test | Medium | Medium |
| MedDRA dictionary upgrade | Hard | High |
| Unit tests coverage | Easy | Medium |

## Code Conventions
- Python: `backend.xxx` absolute imports (never `from core.xxx`)
- Frontend: Vue3 Composition API + `<script setup>`
- SQL: Use MySQL syntax (auto-converted for SQLite)
- API response: `{"code": 200, "message": "success", "data": {...}}`

## Questions?
Open a [Discussion](https://github.com/mgj10086/AEPD-Sentinel/discussions) or check the [project documentation](项目文件/).
