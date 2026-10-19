# 前置文档交接与缺失询问

## 单一任务范围

用户指定的任务目录是文档交接根，不假设技能仓库就是代码仓库。使用 `pipeline.json` 记录 PRD 与技术方案的当前权威文件，文件路径必须相对任务目录，无绝对路径、URL、`..`、跨目录符号链接。外部文档先用授权能力读全，若要进入本地清单，把完整且允许保存的输入副本放在任务目录并记来源，不擅自复制到别的项目。

用户明确输入比自动发现优先。用户指定一个失效文件时不能静默退回另一个文件。来自本轮上下文的确定交接可直接读，不必要求用户重发；清单存在时继续校验版本。文件同名或多个版本无法判断时先请用户确定。

没有清单时只在本次任务目录检查约定名：`prd.json`、`prd.md`、`prd.html`、`requirements.json`、`technical-design.json`、`technical-design.md`、`technical-design.html`、`design.json`，也可位于 `documents/` 或 `docs/`。同种文档多个候选就报告歧义，不按修改时间或优先扩展名擅选。HTML 与 JSON 若是同一文档的两个载体，先明确 JSON 为权威输入并登记；不能仅靠名称推断两者完全等价。

禁止将仓库 `skills/*/assets/` 示例或其他任务目录文档作为真实默认输入。自动读取只是降低重复提供材料的成本，不代替范围授权。

## pipeline.json 结构

清单使用标准 UTF-8 JSON：

```json
{
  "schema_version": 1,
  "task": "reminder-demo",
  "artifacts": {
    "prd": {
      "path": "prd.json",
      "sha256": "文件实际摘要",
      "producer": "requirement-analysis",
      "status": "待评审"
    },
    "technical_design": {
      "path": "technical-design.json",
      "sha256": "文件实际摘要",
      "producer": "technical-design",
      "status": "待评审",
      "prd_sha256": "生成设计时读取的 PRD 摘要"
    }
  }
}
```

摘要示意字符串不能照抄；脚本登记时从真实文件计算 64 位十六进制摘要。producer 允许 `requirement-analysis`、`technical-design` 和 `user`，且与角色匹配。状态允许 `探索草稿`、`待评审`、`已确认`，沿用原文，不因哈希匹配升级。

根的 task 用语义任务名，同一清单不跨任务改名。更新 PRD 会使旧 technical_design 绑定失效；清单保留其旧摘要作为阻断证据，resolve 必须报错，不能再从同名旧文件自动发现并放行。重新评估或生成设计并登记新的绑定后才可继续。其他文件不删除。更新清单采用同目录临时文件原子替换，不并发写；多 Agent 写入须由宿主串行协调。

## 命令

先用 `--help` 确认；把路径占位换成实际值，含空格需引用。

```bash
python3 <开发技能目录>/scripts/pipeline.py register --task-dir <任务目录> --task <任务名> --role prd --file prd.json --status 待评审 --producer requirement-analysis
python3 <开发技能目录>/scripts/pipeline.py register --task-dir <任务目录> --task <任务名> --role technical_design --file technical-design.json --status 待评审 --producer technical-design
python3 <开发技能目录>/scripts/pipeline.py resolve --task-dir <任务目录>
```

用户单独指定材料可使用 `resolve --task-dir <任务目录> --prd <相对文件> --design <相对文件>`。显式指定前置不要求清单，但如果与清单有同一输入的版本记录，会校验；无设计绑定时报告 `version_link: unverified`，Agent 必须读全文核对来源和 REQ/DES，然后再登记或记录人工核验，不声称版本自动一致。

只有 PRD 时 register 允许先登记；resolve 返回缺技术方案。登记技术方案时必须有已登记且未变的 PRD；不给虚假的独立版本绑定。源码不会加载另两个技能，也不会写 PRD、技术方案或产品代码。

resolve 返回：

- `ready`，退出 0：文件可读、摘要未变化，已登记绑定一致或明确提示未绑定；只通过文件门禁，不是开发批准。
- `needs_input`，退出 1：缺文档或多个候选，含角色和相对候选路径。由 Agent 询问用户，不自动生成。
- `invalid`，退出 2：路径越界、坏 JSON/清单、摘要不一致、设计基于旧 PRD、显式文件不存在、角色或状态非法。修复原因后再继续，不能绕过清单覆盖错误。

输出不给本机绝对路径或用户标识；内容仍由 Agent 按返回路径完整读取，脚本只读 bytes/校验基本 JSON，不执行文档代码。非 JSON 载体由宿主对应能力解读，不把空白文件、文件大小或扩展名当语义有效。

## PRD-only 与测试用例交接

测试用例设计只要求 PRD：`resolve --only-prd --task-dir <任务目录>` 只读取本次 PRD，缺失或歧义仍返回 needs_input，不因没有技术方案而阻断。清单结构错误与 PRD 摘要变化仍报 invalid；旧技术方案或旧测试用例绑定不影响基于新 PRD 重新设计用例。文件核验不等于业务确认。

清单 artifacts 还允许 `test_cases`，字段为 path、sha256、producer、status、prd_sha256，producer 为 test-case-design 或 user。`register --role test_cases --file test-cases.json` 必须先登记 PRD，并核对用例 JSON 内 `prd.path/sha256` 与当前 PRD 一致；状态沿用用例套件。

开发的普通 resolve 仍要求 PRD 和技术方案，若同任务已登记 test_cases 则一起读取并核验版本，用于实施与测试映射。未登记用例不自动强制要求；已登记但过期、丢失或内容变化不能静默跳过。PRD 更新后旧设计与用例绑定保留为失效证据，重新评估登记才继续。

## 缺文档时的交互

完成有限只读定位后，若缺任何文档：

1. 准确指出缺 PRD、技术方案或两份；有已有材料不重复请求。
2. 问“是否先帮你完善缺少的文档，确认范围后再开始开发？”并说明也可使用现有文档。
3. 等待用户选择。用户同意才进入对应前置技能，用户拒绝就停止开发。
4. 选已有文档时，自由输入有效链接、路径或附件；不存在的引用按材料缺失处理。
5. 缺目标项目、技术栈、关键规则时与本轮相关阻断一次问清，不为了方便默认栈。

无需把补写许可升级为设计批准。先依据 requirement-analysis 产出/修订 PRD，再依据它用 technical-design 产出/修订设计。两份之间冲突或关键规则待确认时暂停相关实现，文档可交探索稿，不声称已实施。

## 更新与输出

前置技能只登记用户明确要求端到端或后续开发的本次结果；单独生成文档不自动开发。开发阶段在 delivery.md 记录输入摘要与实际核验，不擅自把清单状态改成已确认。

任务目录和 outputs 默认忽略提交，避免用户业务文档、绝对路径与运行报告进入公开仓库。提交授权不能自动包含这些文件；公开代码前须检查实际暂存集合。
