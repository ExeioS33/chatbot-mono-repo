# This is a mono repo POC chatbot project

- Using Flask as a Backend
- Vue3 as a frontend
- Zero-shot-classification as a classifier model
- CamemBERT for question answering

## Key improvements

- Fine-tune model or replace existing one for better accuracy (lack accuracy actually), makes mistake
- Refacto project structure
- Add loging
- Use UV or Poetry for Python env and dependencies
- Dockerize Frontend part (which run locally for now)

## How to run

### Step 1

```bash
# change to root directory
cd chatbot-mono-repo
# start services (needs Makefile support)
# otherwise docker-compose build --no-cache
# docker-compose up -d
make compose
make up
```

### Start frontend in another shell

```bash
cd chatbot-mono-repo/chatbot-interface
npm run serve
```
