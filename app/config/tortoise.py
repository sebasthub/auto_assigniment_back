TORTOISE_ORM = {
    "connections": {
        "default": "sqlite://db.sqlite3",
    },
    "apps": {
        "models": {
            "models": [
                "app.models.assignment",
                "app.models.topic",
                "aerich.models",
            ],
            "default_connection": "default",
        }
    },
}
