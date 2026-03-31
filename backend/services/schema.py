from sqlalchemy import inspect, text

from database import engine


def _ensure_claimed_tickets_columns(sync_conn) -> None:
    inspector = inspect(sync_conn)
    if "claimed_tickets" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("claimed_tickets")}

    if "status" not in columns:
        sync_conn.execute(
            text(
                "ALTER TABLE claimed_tickets "
                "ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'CLAIMED'"
            )
        )
    if "tx_hash" not in columns:
        sync_conn.execute(
            text("ALTER TABLE claimed_tickets ADD COLUMN tx_hash VARCHAR(255) NULL")
        )
    if "vote_tx_hash" not in columns:
        sync_conn.execute(
            text("ALTER TABLE claimed_tickets ADD COLUMN vote_tx_hash VARCHAR(255) NULL")
        )
    if "created_at" not in columns:
        sync_conn.execute(
            text("ALTER TABLE claimed_tickets ADD COLUMN created_at DATETIME NULL")
        )
    if "updated_at" not in columns:
        sync_conn.execute(
            text("ALTER TABLE claimed_tickets ADD COLUMN updated_at DATETIME NULL")
        )

    sync_conn.execute(
        text(
            "UPDATE claimed_tickets "
            "SET status = COALESCE(status, 'CLAIMED'), "
            "created_at = COALESCE(created_at, NOW()), "
            "updated_at = COALESCE(updated_at, NOW())"
        )
    )


def _ensure_elections_columns(sync_conn) -> None:
    inspector = inspect(sync_conn)
    if "elections" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("elections")}

    if "title" not in columns:
        sync_conn.execute(
            text("ALTER TABLE elections ADD COLUMN title VARCHAR(255) NULL")
        )

    sync_conn.execute(
        text(
            "UPDATE elections "
            "SET title = COALESCE(title, '')"
        )
    )


async def ensure_runtime_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(_ensure_claimed_tickets_columns)
        await conn.run_sync(_ensure_elections_columns)
