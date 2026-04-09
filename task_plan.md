# Task Plan

## Goal
实现登录与大屏性能优化：引入索引层思路、减少链上实时读取、优化列表页检索与加载体验。

## Phases
- [complete] 1. 现状审计与瓶颈定位
- [complete] 2. 后端索引/聚合与缓存改造
- [complete] 3. 前端列表与感知性能优化
- [in_progress] 4. 验证与回归检查

## Risks
- 链上 RPC 波动导致数据同步中断
- 过于激进缓存导致实时性下降
