from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import func, select

from config import INDEXER_FETCH_TIMEOUT_SECONDS, INDEXER_SYNC_INTERVAL_SECONDS
from database import SessionLocal
from models import Election
from services.blockchain import fetch_factory_elections

logger = logging.getLogger("indexer")


class ElectionIndexer:
    """Periodically sync factory child contracts into MySQL.

    This keeps request paths fast by avoiding per-request chain reads for basic
    project metadata (title/start/end).
    """

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop(), name="election-indexer")
        logger.info("[Indexer] started")

    async def stop(self) -> None:
        self._running = False
        if not self._task:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("[Indexer] stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self.sync_once()
            except Exception as exc:  # defensive: keep worker alive
                logger.warning("[Indexer] sync cycle failed: %s", exc)
            await asyncio.sleep(INDEXER_SYNC_INTERVAL_SECONDS)

    async def sync_once(self) -> None:
        loop = asyncio.get_running_loop()
        try:
            catalog: list[dict[str, Any]] = await asyncio.wait_for(
                loop.run_in_executor(None, fetch_factory_elections),
                timeout=INDEXER_FETCH_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            logger.warning("[Indexer] fetch factory catalog failed: %s", exc)
            return

        if not isinstance(catalog, list) or not catalog:
            return

        normalized = [item for item in catalog if item.get("address")]
        if not normalized:
            return

        addresses = [item["address"].lower() for item in normalized]

        async with SessionLocal() as db:
            rows = (
                await db.execute(
                    select(Election).where(func.lower(Election.contract_address).in_(addresses))
                )
            ).scalars().all()
            existing = {row.contract_address.lower(): row for row in rows}

            changed = False
            for item in normalized:
                address = item["address"].lower()
                title = (item.get("title") or "").strip()
                start_time = int(item.get("start_time") or 0)
                end_time = int(item.get("end_time") or 0)

                row = existing.get(address)
                if row is None:
                    db.add(
                        Election(
                            contract_address=address,
                            title=title,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
                    changed = True
                    continue

                if row.title != title:
                    row.title = title
                    changed = True
                if row.start_time != start_time:
                    row.start_time = start_time
                    changed = True
                if row.end_time != end_time:
                    row.end_time = end_time
                    changed = True

            if changed:
                await db.commit()
                logger.info("[Indexer] synced %d elections", len(normalized))


election_indexer = ElectionIndexer()
