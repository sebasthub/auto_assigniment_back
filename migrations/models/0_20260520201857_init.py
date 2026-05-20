from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "user" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "hashed_password" VARCHAR(255) NOT NULL,
    "name" VARCHAR(255),
    "is_active" INT NOT NULL DEFAULT 1,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_user_email_1b4f1c" ON "user" ("email");
CREATE TABLE IF NOT EXISTS "assignment" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "active" INT NOT NULL DEFAULT 1,
    "deleted" INT NOT NULL DEFAULT 0,
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "topic" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "question" TEXT NOT NULL,
    "response" TEXT,
    "validated_response" TEXT,
    "active" INT NOT NULL DEFAULT 1,
    "deleted" INT NOT NULL DEFAULT 0,
    "assignment_id" INT NOT NULL REFERENCES "assignment" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "refreshtoken" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "jti" VARCHAR(64) NOT NULL UNIQUE,
    "token_hash" VARCHAR(64) NOT NULL UNIQUE,
    "token_family" VARCHAR(64) NOT NULL,
    "revoked_at" TIMESTAMP,
    "expires_at" TIMESTAMP NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "replaced_by_jti" VARCHAR(64),
    "user_agent" VARCHAR(512),
    "ip_address" VARCHAR(64),
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_refreshtoke_jti_708583" ON "refreshtoken" ("jti");
CREATE INDEX IF NOT EXISTS "idx_refreshtoke_token_h_a8871a" ON "refreshtoken" ("token_hash");
CREATE INDEX IF NOT EXISTS "idx_refreshtoke_token_f_c867a9" ON "refreshtoken" ("token_family");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "documentrecord" (
    "uuid" CHAR(36) NOT NULL PRIMARY KEY,
    "original_name" VARCHAR(255) NOT NULL,
    "filename" VARCHAR(255) NOT NULL,
    "key" VARCHAR(255) NOT NULL UNIQUE,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "deleted" INT NOT NULL DEFAULT 0,
    "assignment_id" INT NOT NULL UNIQUE REFERENCES "assignment" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_documentrec_key_7b296f" ON "documentrecord" ("key");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "P22H+O/xf0GcWdA="
)
