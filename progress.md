# Progress

- 已创建规划文件并进入审计阶段。
- 新增后台索引任务 `backend/services/indexer.py`，启动后定时把工厂子合约元数据同步到 MySQL。
- FastAPI 生命周期接入 indexer 启停（startup/shutdown）。
- 实时推送服务增加 snapshot 短缓存，降低频繁重连时查链开销。
- 从 `my-elections` 请求路径移除同步标题刷写，避免 per-request 重链操作。
- `auth` 路由新增分段耗时日志（my-elections: total/fetch/filter；ticket-status: total）。
- 新增 `PERF_BENCHMARK_TEMPLATE.md`，用于 Before/After 压测对比与验收。
