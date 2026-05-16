from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "topic" ADD "active" INT NOT NULL DEFAULT 1;
        ALTER TABLE "topic" ADD "deleted" INT NOT NULL DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "topic" DROP COLUMN "active";
        ALTER TABLE "topic" DROP COLUMN "deleted";"""


MODELS_STATE = (
    "eJztmG1v2jAQgP9KlE+dxCZgZa34Fli7dW1BomyqNE2RSY5g1bGDbdqijv8+2XlPDCtVW4"
    "HER+7Fvnuw7y5+skPmAxGfHCFwQEOg0u5aTzZFIdhdy6BtWDaKolynBBJNiDZHZbuJkBx5"
    "asUpIgIalu2D8DiOJGbU7lp0QYgSMk9IjmmQixYUzxfgShaAnAG3u9bvPw3LxtSHRxDpz+"
    "jOnWIgfilk7Ku9tdyVy0jLLqg814Zqt4nrMbIIaW4cLeWM0cwax+EHQIEjCWp5yRcqfBVd"
    "kmuaURxpbhKHWPDxYYoWRBbSfSYDj1HFD1OpEn6yA7XLx3br+OT49POX49OGZetIMsnJKk"
    "4vzz121AQGY3ul9Uii2EJjzLlJLAnU0fVniJvZZQ4VfELyKr4U1iZ+qSAHmB+aVyIYokeX"
    "AA3kTGHrdDbw+uWM+t+d0VG70/mgsmEcefEZHySqdqxTUHOIyJP43kCxxxgBRM0gc6cKyQ"
    "lj5K1QZqfzRSg3kOsNh1cq6FCIOdGCi3GF4M/r3tnoqKXBijnBEopHNKfpAwGV9XY4C17v"
    "yHPbCvduQFWhnCaFMqucE+TdPSDuuyVNoRiwCHvCAD7xO78cAUE6yTrmpGmM1Rq7WQkS2r"
    "k0uRAaFmuzdbTqqrAdViWIokBHrfZWO5V4GLprBmp9Y9X/x6Gn7ltPnS9ApJekTG8Mj2vw"
    "FX32pbNugDQ+ux2XqlfaP4+unVtdsMJlorkaDr6l5oXi1r8a9iqNgYOIGBWwDdeiz4Grme"
    "s9IthXBNyXEDZ7H1ibWR9GxcOouMNA8095d6vuX/P7/yCwG/f/NWaB2qxt4lmHec444IBe"
    "wlIzvaBCIuqZrrnxPWZ/5uuGZXP0kA2Y9cPCqBvfSf304Nz0na9n9mr9F8tbzusOcOzNjM"
    "9hsWbzU1hucxjZ92hkvwcujBP7+oewgsu+DDvv8RQWRdtATMz3E2Cr2XwGwFazuRag1pUB"
    "eoxKY7v4cTMcmCEWXCogfexJ669FsNjtljE18FP5bh6/q5O2yp8JGXC9il5Ajd9bPIW9fm"
    "NZ/QPleyQO"
)
