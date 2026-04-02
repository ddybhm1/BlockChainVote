from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket
from web3 import Web3

from services.blockchain import get_contract, get_web3

POLL_INTERVAL_SECONDS = 3
RECENT_EVENT_LIMIT = 60
RECENT_LOOKBACK_BLOCKS = 200
MAX_LOG_BLOCK_RANGE = 10


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

    async def connect(self, election_address: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.state_lock:
            self.connections.setdefault(election_address, set()).add(websocket)
            if election_address not in self.watch_tasks:
                self.watch_tasks[election_address] = asyncio.create_task(
                    self._watch_election(election_address)
                )

        snapshot = await _run_blocking(self._build_snapshot_payload, election_address)
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

    async def _watch_election(self, election_address: str) -> None:
        last_processed_block = await _run_blocking(self._get_current_block, election_address)

        try:
            while True:
                async with self.state_lock:
                    has_connections = bool(self.connections.get(election_address))

                if not has_connections:
                    return

                try:
                    payload = await _run_blocking(
                        self._build_incremental_payload,
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

    async def _broadcast(self, election_address: str, payload: dict[str, Any]) -> None:
        async with self.state_lock:
            sockets = list(self.connections.get(election_address, set()))

        dead_sockets: list[WebSocket] = []
        for socket in sockets:
            try:
                await socket.send_json(payload)
            except Exception:
                dead_sockets.append(socket)

        for socket in dead_sockets:
            await self.disconnect(election_address, socket)

    def _get_current_block(self, election_address: str) -> int:
        w3 = get_web3()
        contract = get_contract(w3, election_address)
        latest_block = int(w3.eth.block_number)
        return latest_block if self._contract_has_vote_history(contract, latest_block) else max(latest_block - 1, 0)

    def _build_snapshot_payload(self, election_address: str) -> dict[str, Any]:
        w3 = get_web3()
        contract = get_contract(w3, election_address)
        status = contract.functions.getVotingStatus().call()
        names, imageCids, manifestoCids, votes = contract.functions.getAllCandidates().call()
        latest_block = int(w3.eth.block_number)

        recent_events = self._fetch_recent_votes(w3, contract, latest_block)
        candidates = self._serialize_candidates(names, imageCids, manifestoCids, votes)

        return {
            "type": "snapshot",
            "electionAddress": election_address,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "totals": self._serialize_totals(status),
            "candidates": candidates,
            "recentEvents": recent_events,
        }

    def _build_incremental_payload(
        self, election_address: str, last_processed_block: int
    ) -> dict[str, Any]:
        w3 = get_web3()
        contract = get_contract(w3, election_address)
        latest_block = int(w3.eth.block_number)
        if latest_block <= last_processed_block:
            return {
                "last_processed_block": last_processed_block,
                "new_events": [],
                "totals": None,
                "candidates": None,
            }

        logs = self._get_voted_logs_in_range(
            contract,
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

        status = contract.functions.getVotingStatus().call()
        names, imageCids, manifestoCids, votes = contract.functions.getAllCandidates().call()
        new_events = self._serialize_vote_events(w3, logs)

        return {
            "last_processed_block": latest_block,
            "new_events": new_events,
            "totals": self._serialize_totals(status),
            "candidates": self._serialize_candidates(names, imageCids, manifestoCids, votes),
        }

    def _fetch_recent_votes(self, w3: Web3, contract: Any, latest_block: int) -> list[dict[str, Any]]:
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
        return self._serialize_vote_events(w3, logs)

    def _serialize_vote_events(self, w3: Web3, logs: list[Any]) -> list[dict[str, Any]]:
        block_cache: dict[int, int] = {}
        events: list[dict[str, Any]] = []

        for index, log in enumerate(logs, start=1):
            block_number = int(log["blockNumber"])
            if block_number not in block_cache:
                block_cache[block_number] = int(w3.eth.get_block(block_number)["timestamp"])

            block_timestamp = block_cache[block_number]
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
