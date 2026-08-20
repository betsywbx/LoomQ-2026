#!/usr/bin/env python3
"""L2 智能体多场景黑盒测试集（带 Rate-Limit 避让保护）"""

import time
import re
from adapter import agent_chat

TEST_CASES = [
    # ------------------ 场景 1：自然语言意图生成 ------------------
    {
        "type": "生成",
        "prompt": "帮我生成一个 3 比特的最大纠缠态 (GHZ 态) 电路，并测量所有量子比特。",
        "check": "qasm",
    },
    {
        "type": "生成",
        "prompt": "我需要一个 2 比特的 Bell 态 |Ψ+⟩ (即 (|01⟩ + |10⟩) / √2) 电路，请用标准的 OpenQASM 2.0 输出。",
        "check": "qasm",
    },
    {
        "type": "生成",
        "prompt": "创建一个包含 4 个量子比特的电路，对第 0 位作用 H 门，然后依次用 CNOT 门将第 0 位与第 1、2、3 位纠缠，最后全测量。",
        "check": "qasm",
    },

    # ------------------ 场景 2：代码纠错与修复 ------------------
    {
        "type": "纠错",
        "prompt": "我想制备一个贝尔态，但这段代码报错了，帮我修好：H q[0]; CX q[0] q[1] (提示：语法大小写错误且未定义寄存器)",
        "check": "qasm",
    },
    {
        "type": "纠错",
        "prompt": "检查并修正以下 OpenQASM 代码：\nOPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\nh q[0];\ncu1(pi/2) q[0], q[1];\nmeasure q[0] -> c[0];\n（错误：缺失 creg 声明，且使用了未声明的经典寄存器 c[0]）",
        "check": "qasm",
    },

    # ------------------ 场景 3：智能选后端 ------------------
    {
        "type": "选后端",
        "prompt": "我需要运行一个 15 比特的电路，且希望零排队等待，推荐哪个后端？",
        "expected_ids": ["braket_local_simulator", "originq_local_simulator", "spinq_taurus_simulator"],
        "check": "backend",
    },
    {
        "type": "选后端",
        "prompt": "我想在一个超导量子真机上面跑电路，要求至少有 50 个量子比特，费用免费，应该选择哪一个？",
        "expected_ids": ["originq_wukong"],
        "check": "backend",
    },
    {
        "type": "选后端",
        "prompt": "我需要跑一个 100 比特的量子电路，有哪个后端可以满足？",
        "expected_no_backend": True,
        "check": "backend_none",
    },
]

def safe_agent_chat(prompt: str, retries: int = 3) -> str:
    """带有 HTTP 429 降级重试逻辑的请求包装器"""
    for attempt in range(retries):
        try:
            return agent_chat(prompt)
        except Exception as e:
            if "429" in str(e) and attempt < retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"⚠️ 触发 API 频率限制 (429)，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                raise e

def run_tests():
    passed = 0
    total = len(TEST_CASES)

    print(f"🚀 开始测试 {total} 个 L2 智能体用例...\n" + "="*50)

    for i, case in enumerate(TEST_CASES, 1):
        prompt = case["prompt"]
        c_type = case["type"]
        print(f"\n[Case {i}/{total}] 类型: {c_type}")
        print(f"输入: {prompt}")

        try:
            # 使用带有重试保护的函数，并在 case 间挂起 2 秒
            response = safe_agent_chat(prompt)
            print(f"输出:\n{response}\n" + "-"*30)

            # 校验逻辑
            if case["check"] == "qasm":
                if "OPENQASM 2.0;" in response:
                    print("✅ 结果校验成功：包含 OpenQASM 2.0 头！")
                    passed += 1
                else:
                    print("❌ 结果校验失败：未找到有效 OpenQASM 2.0 代码！")

            elif case["check"] == "backend":
                found = any(b_id in response for b_id in case["expected_ids"])
                if found:
                    print(f"✅ 结果校验成功：包含预期后端 ID ({case['expected_ids']})！")
                    passed += 1
                else:
                    print(f"❌ 结果校验失败：未在回复中找到规范后端 ID！")

            elif case["check"] == "backend_none":
                if any(kw in response for kw in ["没有", "无法满足", "不满足", "超限"]):
                    print("✅ 结果校验成功：正确识别出无法满足约束！")
                    passed += 1
                else:
                    print("❌ 结果校验失败：未对超限约束做出明确拒绝提示！")

        except Exception as e:
            print(f"❌ 执行抛出异常: {e}")

        # 请求间隔，防止 429
        time.sleep(2)

    print("\n" + "="*50)
    print(f"📊 测试完成：通过 {passed}/{total} (通过率: {passed/total*100:.1f}%)")

if __name__ == "__main__":
    run_tests()