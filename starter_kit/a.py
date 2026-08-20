#!/usr/bin/env python3
import json
from targets.braket import transpile_braket, run_braket

# 覆盖全部 12 个白名单门的 OpenQASM 2.0 测试用例
ALL_12_GATES_QASM2 = """OPENQASM 2.0;
include "qelib1.inc";

qreg q[3];
creg c[3];

h q[0];
x q[1];
s q[2];
sdg q[0];
t q[1];
tdg q[2];
rz(1.570796) q[0];
ry(3.141592) q[1];
cx q[0], q[1];
cu1(0.785398) q[1], q[2];
swap q[0], q[2];
ccx q[0], q[1], q[2];

measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
"""

def test_braket_backend():
    print("==================================================")
    print("🚀 开始测试 Braket 后端：12 门全量转译与模拟")
    print("==================================================\n")

    # 1. 验证静态转译输出
    qasm3_output = transpile_braket(ALL_12_GATES_QASM2)
    print("--- 1. 静态转译结果 (Target IR) ---")
    print(qasm3_output)
    print("------------------------------------\n")

    # 检查关键语法替换
    assert "OPENQASM 3.0;" in qasm3_output, "❌ 缺少 OPENQASM 3.0 头声明"
    assert 'include "stdgates.inc";' in qasm3_output, "❌ 缺少 include stdgates.inc"
    assert "qubit" in qasm3_output, "❌ 寄存器 qreg 未成功转译为 qubit"
    assert "bit" in qasm3_output, "❌ 寄存器 creg 未成功转译为 bit"
    assert "cphase(" in qasm3_output and "cu1(" not in qasm3_output, "❌ cu1 门未正确替换为 cphase"
    print("✅ 静态语法与契约检查 100% 通过！\n")

    # 2. 验证动态运行输出
    print("--- 2. 模拟器运行结果 (Schema JSON) ---")
    res = run_braket(ALL_12_GATES_QASM2, shots=1000)
    print(json.dumps(res, indent=2))
    
    assert res["backend"] is not None, "❌ 返回结果缺少 backend 字段"
    assert "counts" in res and len(res["counts"]) > 0, "❌ 未成功获取测量 counts"
    assert res["bit_order"] == "little", "❌ bit_order 必须归一化为 little"
    
    print("\n✅ 全量 12 门电路运行成功，格式完全符合统一 Schema！")

if __name__ == "__main__":
    test_braket_backend()