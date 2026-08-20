from typing import Any, Dict, List, Tuple
import re

def checker_reg(qasm_str: str) -> str:
    """
    通用检查器 1：防御性检查并补全 OpenQASM 2.0 的 qreg 和 creg 声明。
    如果缺少声明，自动动态解析使用的寄存器名及最大 index 进行补全。
    """
    res = qasm_str.strip()

    # 1. 解析已声明的 qreg / creg 名称
    declared_qregs = set(re.findall(r"\bqreg\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\[\d+\];", res))
    declared_cregs = set(re.findall(r"\bcreg\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\[\d+\];", res))

    # 2. 从门指令（如 h q[0]; cx q[0], q[1];）中扫描使用到的寄存器和下标
    used_q_matches = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\[(\d+)\]", res)

    # 过滤关键字并收集未声明的量子寄存器
    undeclared_q = {}
    for name, idx in used_q_matches:
        if name not in declared_qregs and name not in declared_cregs and name not in ["creg", "qreg", "measure"]:
            idx = int(idx)
            undeclared_q[name] = max(undeclared_q.get(name, -1), idx)

    # 3. 如果有未声明的 qreg，自动补齐
    if undeclared_q:
        q_decls = "\n".join([f"qreg {reg_name}[{max_idx + 1}];" for reg_name, max_idx in undeclared_q.items()])
        # 优先插入到 include 之后，若无 include 则插在 OPENQASM 2.0; 之后
        if 'include "qelib1.inc";' in res:
            res = re.sub(r'(include "qelib1.inc";)', r'\1\n' + q_decls, res)
        elif "OPENQASM 2.0;" in res:
            res = re.sub(r'(OPENQASM\s+2\.0;)', r'\1\n' + q_decls, res)
        else:
            res = q_decls + "\n" + res

    # 4. 检查 creg，若完全没有 creg，则补充对应的 creg c[N];
    if not declared_cregs:
        # 寻找最大的量子比特数作为默认经典寄存器长度
        all_q_sizes = [max_idx + 1 for max_idx in undeclared_q.values()]
        # 如果已有声明的 qreg，也把它们的大小算进来
        qreg_sizes = [int(s) for s in re.findall(r"\bqreg\s+\w+\s*\[(\d+)\];", res)]
        max_size = max(all_q_sizes + qreg_sizes) if (all_q_sizes + qreg_sizes) else 2

        c_decl = f"creg c[{max_size}];"
        # 插入在最后一个 qreg 声明的后面
        if re.search(r"\bqreg\s+.*?;", res):
            res = re.sub(r"(\bqreg\s+.*?;)", r"\1\n" + c_decl, res, count=1)
        else:
            res = res + "\n" + c_decl

    return res


def checker_measure(qasm_str: str) -> str:
    """
    通用检查器 2：防御性检查是否存在测量语句。
    若缺失，自动读取当前 qreg 和 creg 并补充 measure q[i] -> c[i];
    """
    res = qasm_str.strip()

    # 如果已经有 measure 语句，直接返回
    if "measure" in res:
        return res

    # 提取第 1 个 qreg 和第 1 个 creg 的名字和大小
    qreg_match = re.search(r"\bqreg\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\[(\d+)\];", res)
    creg_match = re.search(r"\bcreg\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\[(\d+)\];", res)

    if qreg_match and creg_match:
        q_name, q_size = qreg_match.group(1), int(qreg_match.group(2))
        c_name, c_size = creg_match.group(1), int(creg_match.group(2))
        
        num_measures = min(q_size, c_size)
        measures = "\n" + "\n".join([f"measure {q_name}[{i}] -> {c_name}[{i}];" for i in range(num_measures)])
        res = res + measures

    return res
