# Perf Benchmark Template

## 1. Scope

- API A: `/api/auth/login`
- API B: `/api/auth/my-elections`
- API C: `/api/auth/ticket-status/{election_address}`
- WS: `/ws/elections/{election_address}/votes`

## 2. Environment

- Backend commit:
- Frontend commit:
- Machine spec:
- RPC provider:
- DB size (elections / voters / tickets):

## 3. Method

### 3.1 Warm-up

Run 20 warm-up requests before sampling.

### 3.2 Sample

- Concurrency: 1 / 5 / 10
- Duration: 60s each
- Tool suggestion: `hey` or `wrk`

### 3.3 Example Commands

```bash
# login (replace payload)
hey -n 200 -c 10 -m POST -H "Content-Type: application/json" -d '{"student_id":"2025001","password":"xxx"}' http://localhost:8000/api/auth/login

# my-elections (replace token)
hey -n 300 -c 10 -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/auth/my-elections

# ticket-status (replace token/address)
hey -n 300 -c 10 -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/auth/ticket-status/<ELECTION_ADDRESS>
```

## 4. Metrics Table

| API | Version | P50 | P95 | P99 | Avg | RPS | Error % |
|---|---|---:|---:|---:|---:|---:|---:|
| /auth/login | Before |  |  |  |  |  |  |
| /auth/login | After |  |  |  |  |  |  |
| /auth/my-elections | Before |  |  |  |  |  |  |
| /auth/my-elections | After |  |  |  |  |  |  |
| /auth/ticket-status | Before |  |  |  |  |  |  |
| /auth/ticket-status | After |  |  |  |  |  |  |

## 5. Log Parsing (Perf)

The backend now logs perf lines in `app_business.log`:

- `[Perf] /auth/my-elections ... total=... fetch=... filter=...`
- `[Perf] /auth/ticket-status ... total=...`

Use these fields to identify whether latency is dominated by:

- `fetch`: chain catalog / DB execute stage
- `filter`: in-memory shaping/filter stage

## 6. Acceptance Suggestion

- `/auth/login` P95 < 300ms
- `/auth/my-elections` P95 < 800ms
- `/auth/ticket-status` P95 < 400ms
- WS first snapshot < 1.2s
