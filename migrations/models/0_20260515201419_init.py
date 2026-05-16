from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "assignment" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "active" INT NOT NULL DEFAULT 1,
    "deleted" INT NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "topic" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "question" TEXT NOT NULL,
    "response" TEXT NOT NULL,
    "validated_response" TEXT NOT NULL,
    "assignment_id" INT NOT NULL REFERENCES "assignment" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmG1v2jAQgP9KlE+dxCZgZa34Fli7dW1BomyqNE2RSY5g1bGDbVpQx3+f7LwnhpWqrY"
    "rER+7Fvntw7s5+tEPmAxGfHCFwQEOg0u5ajzZFIdhdy6BtWDaKolynBBJNiDZHZbuJkBx5"
    "asUpIgIalu2D8DiOJGbU7lp0QYgSMk9IjmmQixYUzxfgShaAnAG3u9bvPw3LxtSHJYj0Z3"
    "TnTjEQvxQy9tXeWu7KVaRlF1Sea0O128T1GFmENDeOVnLGaGaN4/ADoMCRBLW85AsVvoou"
    "yTXNKI40N4lDLPj4MEULIgvpPpGBx6jih6lUCT/agdrlY7t1fHJ8+vnL8WnDsnUkmeRkHa"
    "eX5x47agKDsb3WeiRRbKEx5twklgTq6PozxM3sMocKPiF5FV8Kaxu/VJADzA/NCxEM0dIl"
    "QAM5U9g6nS28fjmj/ndndNTudD6obBhHXnzGB4mqHesU1Bwi8iS+N1DsMUYAUTPI3KlCcs"
    "IYeS2U2el8Fsot5HrD4ZUKOhRiTrTgYlwh+PO6dzY6ammwYk6whOIRzWn6QEBlvRvOgtcb"
    "8ty1wr0ZUFUop0mhzCrnBHl3D4j7bklTKAYswp4wgE/8zi9HQJBOso45aRpjtcb7rAQJ7V"
    "yafBAaFmuzTbTqqrAdViWIokBHrfZWO5V4GLprBmpzY9X/x6Gn7ltPnS9ApB9Jmd4Ylhvw"
    "FX32pbNugTQ+ux2XqlfaP4+unVtdsMJVorkaDr6l5oXi1r8a9iqNgYOIGBWwC9eiz4Grme"
    "s9IthXBNznEDZ7H1ibWed3JXen8lrz+3+lfR+AX6LY1oYZE886zHPGAQf0Elaa6QUVElHP"
    "dDyNF979GWAals3RQ9bB64eFUTeej/XdzrnpO1/P7PXmkfA1ByIHOPZmxveGWLP9rSG3Oc"
    "xEezQT3QMXxpFo80tDwWVfuslbvDVE0S4QE/P9BNhqNp8AsNVsbgSodWWAHqPS2C5+3AwH"
    "ZogFlwpIH3vS+msRLN53y5ga+Kl8t8831VFG5c+EDLheRS+g5psd3hpevrGs/wEDjk8y"
)
