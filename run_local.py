import os
from pathlib import Path


def setup_local_environment() -> Path:
    """Configure environment variables for local development."""
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    sqlite_db_path = data_dir / "local_dev.db"

    # Configure local-first environment before importing app/config modules.
    os.environ["DEBUG"] = "True"
    os.environ["API_HOST"] = os.getenv("API_HOST", "127.0.0.1")
    os.environ["API_PORT"] = os.getenv("API_PORT", "5000")
    os.environ["DATABASE_URL"] = f"sqlite:///{sqlite_db_path.as_posix()}"
    os.environ["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    os.environ["RATE_LIMIT_PER_MINUTE"] = os.getenv("RATE_LIMIT_PER_MINUTE", "120 per minute")

    return sqlite_db_path


def initialize_and_seed_database() -> None:
    """Create tables and seed dictionary/sentence data."""
    from config.database_config import SessionLocal
    from scripts.init_db import create_tables, seed_dictionary, seed_sentences

    create_tables()
    session = SessionLocal()
    try:
        inserted_words = seed_dictionary(session)
        inserted_sentences = seed_sentences(session)
        session.commit()
        print(f"Database initialized. Added {inserted_words} dictionary entries.")
        print(f"Added {inserted_sentences} sample sentences.")
    finally:
        session.close()


def run_local_app() -> None:
    """Start Flask app in debug mode for local development."""
    from api import app as app_module

    # Local mode should not hard-fail if Redis is absent.
    import services.translation_service as translation_module

    translation_module.redis_client = None

    app_module.app.config.update(
        ENV="development",
        DEBUG=True,
    )
    host = os.environ.get("API_HOST", "127.0.0.1")
    port = int(os.environ.get("API_PORT", "5000"))
    app_module.app.run(host=host, port=port, debug=True)


def main() -> None:
    db_path = setup_local_environment()
    print(f"Using local SQLite database: {db_path}")
    initialize_and_seed_database()
    print("Starting local Flask server in debug mode...")
    print("Open: http://127.0.0.1:5000")
    run_local_app()


if __name__ == "__main__":
    main()
