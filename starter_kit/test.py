import os
import json
from targets.originq import run_originq

GHZ3_QASM = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
h q[0];
cx q[0],q[1];
cx q[1],q[2];
measure q -> c;
"""

def test_originq():
    print("🚀 提交 GHZ-3 至本源量子云平台...")

    res = run_originq(GHZ3_QASM, shots=8192, use_hardware=True)

    print("\n✅ 归一化后的统一 schema 结果：")
    print(json.dumps(res, indent=2, ensure_ascii=False))

    os.makedirs("evidence", exist_ok=True)

    # 存统一schema版本(这是你 run_originq 实际返回的结果)
    with open("evidence/originq_ghz3_evidence.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    print(f"\n💾 证据已落盘至 evidence/originq_ghz3_evidence.json")
    print(f"📌 job_id (用于评委去控制台核验): {res['job_id']}")
    print(f"📌 backend: {res['backend']}")
    print(f"📌 timestamp: {res['timestamp']}")

if __name__ == "__main__":
    test_originq()