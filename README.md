# Autenticacao com Next.js BFF

Este backend FastAPI emite `access_token` e `refresh_token` em JSON. O browser
nao deve salvar tokens em `localStorage` nem `sessionStorage`.

Fluxo esperado:

1. O browser chama uma Route Handler do Next.js, por exemplo `POST /api/auth/login`.
2. O Next.js chama `POST ${API_URL}/auth/login` no FastAPI.
3. O FastAPI retorna `access_token` e `refresh_token`.
4. O Next.js salva os tokens em cookies HttpOnly.
5. O browser recebe apenas uma resposta como `{ "ok": true }`.
6. Rotas server-side do Next.js chamam o FastAPI usando `Authorization: Bearer <access_token>`.

O `access_token` e curto e deve ser usado apenas para autorizar chamadas ao
FastAPI. O `refresh_token` e mais longo, salvo como hash no banco, rotacionado
a cada uso e revogado no logout.

Endpoints de autenticacao:

- `POST /auth/register`: cria usuario e retorna `access_token` e `refresh_token`.
- `POST /auth/login`: autentica usuario e retorna `access_token` e `refresh_token`.
- `POST /auth/refresh`: rotaciona refresh token e retorna um novo par.
- `POST /auth/logout`: revoga o refresh token informado.
- `POST /auth/logout-all`: revoga todos os refresh tokens do usuario autenticado.
- `GET /auth/me`: retorna o usuario autenticado via `Authorization: Bearer`.

Variaveis de ambiente obrigatorias para autenticacao:

```env
SECRET_KEY=<gere-um-secret-forte>
REFRESH_SECRET_KEY=<gere-outro-secret-forte>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

Em producao, use secrets fortes e nao use `*` em `CORS_ALLOWED_ORIGINS`.

## Desenvolvimento

Rode a API observando apenas a pasta `app/`:

```bash
uv run uvicorn app.main:app --reload --reload-dir app
```

## Exemplo Next.js: login

```ts
import { cookies } from "next/headers"
import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  const body = await request.json()

  const response = await fetch(`${process.env.API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    return NextResponse.json(
      { message: "Credenciais invalidas" },
      { status: 401 },
    )
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

## Exemplo Next.js: rota autenticada

```ts
import { cookies } from "next/headers"
import { NextResponse } from "next/server"

export async function GET() {
  const cookieStore = await cookies()
  const accessToken = cookieStore.get("access_token")?.value

  if (!accessToken) {
    return NextResponse.json(
      { message: "Nao autenticado" },
      { status: 401 },
    )
  }

  const response = await fetch(`${process.env.API_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    return NextResponse.json(
      { message: "Sessao invalida" },
      { status: 401 },
    )
  }

  const data = await response.json()
  return NextResponse.json(data)
}
```
