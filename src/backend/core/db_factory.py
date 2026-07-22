"""
IPF IPA PoC - Database Factory
Auto-selects Supabase or SQLite based on availability and configuration.
Set USE_SQLITE=true in .env to force SQLite mode.
"""
import os
import logging

logger = logging.getLogger(__name__)

_db_instance = None


def get_database():
    """
    Returns the appropriate database instance.
    Auto-fallback: tries Supabase first, falls back to SQLite.
    """
    global _db_instance
    if _db_instance is not None:
        return _db_instance

    # Force SQLite via env var
    if os.getenv("USE_SQLITE", "").lower() in ("true", "1", "yes"):
        logger.info("Using SQLite (USE_SQLITE=true)")
        from .sqlite_database import SQLiteDatabase
        _db_instance = SQLiteDatabase()
        return _db_instance

    # Try Supabase
    supabase_url = os.getenv("SUPABASE_URL", "")
    if supabase_url and supabase_url != "https://your-project.supabase.co":
        try:
            from .database import Database
            db = Database()
            # Quick connectivity test
            db.client.table("documents").select("id").limit(1).execute()
            logger.info("Using Supabase database")
            _db_instance = db
            return _db_instance
        except Exception as e:
            logger.warning(f"Supabase unavailable ({e}), falling back to SQLite")

    # Fallback: SQLite
    logger.info("Using SQLite database (local fallback)")
    from .sqlite_database import SQLiteDatabase
    _db_instance = SQLiteDatabase()
    return _db_instance


# Convenience alias
Database = get_database
