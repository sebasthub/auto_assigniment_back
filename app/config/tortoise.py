TORTOISE_ORM = {
    "connections": {
        "default": "sqlite://db.sqlite3",
    },
    "apps": {
        "models": {
            "models": [
                "app.models.assignment",
                "app.models.user",
                "app.models.topic",
                "app.models.refresh_token",
                "aerich.models",
                "app.models.document_record",
            ],
            "default_connection": "default",
        }
    },
}
