import os

from fastapi.middleware.cors import CORSMiddleware


def setup_middlewares(app):
    env_origins = os.getenv("CORS_ORIGINS")
    if env_origins:
        origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    else:
        origins = ["http://localhost:4200", "http://127.0.0.1:4200"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
