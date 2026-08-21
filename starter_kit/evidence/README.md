# LoomQ 人工评分证据

这份文件是人工评分材料的统一入口。请直接编辑它，只填写要申报的项目。截图、原始结果或图表统一放在 `starter_kit/evidence/files/`，也可以引用 `starter_kit/` 中已有的代码和文档。

证据包是可选的。没有申报某项人工分时，留空即可，不影响自动评分。

## 提交前填写

把要申报项目的方框改成 `[x]`，并填写对应内容：

- [x] L1 真机
- [ ] L2 交互体验
- [ ] 工程与产品化
- [ ] 自定义量子 RISC-V Bonus
- [ ] 新手引导与视觉叙事 Bonus

## L1 真机

每个有效真机平台计 5 分，最多两个平台。模拟器不计真机分。每个平台复制并填写一次下面的信息：

### SpinQ
**平台名称**：量旋云
**平台 job ID**：S-260820-0010
**运行时间**：2026-08-20T06:47:33.235567Z
**shots**：8192
**实际执行的 QASM**：[files/spinq-circuit.qasm](./files/spinq-circuit.qasm)
**平台返回的原始结果**：[files/S-260820-0010_raw.json](./files/S-260820-0010_raw.json)
**任务页截图**：[files/spinq-screenshot.png](./files/spinq-screenshot.png)

### OriginQ
**平台名称**：本源量子
**平台 job ID**：959CD11FB04417BF96280FCA8AEE7D5E
**运行时间**：2026-08-21T01:12:40.984267Z
**shots**：8192
**实际执行的 QASM**：[files/originq-circuit.qasm](./files/originq-circuit.qasm)
**平台返回的原始结果**：[files/originq_959CD11FB04417BF96280FCA8AEE7D5E_raw.json](./files/originq_959CD11FB04417BF96280FCA8AEE7D5E_raw.json)
**任务页截图**：[files/originq-screenshot.png](./files/originq-screenshot.png)

**非对称电路测试结果：**
**平台名称**：本源量子
**平台 job ID**: EA3F5364AE4741D0DD9B19F918E3F78D
**shots**: 200
**实际执行的 QASM**：[files/originq-asymmetrical-circuit.qasm](./files/originq-asymmetrical-circuit.qasm)
**平台返回的原始结果**：[files/originq_EA3F5364AE4741D0DD9B19F918E3F78D_raw.json](./files/originq_EA3F5364AE4741D0DD9B19F918E3F78D_raw.json)
**任务页截图**：[files/originq-asymmetrical-screenshot.png](./files/originq-asymmetrical-screenshot.png)

工作人员会核对 job ID、运行时间、电路、shots 和原始结果。截图只能辅助说明，不能代替 job ID 和原始结果。

## L2 交互体验

请填写：

```text
启动界面或 CLI 的命令：[填写]
测试入口或页面地址：[填写，没有则写“无”]
适合现场体验的 3 个用户任务：
1. [填写]
2. [填写]
3. [填写]
截图或演示视频：[选填，填写仓库内路径或稳定只读链接]
```

工作人员会在组委会统一模型环境中运行最终代码，测试新手是否看得懂、出错后能否得到有效帮助、结果是否清楚，以及多轮回答是否一致。选手自己的对话截图只用于说明产品流程，不直接证明得分。

## 工程与产品化

已有内容可以直接引用主 README 或其他项目文档，不必复制到本目录。

```text
干净环境中的构建和启动命令：[填写命令或文档路径]
架构说明：[填写文档路径，或用几句话说明主要模块]
目标用户和使用场景：[填写]
完整使用流程：[填写文档、截图或演示路径]
```

工作人员会按最终 commit 实际构建和启动，并检查文档与代码是否一致、产品是否真的降低了量子计算的使用门槛。

## 自定义量子 RISC-V Bonus

以下三项必须齐全且测试通过，才获得 8 分：

```text
指令编码规格：[填写文档路径]
模拟器扩展实现：[填写代码路径]
端到端测试命令：[填写命令或文档路径]
```

## 新手引导与视觉叙事 Bonus

请填写已有材料的路径，不要求为评分另写一套文档：

```text
零基础首次运行指南：[填写]
量子概念解释：[填写]
结果可视化：[填写]
错误恢复或无障碍引导：[填写]
```

以上四项各 1 分。普通项目 README 完整不代表自动获得 Bonus。

## 提交规则

- 所有材料都要在截止前进入最终提交的 commit，工作人员不接受截止后补交。
- 外部视频可以用稳定只读链接，源码、原始结果和复现命令应保存在仓库中。
- 整个 fork commit 的归档包不得超过 100 MiB。
- 不要提交 API Key、Token、Cookie、个人身份信息或平台账户隐私。
- 如申报 L1 真机分，在最终提交 Issue 的 `Hardware evidence` 中填写 `starter_kit/evidence/README.md`。
