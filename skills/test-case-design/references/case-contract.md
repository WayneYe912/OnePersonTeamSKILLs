# 用例数据契约与前置交接

## 输入与交接

同任务 PRD 是必需输入，技术方案可选。先看显式材料、本轮确定交接、pipeline.json，再同任务唯一候选。没有或无法读取就问是否先帮助完善 PRD，等待用户；不得直接编模板或把技能示例当真实文档。

同仓库共享工具：`../product-development/scripts/pipeline.py resolve --only-prd --task-dir <任务目录>`。无共享工具时仍可人工核验相同范围和版本，不强制安装开发技能。文档读全才推导用例，路径或摘要不证明业务准确。

用例记录实际 PRD 摘要；JSON/HTML 两载体同时存在时指定权威输入，而非按扩展名或修改时间擅选。生成后 `register --role test_cases` 绑定本次 PRD；PRD 改变使旧绑定失效，必须重新评估生成。旧技术方案不阻断 PRD-only 用例重写，但开发阶段仍核验设计。

## 套件根对象

标准 UTF-8 JSON，不含重复键、NaN、注释或尾逗号：

- `title`：非空标题。
- `status`：`探索草稿`、`待评审`、`已确认`；沿用实际确认范围，不冒充用例已执行。
- `prd`：含 `path`（任务内相对路径，不含 URL、绝对路径或上级跳转）、`sha256`（实际 64 位十六进制摘要）、`status`（上述文档状态）。
- `requirements`：非空数组，各项 `id`（REQ- 至少三位数字）、`title`、`status`（已确认/建议/待确认）、`source`（文件/原句/章节定位的非空说明）。
- `conditions`：非空数组，各项 `id`（AC- 至少三位数字）、`req_id`、`text`、`status`（已确认/建议/待确认）、`source`；原始验收编号非本格式时在 source 记录并用 AC 作为映射键。
- `cases`：非空数组，字段见下文。
- `coverage_gaps`：数组，可以为空；各项 `condition_id`、`reason`、`needed_input`。
- `type_notes`：非空数组，各项 `type`、`applicability`（适用/不适用/待确认）、`reason`；涵盖所有内置类型。

## 单条用例

- `id`：TC- 至少三位数字，全局唯一。
- `title`：具体目标。
- `type`：functional、boundary、negative、permission、security、api、state、compatibility、accessibility、performance、reliability、regression、acceptance。
- `level`：unit、integration、system、acceptance。
- `method`：scenario、equivalence、boundary_value、decision_table、state_transition、pairwise、error_guessing。
- `priority`：P0/P1/P2，`priority_reason` 必填。
- `req_ids`、`condition_ids`：非空引用数组，条件所属需求必须包含在 req_ids 中；不可引用不存在或不相关编号。
- `definition_status`：已确认/建议/待确认。任何引用的需求或条件是待确认时用例必须待确认；已确认用例只能引用已确认依据。
- `execution_status`：仅允许“未执行”。运行结果属于后续报告，不在生成阶段填 passed。
- `preconditions`、`data`、`assertions`：非空字符串数组。
- `steps`：非空数组，各项 `action` 和 `expected` 都是非空字符串；expected 写可观察结果。
- `cleanup`：非空说明，未改数据也说明无需清理及原因。
- `automation`：可自动化/需人工/待评估，`automation_reason` 非空。

“待确认”数据或预期必须把 definition_status 标待确认；JSON 结构校验不会自动推断所有语义缺口。已确认套件不能包含未确认需求、条件、用例或未解决覆盖缺口。

## 覆盖口径

每条 AC 条件必须关联至少一个 TC 或覆盖缺口；同条件可以同时存在候选用例与缺口，说明差距。每个 REQ 至少有一个 AC。type_notes 的适用类型应有用例；不适用类型不能塞入用例。待确认类型对应的用例必须待确认。

统计按明细计算：用例总数、各类型数量、可执行定义映射（已确认用例）、候选/待确认映射和缺口，不得把 TC 非空或结构通过称为全覆盖。

## 脚本与交付

`cases.py check` 返回 passed、errors、summary；0 为结构通过，1 为不合格，2 为读写/参数错误。它不读取产品、不执行测试，仍须人工校验预期与 PRD 等价。

`cases.py render` 先校验再输出 Markdown 文档；默认拒绝覆盖，`--force` 仅用于更新本次产物。自由文本不执行 HTML、链接或代码，Markdown 转义，按独立字段组织，避免超宽表格；未知规则在正文可见。

实际用例 JSON 与 Markdown 放同任务目录（默认 outputs 内），任务材料不随公开源码提交。用户另要在线文档或特定格式时使用宿主能力，不声称脚本自带转换。

完整交付需 PRD 依据、测试类型适用说明、所有可执行字段、需求与条件映射、覆盖缺口及未执行说明。只给类型目录、框架或少数示范用例不算完成用户的测试用例设计需求。
