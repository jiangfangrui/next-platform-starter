# Git 操作规范

## 1. 提交规范

- 格式：`<type>(<scope>): <subject>`
- type 可选值：`feat`、`fix`、`docs`、`style`、`refactor`、`test`、`chore`
- scope：说明涉及的模块或功能块，如 `books-nav`、`content-docs`、`build`
- subject：一句话描述修改点，动词原形，不超过 72 字符，不以句号结尾
- 示例：
  - `feat(books-nav): 统一书籍子站引用为 /books 前缀`
  - `fix(content-index): 修复菜单图标相对路径导致的 404`
  - `docs(standards): 新增 Git 操作规范与钩子提示`
  - `refactor(tools): 重构批量路径转换脚本与验证逻辑`
  - `chore(repo): 更新 .gitignore 忽略备份与日志`
- 建议：
  - 关联任务/Issue：在提交正文或 PR 中引用 `#123`
  - 原子提交：每次提交尽量只做一件事，便于回滚与审查
  - 提交正文：如需补充，使用多行正文说明动机、影响范围、风险与回滚方案

## 2. 分支管理规则

- 主分支保护：`main`
  - 禁止直接推送；必须通过 PR 合并
  - 合并策略：`Squash & Merge`（推荐）或 `Rebase & Merge`（保持线性历史）
- 功能分支命名：
  - `feature/<scope>-<short-desc>`（示例：`feature/books-prefix-cleanup`）
  - `fix/<issue-id>-<short-desc>`（示例：`fix/123-broken-icons`）
  - 紧急修复：`hotfix/<short-desc>`（直接从 `main` 切出）
- 合并请求审查流程：
  - 自检通过（见第 3 节检查清单）后发起 PR
  - 至少 1 人 Code Review，避免作者本人自审自合并
  - CI/预览通过后方可合并；合并后由发布负责人执行发布步骤

## 3. 代码审查建议

- 必做检查清单：
  - 构建/预览通过，无报错（Console/Network 无 404/跨域/脚本错误）
  - 静态资源路径一致：书籍子站统一使用 `/books/...`
  - 不引入本地绝对文件系统路径（如 `E:\...`、`/var/...`）
  - 安全检查：不提交敏感信息（密钥、Token、私人数据）；`.gitignore` 生效
  - 兼容性：Windows 下行尾 CRLF/LF 处理合理；避免路径分隔符不一致
  - 可回滚性：复杂改动具备回滚说明与备份（如 `_backup_before_path_conversion/`）
- 常见问题与解决：
  - 页面在根站点访问书籍子站：确保使用 `/books/...` 前缀而非相对路径
  - 资源 404：检查目录层级与前缀是否匹配；使用本地预览核对 URL
  - 合并冲突：优先 `git pull --ff-only` 保持线性历史，必要时 rebase
- 最佳实践示例：
  - 小步快跑：将路径修复、布局注释、脚本重构分开提交
  - PR 描述包含动机、变更范围、验证方式、回滚方法与影响评估

## 4. 操作流程指南

- 日常开发工作流：
  - 从 `main` 切出功能分支 → 开发与自测 → 提交与推送 → 发起 PR → 审查通过合并
- 紧急修复流程：
  - 从 `main` 切出 `hotfix/*` → 修复并验证 → 提交 PR → 快速审查 → 合并并发布
- 版本发布步骤：
  - 合并到 `main` 后打标签：`git tag -a vX.Y.Z -m "release: vX.Y.Z"`
  - 推送标签：`git push origin --tags`
  - 生成发布说明（变更列表、兼容性、升级指引）并在平台完成部署

## 5. 工具配置建议

- Git 钩子：
  - 本仓库提供 `pre-commit` 钩子提示（本地 `.git/hooks/pre-commit`）
  - 团队共享建议：设置 `core.hooksPath` 指向仓库内版本化钩子目录，例如 `.githooks`
- 客户端工具：
  - VS Code（集成终端与 Git，推荐安装 GitLens）
  - SourceTree / GitKraken（可视化分支与历史）
- 可视化技巧：
  - 图形历史：`git log --graph --oneline --decorate --all`
  - 差异对比：`git diff --stat`、`git difftool`

---

- 本规范适用于本仓库所有提交与合并操作；如需更新，请在 PR 中修改本文件并同步团队通知。

