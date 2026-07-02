# Incident Extraction API

API em Python que recebe descrições livres de incidentes e usa um LLM local
(via [Ollama](https://ollama.com)) para extrair informações estruturadas em JSON:

```json
{
  "data_ocorrencia": "2026-07-01 14:00",
  "local": "São Paulo",
  "tipo_incidente": "Falha no servidor",
  "impacto": "Sistema de faturamento indisponível por 2 horas"
}
```

O enunciado completo do desafio está em [docs/case.md](docs/case.md).

## Como executar

### Opção A — Docker Compose (recomendado)

Requisito: Docker.

```bash
docker compose up --build
```

Sobe o Ollama, baixa o modelo (`llama3.2:3b`, ~2 GB, apenas na primeira vez)
e inicia a API em `http://localhost:8000`.

### Opção B — Local

Requisitos: [uv](https://docs.astral.sh/uv/) e [Ollama](https://ollama.com/download).

```bash
# 1. Ollama + modelo
ollama serve &
ollama pull llama3.2:3b

# 2. Dependências e API
make install
make run   # http://localhost:8000
```

## Uso

Documentação interativa em `http://localhost:8000/docs`.

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"texto": "Ontem às 14h, no escritório de São Paulo, houve uma falha no servidor principal que afetou o sistema de faturamento por 2 horas."}'
```

Campos ausentes no texto voltam como `null`. Se o Ollama estiver fora do ar,
a API responde `503`.

| Variável de ambiente | Padrão                   | Descrição            |
| -------------------- | ------------------------ | -------------------- |
| `OLLAMA_URL`         | `http://localhost:11434` | Endereço do Ollama   |
| `OLLAMA_MODEL`       | `llama3.2:3b`            | Modelo usado         |

## Testes e qualidade

```bash
make test       # testes unitários (LLM mockado, rodam offline)
make test-e2e   # end-to-end contra a API + Ollama reais (suba-os antes)
make lint       # ruff check + format check
```

O CI (GitHub Actions) roda lint e testes unitários a cada push.

## Decisões de projeto

- **Structured outputs**: o JSON Schema do contrato (`IncidentInfo`) é enviado
  no campo `format` do Ollama, que restringe a decodificação do modelo ao
  schema — chaves erradas ou JSON inválido tornam-se impossíveis, mesmo com
  modelos pequenos.
- **`temperature: 0`**: extração pede reprodutibilidade, não criatividade.
- **Data de referência no prompt**: a data atual é injetada para resolver
  expressões relativas ("ontem às 14h" → data absoluta).
- **Degradação graciosa**: saída inparseável ou sentinelas como `"null"`/`"N/A"`
  viram `null` no campo correspondente — o contrato da API não depende da
  qualidade do modelo.
- **Pré-processamento**: pipeline de funções puras (controle de caracteres,
  normalização Unicode, colapso de espaços) aplicado antes do prompt.
- **LLM plugável**: o app depende de um `Protocol` (`LLMClient`); o backend
  concreto (Ollama) pode ser trocado ou mockado nos testes sem tocar o resto
  do código.
