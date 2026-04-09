from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket
from web3 import Web3

from config import REALTIME_SNAPSHOT_CACHE_SECONDS
from services.blockchain import get_contract, get_web3

POLL_INTERVAL_SECONDS = 3
RECENT_EVENT_LIMIT = 60
RECENT_LOOKBACK_BLOCKS = 200
MAX_LOG_BLOCK_RANGE = 10
BLOCK_TIME_CACHE_SECONDS = 30


def _to_iso(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


async def _run_blocking(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args))


class VoteStreamManager:
    def __init__(self) -> None:
        self.connections: dict[str, set[WebSocket]] = {}
        self.watch_tasks: dict[str, asyncio.Task] = {}
        self.state_lock = asyncio.Lock()
        self.snapshot_cache: dict[str, dict[str, Any]] = {}
        self.block_time_cache: dict[int, dict[str, float | int]] = {}

    async def connect(self, election_address: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.state_lock:
            self.connections.setdefault(election_address, set()).add(websocket)
            if election_address not in self.watch_tasks:
                self.watch_tasks[election_address] = asyncio.create_task(
                    self._watch_election(election_address)
                )

        snapshot = await self._get_snapshot_with_cache(election_address)
        await websocket.send_json(snapshot)

    async def disconnect(self, election_address: str, websocket: WebSocket) -> None:
        async with self.state_lock:
            sockets = self.connections.get(election_address)
            if not sockets:
                return

            sockets.discard(websocket)
            if not sockets:
                self.connections.pop(election_address, None)
                task = self.watch_tasks.pop(election_address, None)
                if task:
                    task.cancel()
                    self.snapshot_cache.pop(election_address, None)
                    self._prune_block_time_cache(force=True)

    async def _watch_election(self, election_address: str) -> None:
        last_processed_block = await _run_blocking(self._get_current_block, election_address)

        try:
            while True:
                async with self.state_lock:
                    has_connections = bool(self.connections.get(election_address))

                if not has_connections:
                    return

                try:
                    payload = await self._build_incremental_payload_async(
                        election_address,
                        last_processed_block,
                    )
                    last_processed_block = payload["last_processed_block"]
                    if payload["new_events"]:
                        await self._broadcast(
                            election_address,
                            {
                                "type": "vote_update",
                                "electionAddress": election_address,
                                "generatedAt": datetime.now(timezone.utc).isoformat(),
                                "totals": payload["totals"],
                                "candidates": payload["candidates"],
                                "newEvents": payload["new_events"],
                                "latestVote": payload["new_events"][-1],
                            },
                        )
                except Exception as exc:
                    await self._broadcast(
                        election_address,
                        {
                            "type": "stream_error",
                            "electionAddress": election_address,
                            "message": str(exc),
                            "generatedAt": datetime.now(timezone.utc).isoformat(),
                        },
                    )

                await asyncio.sleep(POLL_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            return

    async def _get_snapshot_with_cache(self, election_address: str) -> dict[str, Any]:
        now = asyncio.get_running_loop().time()
        cached = self.snapshot_cache.get(election_address)
        if cached and now < float(cached.get("expires_at", 0)):
            return cached["payload"]

        snapshot = await self._build_snapshot_payload_async(election_address)
        self.snapshot_cache[election_address] = {
            "payload": snapshot,
            "expires_at": now + REALTIME_SNAPSHOT_CACHE_SECONDS,
        }
        return snapshot

    async def _broadcast(self, election_address: str, payload: dict[str, Any]) -> None:
        async with self.state_lock:
            sockets = list(self.connections.get(election_address, set()))

        if not sockets:
            return

        send_tasks = [socket.send_json(payload) for socket in sockets]
        send_results = await asyncio.gather(*send_tasks, return_exceptions=True)
        dead_sockets: list[WebSocket] = [
            socket
            for socket, result in zip(sockets, send_results)
            if isinstance(result, Exception)
        ]

        if dead_sockets:
            await asyncio.gather(
                *(self.disconnect(election_address, socket) for socket in dead_sockets),
                return_exceptions=True,
            )

    async def _build_snapshot_payload_async(self, election_address: str) -> dict[str, Any]:
        status_task = _run_blocking(self._read_voting_status, election_address)
        candidates_task = _run_blocking(self._read_all_candidates, election_address)
        latest_block_task = _run_blocking(self._read_latest_block)
        status, all_candidates, latest_block = await asyncio.gather(
            status_task,
            candidates_task,
            latest_block_task,
        )

        names, imageCids, manifestoCids, votes = all_candidates
        recent_logs = await _run_blocking(
            self._fetch_recent_vote_logs_for_address,
            election_address,
            latest_block,
        )
        recent_events = await self._serialize_vote_events_async(recent_logs)
        candidates = self._serialize_candidates(names, imageCids, manifestoCids, votes)

        return {
            "type": "snapshot",
            "electionAddress": election_address,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "totals": self._serialize_totals(status),
            "candidates": candidates,
            "recentEvents": recent_events,
        }

    async def _build_incremental_payload_async(
        self, election_address: str, last_processed_block: int
    ) -> dict[str, Any]:
        latest_block = await _run_blocking(self._read_latest_block)
        if latest_block <= last_processed_block:
            return {
                "last_processed_block": last_processed_block,
                "new_events": [],
                "totals": None,
                "candidates": None,
            }

        logs = await _run_blocking(
            self._read_voted_logs,
            election_address,
            last_processed_block + 1,
            latest_block,
        )
        if not logs:
            return {
                "last_processed_block": latest_block,
                "new_events": [],
                "totals": None,
                "candidates": None,
            }

        status_task = _run_blocking(self._read_voting_status, election_address)
        candidates_task = _run_blocking(self._read_all_candidates, election_address)
        events_task = self._serialize_vote_events_async(logs)
        status, all_candidates, new_events = await asyncio.gather(
            status_task,
            candidates_task,
            events_task,
        )

        names, imageCids, manifestoCids, votes = all_candidates
        return {
            "last_processed_block": latest_block,
            "new_events": new_events,
            "totals": self._serialize_totals(status),
            "candidates": self._serialize_candidates(names, imageCids, manifestoCids, votes),
        }

    def _read_latest_block(self) -> int:
        w3 = get_web3()
        return int(w3.eth.block_number)

    def _read_voting_status(self, election_address: str) -> Any:
        w3 = get_web3()
        contract = get_contract(w3, election_address)
        return contract.functions.getVotingStatus().call()

    def _read_all_candidates(self, election_address: str) -> tuple[list[str], list[str], list[str], list[int]]:
        w3 = get_web3()
        contract = get_contract(w3, election_address)
        return contract.functions.getAllCandidates().call()

    def _read_voted_logs(self, election_address: str, from_block: int, to_block: int) -> list[Any]:
        w3 = get_web3()
        contract = get_contract(w3, election_address)
        return self._get_voted_logs_in_range(contract, from_block, to_block)

    def _fetch_recent_vote_logs_for_address(self, election_address: str, latest_block: int) -> list[Any]:
        w3 = get_web3()
        contract = get_contract(w3, election_address)
        return self._fetch_recent_vote_logs(contract, latest_block)

    def _read_block_timestamp(self, block_number: int) -> int:
        w3 = get_web3()
        return int(w3.eth.get_block(block_number)["timestamp"])

    async def _serialize_vote_events_async(self, logs: list[Any]) -> list[dict[str, Any]]:
        if not logs:
            return []

        block_numbers = sorted({int(log["blockNumber"]) for log in logs})
        block_time_map = await self._get_block_timestamp_map(block_numbers)

        events: list[dict[str, Any]] = []
        for index, log in enumerate(logs, start=1):
            block_number = int(log["blockNumber"])
            block_timestamp = int(block_time_map.get(block_number, 0))
            events.append(
                {
                    "sequence": index,
                    "candidateId": int(log["args"]["candidateId"]),
                    "voter": log["args"]["voter"],
                    "txHash": log["transactionHash"].hex(),
                    "blockNumber": block_number,
                    "blockTime": _to_iso(block_timestamp),
                }
            )

        return events

    async def _get_block_timestamp_map(self, block_numbers: list[int]) -> dict[int, int]:
        now = asyncio.get_running_loop().time()
        result: dict[int, int] = {}
        missing: list[int] = []

        for block_number in block_numbers:
            cached = self.block_time_cache.get(block_number)
            if cached and now < float(cached.get("expires_at", 0)):
                result[block_number] = int(cached["timestamp"])
            else:
                missing.append(block_number)

        if missing:
            fetch_tasks = [_run_blocking(self._read_block_timestamp, block_number) for block_number in missing]
            fetched = await asyncio.gather(*fetch_tasks)
            for block_number, timestamp in zip(missing, fetched):
                result[block_number] = int(timestamp)
                self.block_time_cache[block_number] = {
                    "timestamp": int(timestamp),
                    "expires_at": now + BLOCK_TIME_CACHE_SECONDS,
                }

        self._prune_block_time_cache()
        return result

    def _prune_block_time_cache(self, force: bool = False) -> None:
        if not self.block_time_cache:
            return

        now = asyncio.get_running_loop().time()
        if force:
            self.block_time_cache.clear()
            return

        expired_keys = [
            block_number
            for block_number, payload in self.block_time_cache.items()
            if now >= float(payload.get("expires_at", 0))
        ]
        for block_number in expired_keys:
            self.block_time_cache.pop(block_number, None)

    def _get_current_block(self, election_address: str) -> int:
        w3 = get_web3()
        contract = get_contract(w3, election_address)
        latest_block = int(w3.eth.block_number)
        return latest_block if self._contract_has_vote_history(contract, latest_block) else max(latest_block - 1, 0)

    def _fetch_recent_vote_logs(self, contract: Any, latest_block: int) -> list[Any]:
        lower_bound = max(0, latest_block - RECENT_LOOKBACK_BLOCKS)
        logs: list[Any] = []
        current_to = latest_block

        while current_to >= lower_bound and len(logs) < RECENT_EVENT_LIMIT:
            current_from = max(lower_bound, current_to - (MAX_LOG_BLOCK_RANGE - 1))
            chunk_logs = self._get_voted_logs_in_range(contract, current_from, current_to)
            if chunk_logs:
                logs = chunk_logs + logs
            current_to = current_from - 1

        if len(logs) > RECENT_EVENT_LIMIT:
            logs = logs[-RECENT_EVENT_LIMIT:]
        return logs

    def _serialize_candidates(
        self, names: list[str], imageCids: list[str], manifestoCids: list[str], votes: list[int]
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": index,
                "name": names[index],
                "cid": imageCids[index],
                "manifestoCid": manifestoCids[index],
                "votes": int(votes[index]),
            }
            for index in range(len(names))
        ]

    def _serialize_totals(self, status: Any) -> dict[str, Any]:
        return {
            "started": bool(status[0]),
            "ended": bool(status[1]),
            "candidates": int(status[2]),
            "voters": int(status[3]),
            "voted": int(status[4]),
        }

    def _contract_has_vote_history(self, contract: Any, latest_block: int) -> bool:
        if latest_block <= 0:
            return False
        from_block = max(0, latest_block - 1)
        logs = self._get_voted_logs_in_range(contract, from_block, latest_block)
        return bool(logs)

    def _get_voted_logs_in_range(self, contract: Any, from_block: int, to_block: int) -> list[Any]:
        if to_block < from_block:
            return []

        logs: list[Any] = []
        current = from_block
        while current <= to_block:
            chunk_end = min(current + (MAX_LOG_BLOCK_RANGE - 1), to_block)
            chunk_logs = contract.events.Voted().get_logs(
                fromBlock=current,
                toBlock=chunk_end,
            )
            if chunk_logs:
                logs.extend(chunk_logs)
            current = chunk_end + 1

        return logs


vote_stream_manager = VoteStreamManager()
