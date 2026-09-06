# 给编码 Agent 的首次提示词

把下面这段直接粘贴给 Codex、Claude Code 或其他可以运行终端命令的编码 Agent：

```text
请从这个公开 starter 帮我设置 q-workflow：
https://github.com/Aha-xiaoQ/q-workflow-hub.git

请用简单中文一步一步引导我。
请把 QUICKSTART.zh-CN.md、QUICKSTART.md 和 MACHINE_BOOTSTRAP.md 作为安装依据。
先说明 q-workflow 会创建什么、哪些内容应该保持私有。
检查 Git 和我的编码 Agent 环境是否可用。
只询问安装必需的信息，然后帮我安装 q-workflow。
安装完成后，请打开或概括 FIRST_RUN_GUIDE.zh-CN.html，验证是否成功，告诉我日常恢复提示词，并带我做第一次恢复测试。
```

Agent 应该向你询问：

- 显示名称；
- 工作区根目录；
- 个人工作流资料夹路径，也就是需要保持私有的本地资料夹；
- 可选的工作流标签，用于可见的恢复提示头；
- 可选的私有备份 Git 仓库地址。

首次设置完成后，日常使用：

```text
继续我的项目，使用 q-workflow。
```

重启 Agent 后，可以用显示名称做最短 smoke test：

```text
<显示名称>
```

预期第一行类似：

```text
【小Q工作流 | 快速恢复 】
```

恢复指定项目：

```text
继续 <项目名称>，使用 q-workflow。
```

也可以用你的名字或项目名帮助 Agent 定位：

```text
继续 <用户名称或项目名称>，使用 q-workflow。
```
