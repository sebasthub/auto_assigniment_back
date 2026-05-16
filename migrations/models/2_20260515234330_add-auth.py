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
CREATE INDEX IF NOT EXISTS "idx_refreshtoke_token_f_c867a9" ON "refreshtoken" ("token_family");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "refreshtoken";
        DROP TABLE IF EXISTS "user";"""


MODELS_STATE = (
    "eJztml1v4jgUhv9KlKuOxI4KC51R72hLd9hpy4hmPjSrVWSSA3jr2Klt2qIu/31l5zskbM"
    "NCl1S5ajn2cewnjs/rYz+bHnOBiPd9IfCMekCleWo8mxR5YJ4aBaUtw0S+n5Qpg0QToquj"
    "bL2JkBw5qsUpIgJahumCcDj2JWbUPDXoghBlZI6QHNNZYlpQfL8AW7IZyDlw89T448+WYW"
    "LqwhOI6Kd/Z08xEDfTZeyqZ2u7LZe+tg2pvNQV1dMmtsPIwqNJZX8p54zGtXHQ/RlQ4EiC"
    "al7yheq+6l041mhEQU+TKkEXUz4uTNGCyNRwX8jAYVTxw1SqAT+bM/WUXzrt7ofux19Puh"
    "9bhql7Els+rILhJWMPHDWBG8tc6XIkUVBDY0y4SSwJrKM7nyNezC52yOETkufxRbA28YsM"
    "CcBk0uyIoIeebAJ0JucKW6+3gde3/vj8U3981On13qnRMI6cYI7fhEWdoExBTSAiR+KHAo"
    "pnjBFAtBhk4pQjOWGM7AtlPDu3QrmB3NlodKU67QlxT7RhaOUIfr0+G4yP2hqsuCdYQnqK"
    "JjRdIKBGXQ1nyusVeVZd4V4NqFoop+FCGa+cE+TcPSLu2pmS1GLAfOyIAvCh3+XnMRCkB7"
    "mOOQwalmrjMFeCkHZiDT8IDYt1WBmt9SKv4+UtiKKZ7rV6tnpSyOOr0IFsLbhq+8awuohq"
    "NAG1RgEVPIRJlYAaO+wmoO6d3/7D6RyJObi2j4R4ZNytArPAtdEpMVj9twLNqP5WCMN597"
    "YIYmFvJfYyfo3eyzB1OKhR20iuQ71AEiT2oJhq1jOH1Q1d30f/HOhnzwG5I0qWkRgpZ24N"
    "rwe3Vv/6Swb8Rd8aqJKOti5z1qOT3PSOGzG+D61Phvpp/BzdDDRBJuSM6ycm9ayfpuoTWk"
    "hmU/ZoIzcVVSJrBGY73clhykHMbcnugP5H/TkO2rJUU4f5xv8XGRrI8gIdGuv1ciGqtwWN"
    "Eq2bEr1fgIi+lSw9C55K8KV96iKcNq2Ygx9WZrGMgvvRdf/Hu8yCeTW6+S2qngpi51ejs1"
    "y84iB8RgVU4Zr2abgWc31ABKtY7drbEC72blgXs24ylk3G8oCBJidKdqXov+b370LgML7/"
    "XWiBNeldxHMd5iXjgGf0Myw10yEVElGn6DMvPBasj75uGSZHj7HAXJ8sjNrBN6mzIv3b8/"
    "7FwFyVb2D2qdcz25gC2Z7f5pSr93BzpfdWjYivm4j/S+IqGbuweh1TySfdF6TrTrql2TpV"
    "lI0iesrbKiVc6YA749WQTJhMkYfJsjrLxG9fcrxmODk8sLutMp5Zzx1kPF8/S1+TBGc07L"
    "UMZ/pFwpOPOYgtXmTWs56p67f0JptDiDd0CJFda32CHHDtydKuKKYKXGt5Err7AKauptho"
    "VrifLOeZ9aolyl678wKWvXanFKYuyx0q+2o+cxCiCs2sVy1p7mliVtprpjyaZFHMcAdpou"
    "iCW30TRKmpcUipoT5w7MwLL+wHJZsv6yd1mkRQjRJBD8BF4WFueYRIudTlHOw1Luv7fhWI"
    "YfV6AmwfH78AYPv4uBSgLsvd12JUFiq/329HNyV7pMQlv0HCjjT+NggWBxpsV+X81Hg3n8"
    "zmD2Fz2xvVgDqZrXBpaveBZfUPeNNUcw=="
)
