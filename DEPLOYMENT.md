# Deploy

Esta aplicação possui dois serviços independentes:

1. **AgentOS**: executa o agente, ferramentas, memória e banco de dados.
2. **Streamlit**: exibe a interface e chama a URL pública do AgentOS.

Não use `127.0.0.1` em produção: no Streamlit Cloud ele aponta para o próprio contêiner do Streamlit, não para o AgentOS.

## Backend AgentOS

Publique o backend em um serviço que execute processos Python (por exemplo, Render, Railway ou Fly.io), com o comando:

```bash
uv run python agent.py
```

Defina nele `OPENAI_API_KEY`, `TAVILY_API_KEY` e `DATABASE_URL`. O `DATABASE_URL` deve apontar para um PostgreSQL gerenciado; SQLite só é usado localmente e seu arquivo não é persistente em hospedagens efêmeras.

## Streamlit Cloud

Publique este repositório no GitHub e configure o Streamlit Cloud para executar `deploy.py`. Nos Secrets do Streamlit, defina:

```toml
AGENT_OS_URL = "https://url-publica-do-agentos"
```

O Streamlit mantém um `user_id` anônimo e um `session_id` nos parâmetros da URL. Isso permite listar, reabrir e manter o contexto das conversas do mesmo navegador. Para identidade segura entre dispositivos, acrescente autenticação antes de usar em produção com usuários reais.
