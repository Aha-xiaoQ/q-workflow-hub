# q-workflow v1.0-beta

[English](q-workflow-v1.0-beta.md) | **简体中文**

`v1.0-beta` 是以恢复能力为先的 q-workflow 内核首个公开 beta 版本。
其符合 SemVer 的预发布标识为 `1.0.0-beta`，显示标签为 `v1.0-beta`。

## 相关链接

- [仓库](https://github.com/Aha-xiaoQ/q-workflow-hub)
- [对应版本源码](https://github.com/Aha-xiaoQ/q-workflow-hub/tree/v1.0-beta)
- [英文快速开始](../../QUICKSTART.md)
- [中文快速开始](../../QUICKSTART.zh-CN.md)
- [更新记录](../../CHANGELOG.zh-CN.md)
- [问题跟踪](https://github.com/Aha-xiaoQ/q-workflow-hub/issues)

## 包含范围

- `skills/q-workflow`：管理器命令行工具、任务状态与事件契约、组件注册表、运行时清单、
  恢复／输出检查，以及验证和稳定性工具。
- `skills/q-agent-roster`：工作流检查直接覆盖的交接、验证场景及子智能体模型自适应路由组件。
- `skills/q-skill-creation/scripts/skill_portfolio_audit.py`：完整诊断使用的、能够识别配置档案的技能组合检查工具。
- `scripts/sync-workflow-bootstrap.ps1`：经过注册表验证的源码到引导副本同步，并可选同步到运行时。

## 主要变化

- `q_workflow_manager.py` 为 `status`、`doctor`、`registry`、`surfaces` 以及任务发现／验证
  提供一个默认只读的统一入口。
- 实质性任务状态变更采用可审查的计划／应用事务，具备显式确认、比较并交换哈希、共享操作系统锁、
  原子替换、回滚、回读检查和操作凭证。
- `ACTIVE_WORK.md` 是当前焦点视图，不再是唯一的任务数据库；任务记录与 JSONL 事件支持按
  `task_id`／`trace_id` 独立验证。
- 按内容寻址的组件注册表管理源码、引导副本、运行时和个人源目录的预期状态。同步前先验证注册表，再暂存文件。
- 运行证据保持精简：状态、哈希、`elapsed_ms`、稳定的 `failure_class` 和产物路径。
  默认遥测不包含提示词、凭据或私人产物正文。

## 安装或固定到 beta 版本

全新克隆：

```powershell
git clone --branch v1.0-beta --depth 1 https://github.com/Aha-xiaoQ/q-workflow-hub.git
```

已有本地副本：

```powershell
git fetch --tags origin
git switch --detach v1.0-beta
```

该标签不可变。检出标签后处于分离状态，不应使用 `git pull`；发布了经过审查的新标签后，
应先抓取标签，再显式切换。

选定 beta 源码后，请按照[中文快速开始](../../QUICKSTART.zh-CN.md)或
[英文快速开始](../../QUICKSTART.md)操作。已有用户可按照文档中的
`scripts/sync-workflow-bootstrap.ps1` 路径刷新私人引导副本，并可选刷新运行时安装。

## 兼容性

- 现有 Markdown 状态文件仍可读取。
- `RECOVERY_POINTER v1` 仍作为扁平化的兼容视图。
- `sync_state` 是派生的旧版别名；已注册任务记录中的工作、完整性与发布状态仍是独立维度。
- 遇到未知的未来主版本结构定义时，拒绝继续处理，而不是猜测其含义。
- 新管理器命令是增量添加；写入任务仍需要先显式生成计划，再使用 `--yes` 应用。

## 已知限制

- 由于尚未实现持久化预写日志，在多个文件切换之间强制终止进程，可能留下未完成的事务。
- 发布保证覆盖五个已注册核心组件。旗舰技能和实验技能仍是各自独立版本的候选，
  除非它们自己的检查明确给出其他结论。
- 远程最新状态只能由成功的抓取／推送／回读过程证明；本地标签或缓存的远程跟踪引用并不足够。

## 恢复与回滚

将私人状态保存在本公开起步包之外。如需查看本次 beta 之前的公开起步包，且不重写工作分支，可使用：

```powershell
git switch --detach 74096b83cf75ffec64dac4e07f35c701993efa10
```

使用 `git switch --detach v1.0-beta` 返回 beta 版本。
不要对状态不明或有未提交更改的工作区执行强制重置。
