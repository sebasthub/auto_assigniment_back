from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
        DROP TABLE IF EXISTS "documentrecord";"""


MODELS_STATE = (
    "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"
)
