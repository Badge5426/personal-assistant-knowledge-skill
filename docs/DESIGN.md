# 设计与来源依据

这是个人助手上下文维护方法，不是一般资料库。七类组织与三层存放来自任务提供的匿名方案及范围要求；公开实现为本项目原创，不包含真实个人档案或会话。

已有 Skill Creator / Skill Installer 提供文件结构、渐进读取、安装不覆盖原则。本包不复制其脚本；本地助手与安装器均自行实现，只用 Python 标准库。
本轮未引入第三方实现、依赖、插件或远端服务。未执行陌生仓库代码。LifeOS 的身份/目标分层仅是可选参考，未复制内容；其 MIT 不被当作访问控制，publish:false 也不赋予保密能力。

兼容性核查日期：2026-10-09。
- [Build skills](https://learn.chatgpt.com/docs/build-skills)：独立 Skill 客户端、本地 .agents/skills 与插件分发区别。
- [Space getting started](https://learn.chatgpt.com/docs/space/getting-started)：账号访问与页面权限。
- [Space agents](https://learn.chatgpt.com/docs/space/agents)：定时工作必须独立创建并验证。
- [Long-running work](https://learn.chatgpt.com/docs/long-running-work)：/goal 是产品模式入口；一个目标提示词不能证明已启用 Goal。

本包没有 Goal 启用代码、真实 Space 写入代码、永久记忆服务、Web/手机插件或自动调度器。模型、客户端和 app 工具的运行能力仍需目标环境验证。
