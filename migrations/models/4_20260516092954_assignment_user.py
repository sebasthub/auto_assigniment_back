from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "assignment" ADD "user_id" INT REFERENCES "user" ("id") ON DELETE CASCADE;
        UPDATE "assignment"
        SET "user_id" = (SELECT "id" FROM "user" ORDER BY "id" LIMIT 1)
        WHERE "user_id" IS NULL
          AND EXISTS (SELECT 1 FROM "user");
        CREATE INDEX IF NOT EXISTS "idx_assignment_user_id_5d51b3" ON "assignment" ("user_id");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_assignment_user_id_5d51b3";
    """


MODELS_STATE = (
    "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"
    "2yL+e/ofa89aZg=="
)
