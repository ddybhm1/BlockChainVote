# Findings

- 已有 WebSocket 推送链路：每个投票项目只维护一个 watcher 任务，天然优于前端轮询。
- 登录慢的核心在请求路径上混入链上读取；已通过后台 indexer 同步到 MySQL，减少请求时查链。
- 实时大屏存在频繁重连/多开页时重复构建 snapshot 的成本；已加入短 TTL 快照缓存。
- `/auth/my-elections` 之前会在请求中做同步标题刷写；已改为依赖后台索引任务。
