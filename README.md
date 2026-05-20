# Auto Assignment — Backend

API REST em **FastAPI** para gerenciar trabalhos acadêmicos (assignments), tópicos, usuários e edição de documentos **DOCX** via **OnlyOffice**. Pensada para ser consumida por um frontend **Next.js** que atua como BFF: tokens JWT ficam em cookies HttpOnly no Next.js, não no browser.

## Visão geral

| Área | Descrição |
|------|-----------|
| **Auth** | Registro, login, refresh rotacionado, logout e perfil (`/auth/*`). Refresh tokens são hasheados no banco. |
| **Assignments** | CRUD de trabalhos por usuário autenticado, com tópicos aninhados e vínculo opcional a um documento. |
| **Topics** | CRUD de tópicos dentro de um assignment (soft delete). |
| **Documents** | Upload de `.docx` por assignment, listagem, download e configuração do editor OnlyOffice. |
| **OnlyOffice** | Callback do Document Server para persistir alterações após edição. |

**Stack:** Python 3.14+, FastAPI, Tortoise ORM, SQLite (`db.sqlite3`), Aerich (migrations), Pydantic Settings, JWT (PyJWT), armazenamento local ou S3/MinIO (boto3).

```
app/
├── config/       # settings, JWT, Tortoise
├── models/       # User, Assignment, Topic, DocumentRecord, RefreshToken
├── routes/       # auth, assignment, topic, document, onlyoffice
├── services/     # auth, documents, storage
└── main.py
```

## Início rápido

```bash
cp .env.example .env
# Preencha SECRET_KEY e REFRESH_SECRET_KEY (veja tabela abaixo)

uv sync
uv run aerich upgrade
uv run uvicorn app.main:app --reload --reload-dir app
```

Documentação interativa: [http://localhost:8000/docs](http://localhost:8000/docs)

## Variáveis de ambiente

Copie `.env.example` para `.env`. Todas as chaves são lidas por `app/config/settings.py` (Pydantic Settings, arquivo `.env`, case-insensitive).

### Aplicação

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `ENVIRONMENT` | `development` | `development` ou `production`. Em `production`, cookies de auth usam `Secure` e wildcard em CORS é rejeitado. |

### Autenticação (JWT)

Obrigatórias para endpoints `/auth/*` (exceto que dependam de secrets na emissão/validação).

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SECRET_KEY` | — | Chave para assinar o access token. Gere com `openssl rand -hex 32`. |
| `REFRESH_SECRET_KEY` | — | Chave separada para o refresh token. |
| `JWT_ALGORITHM` | `HS256` | Algoritmo JWT. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Validade do access token. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Validade do refresh token. |

### CORS e frontend

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `FRONTEND_URL` | `http://localhost:3000` | Origem do frontend; sempre incluída em CORS. |
| `CORS_ALLOWED_ORIGINS` | *(vazio)* | Origens extras, separadas por vírgula. Em produção, não use `*`. |

### OnlyOffice e URLs do backend

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `ONLYOFFICE_URL` | `http://localhost:8080` | URL do OnlyOffice Document Server. |
| `BROWSER_BACKEND_URL` | `http://localhost:8000` | URL que o **browser** usa (download, links na UI). |
| `PUBLIC_BACKEND_URL` | `http://host.docker.internal:8000` | URL que o **OnlyOffice no Docker** usa para callback e download (precisa alcançar a API no host). |

### Armazenamento de documentos

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `STORAGE_BACKEND` | `local` | `local`, `s3` ou `minio`. |
| `STORAGE_LOCAL_DIR` | `storage/documents` | Diretório quando `STORAGE_BACKEND=local`. |
| `STORAGE_BUCKET` | — | Obrigatório para `s3` / `minio`. |
| `STORAGE_REGION` | — | Região AWS (ex.: `us-east-1`). |
| `STORAGE_ACCESS_KEY_ID` | — | Credencial S3/MinIO. |
| `STORAGE_SECRET_ACCESS_KEY` | — | Credencial S3/MinIO. |
| `STORAGE_ENDPOINT_URL` | — | Obrigatório para **MinIO** (ex.: `http://localhost:9000`). Para AWS S3, deixe vazio para o endpoint padrão da região. |
| `STORAGE_ADDRESSING_STYLE` | `path` | `path` ou `virtual` (MinIO costuma usar `path`). |

O banco de dados está configurado em código (`sqlite://db.sqlite3` em `app/config/tortoise.py`), sem variável de ambiente.

## API

### Auth

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/auth/register` | Cria usuário; retorna par de tokens. |
| `POST` | `/auth/login` | Login; retorna `access_token` e `refresh_token`. |
| `POST` | `/auth/refresh` | Rotaciona refresh token; retorna novo par. |
| `POST` | `/auth/logout` | Revoga o refresh token enviado. |
| `POST` | `/auth/logout-all` | Revoga todos os refresh tokens do usuário (Bearer). |
| `GET` | `/auth/me` | Usuário autenticado (Bearer). |

### Assignments e topics

Requerem `Authorization: Bearer <access_token>`.

- **Assignments:** `GET/POST /assignments`, `GET/PUT/DELETE /assignments/{id}`
- **Topics:** `GET/POST /topics`, `GET/PUT/DELETE /topics/{id}` (filtro por `assignment_id` na listagem)

### Documents e OnlyOffice

- `GET /documents` — lista documentos
- `POST /assignments/{assignment_id}/document` — upload `.docx`
- `GET /documents/{document_id}/config` — config do editor OnlyOffice
- `GET /documents/{document_id}/download` — download do arquivo
- `POST /onlyoffice/callback/{document_id}` — callback do Document Server

## Integração com Next.js (BFF)

O backend devolve tokens em JSON. O browser **não** deve guardá-los em `localStorage` nem `sessionStorage`.

1. O browser chama uma Route Handler do Next.js (ex.: `POST /api/auth/login`).
2. O Next.js chama `POST ${API_URL}/auth/login` nesta API.
3. O Next.js grava `access_token` e `refresh_token` em cookies **HttpOnly**.
4. O browser recebe algo como `{ "ok": true }`.
5. Rotas server-side do Next.js chamam esta API com `Authorization: Bearer <access_token>`.

O access token é curto e autoriza chamadas ao FastAPI. O refresh token é mais longo, hasheado no banco, rotacionado a cada uso e revogado no logout.

### Exemplo: login

```ts
import { cookies } from "next/headers"
import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  const body = await request.json()

  const response = await fetch(`${process.env.API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    return NextResponse.json({ message: "Credenciais inválidas" }, { status: 401 })
  }

  const data = await response.json()
  const cookieStore = await cookies()

  cookieStore.set("access_token", data.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 15,
  })

  cookieStore.set("refresh_token", data.refresh_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/api/auth/refresh",
    maxAge: 60 * 60 * 24 * 7,
  })

  return NextResponse.json({ ok: true })
}
```

### Exemplo: rota autenticada

```ts
import { cookies } from "next/headers"
import { NextResponse } from "next/server"

export async function GET() {
  const accessToken = (await cookies()).get("access_token")?.value

  if (!accessToken) {
    return NextResponse.json({ message: "Não autenticado" }, { status: 401 })
  }

  const response = await fetch(`${process.env.API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })

  if (!response.ok) {
    return NextResponse.json({ message: "Sessão inválida" }, { status: 401 })
  }

  return NextResponse.json(await response.json())
}
```

## Desenvolvimento

```bash
# Servidor com reload apenas em app/
uv run uvicorn app.main:app --reload --reload-dir app

# Testes
uv run pytest

# Migrations (após alterar models)
uv run aerich migrate --name "descricao"
uv run aerich upgrade
```

Em produção, use secrets fortes para `SECRET_KEY` e `REFRESH_SECRET_KEY` e restrinja `CORS_ALLOWED_ORIGINS` às origens reais do frontend.
