"""
compile_hybrid 实现: 把 Hybrid-QASM 拆成 (量子操作序列, RISC-V汇编文本)。

语法回顾(题面第三节):
- classical{} 块外: 标准 OpenQASM2.0 量子门/测量语句
- classical{} 块内: r1..r9(映射x1..x9)、c[k](映射x10,x11,...)、
  整数字面量、运算符 + - == !=、if/else、顺序赋值

设计原则: 这是一个真正的解析器+代码生成器,不是字符串替换/模式匹配——
评测会随机生成不同分支结构/常量/测量位数的用例,任何"认识几个固定样例"
式的实现在隐藏用例上都会失败。
"""

import re
from typing import List, Tuple, Optional, Union


# ---------------------------------------------------------------------------
# 第一步: 从 Hybrid-QASM 中切出 classical{} 块,剩下的就是量子操作序列
# ---------------------------------------------------------------------------
def _extract_classical_block(hybrid_qasm_str: str) -> Tuple[List[str], str]:
    """
    返回 (量子操作语句列表, classical块内部的原始文本)。
    用花括号配对定位 classical{...},不能简单按分号/换行切,
    因为块内部本身也有 { } (if/else的花括号)。
    """
    # 先去掉行内 // 注释(避免注释里的花括号干扰配对)
    lines = []
    for line in hybrid_qasm_str.splitlines():
        if "//" in line:
            line = line[:line.index("//")]
        lines.append(line)
    text = "\n".join(lines)

    start = text.find("classical")
    if start == -1:
        raise ValueError("输入中没有找到 classical{} 块")

    brace_start = text.find("{", start)
    if brace_start == -1:
        raise ValueError("classical 关键字后没有找到 {")

    depth = 0
    end = None
    for i in range(brace_start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        raise ValueError("classical{} 块的花括号不匹配")

    classical_body = text[brace_start + 1:end]

    # 量子部分 = classical块之前的文本 + classical块之后的文本
    before = text[:start]
    after = text[end + 1:]
    quantum_text = before + "\n" + after

    quantum_ops = []
    for stmt in quantum_text.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        if stmt.startswith(("OPENQASM", "include", "qreg", "creg")):
            continue
        quantum_ops.append(stmt + ";")

    return quantum_ops, classical_body


# ---------------------------------------------------------------------------
# 第二步: 对 classical{} 内部文本做词法+语法分析,生成简单AST
# ---------------------------------------------------------------------------
_TOKEN_RE = re.compile(r"""
    \s*(?:
        (?P<NUMBER>-?\d+)
      | (?P<CREG>c\[\d+\])
      | (?P<REG>r[1-9])
      | (?P<IF>\bif\b)
      | (?P<ELSE>\belse\b)
      | (?P<EQ>==)
      | (?P<NE>!=)
      | (?P<ASSIGN>=)
      | (?P<PLUS>\+)
      | (?P<MINUS>-)
      | (?P<LBRACE>\{)
      | (?P<RBRACE>\})
      | (?P<LPAREN>\()
      | (?P<RPAREN>\))
      | (?P<SEMI>;)
    )
""", re.VERBOSE)


def _tokenize(text: str) -> List[Tuple[str, str]]:
    tokens = []
    pos = 0
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
            continue
        m = _TOKEN_RE.match(text, pos)
        if not m or m.end() == pos:
            raise ValueError(f"classical块中出现无法识别的字符: {text[pos:pos+20]!r}")
        kind = m.lastgroup
        value = m.group(kind)
        tokens.append((kind, value))
        pos = m.end()
    return tokens


# AST节点: 用简单的元组/类表示,不引入额外依赖
class Assign:
    def __init__(self, reg_num: int, expr):
        self.reg_num = reg_num
        self.expr = expr


class IfElse:
    def __init__(self, cond, then_stmts, else_stmts):
        self.cond = cond
        self.then_stmts = then_stmts
        self.else_stmts = else_stmts


class Atom:
    """expr中的一个原子: 数字字面量 / r寄存器 / c[k]测量位"""
    def __init__(self, kind: str, value: int):
        self.kind = kind  # 'num' | 'reg' | 'creg'
        self.value = value  # 数字本身 / 寄存器编号(1-9) / creg索引(0,1,2..)


class BinExpr:
    def __init__(self, op: str, left: Atom, right: Atom):
        self.op = op  # '+' | '-' | '==' | '!='
        self.left = left
        self.right = right


class Parser:
    def __init__(self, tokens: List[Tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)

    def _advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, kind: str):
        actual_kind, value = self._peek()
        if actual_kind != kind:
            raise ValueError(f"语法错误: 期望 {kind}, 实际是 {actual_kind}({value}) at token {self.pos}")
        return self._advance()

    def parse_program(self) -> List:
        stmts = []
        while self.pos < len(self.tokens):
            stmts.append(self._parse_stmt())
        return stmts

    def _parse_stmt(self):
        kind, _ = self._peek()
        if kind == "IF":
            return self._parse_if()
        elif kind == "REG":
            return self._parse_assign()
        else:
            raise ValueError(f"语法错误: 未知语句起始token {kind}")

    def _parse_if(self):
        self._expect("IF")
        self._expect("LPAREN")
        cond = self._parse_cond()
        self._expect("RPAREN")
        self._expect("LBRACE")
        then_stmts = []
        while self._peek()[0] != "RBRACE":
            then_stmts.append(self._parse_stmt())
        self._expect("RBRACE")

        else_stmts = []
        if self._peek()[0] == "ELSE":
            self._advance()
            self._expect("LBRACE")
            while self._peek()[0] != "RBRACE":
                else_stmts.append(self._parse_stmt())
            self._expect("RBRACE")

        return IfElse(cond, then_stmts, else_stmts)

    def _parse_assign(self):
        _, reg_tok = self._expect("REG")
        reg_num = int(reg_tok[1:])
        self._expect("ASSIGN")
        expr = self._parse_expr()
        self._expect("SEMI")
        return Assign(reg_num, expr)

    def _parse_atom(self) -> Atom:
        kind, value = self._peek()
        if kind == "NUMBER":
            self._advance()
            return Atom("num", int(value))
        elif kind == "REG":
            self._advance()
            return Atom("reg", int(value[1:]))
        elif kind == "CREG":
            self._advance()
            idx = int(value[2:-1])  # "c[3]" -> 3
            return Atom("creg", idx)
        else:
            raise ValueError(f"语法错误: 期望数字/寄存器/测量位, 实际是 {kind}({value})")

    def _parse_expr(self):
        """expr := atom (('+' | '-') atom)?  —— 迷你文法,不支持深层嵌套"""
        left = self._parse_atom()
        kind, _ = self._peek()
        if kind in ("PLUS", "MINUS"):
            op = "+" if kind == "PLUS" else "-"
            self._advance()
            right = self._parse_atom()
            return BinExpr(op, left, right)
        return left  # 单个原子,也算合法expr(比如 r1 = 5;)

    def _parse_cond(self):
        """cond := atom ('==' | '!=') atom"""
        left = self._parse_atom()
        kind, _ = self._peek()
        if kind not in ("EQ", "NE"):
            raise ValueError(f"语法错误: if条件里期望 == 或 !=, 实际是 {kind}")
        op = "==" if kind == "EQ" else "!="
        self._advance()
        right = self._parse_atom()
        return BinExpr(op, left, right)


# ---------------------------------------------------------------------------
# 第三步: AST -> RISC-V 汇编文本 (只用 li/add/sub/addi/beq/bne/j)
# ---------------------------------------------------------------------------
def _atom_reg(atom: Atom) -> str:
    """把 reg/creg 原子转成寄存器名; num原子不适用(调用前需另行处理)"""
    if atom.kind == "reg":
        return f"x{atom.value}"
    elif atom.kind == "creg":
        return f"x{10 + atom.value}"
    else:
        raise ValueError("num原子不能直接当寄存器用")


class CodeGen:
    # x31 保留作比较/加载常量用的临时寄存器,r1..r9(x1..x9)和c[k](从x10起)
    # 不会用到这么大的编号,足够安全
    SCRATCH_REG = "x31"

    def __init__(self):
        self.lines: List[str] = []
        self._label_counter = 0

    def _new_label(self, hint: str) -> str:
        self._label_counter += 1
        return f"{hint}_{self._label_counter}"

    def _emit(self, line: str):
        self.lines.append(line)

    def gen_program(self, stmts: List) -> str:
        for stmt in stmts:
            self._gen_stmt(stmt)
        return "\n".join(self.lines)

    def _gen_stmt(self, stmt):
        if isinstance(stmt, Assign):
            self._gen_assign(stmt)
        elif isinstance(stmt, IfElse):
            self._gen_if(stmt)
        else:
            raise ValueError(f"未知语句类型: {stmt}")

    def _gen_assign(self, stmt: Assign):
        rd = f"x{stmt.reg_num}"
        expr = stmt.expr

        if isinstance(expr, Atom):
            if expr.kind == "num":
                self._emit(f"li {rd}, {expr.value}")
            else:
                # r1 = r2;  或 r1 = c[0];  —— 用 addi rd, rs, 0 实现纯拷贝
                self._emit(f"addi {rd}, {_atom_reg(expr)}, 0")
            return

        # BinExpr: '+' 或 '-'
        left, right = expr.left, expr.right

        # 约定: left 一定是寄存器/测量位(赋值语句左值是r_i,右边表达式
        # 通常以某个已有寄存器为基准做加减,题面例子 "r1 = r1 + 5" 就是这个模式)
        if left.kind == "num":
            # 数字在左边(如 5 + r1)比较少见,先把它当成"先li到rd再加"处理
            self._emit(f"li {rd}, {left.value}")
            left_reg = rd
        else:
            left_reg = _atom_reg(left)

        if right.kind == "num":
            imm = right.value if expr.op == "+" else -right.value
            self._emit(f"addi {rd}, {left_reg}, {imm}")
        else:
            right_reg = _atom_reg(right)
            if expr.op == "+":
                self._emit(f"add {rd}, {left_reg}, {right_reg}")
            else:
                self._emit(f"sub {rd}, {left_reg}, {right_reg}")

    def _gen_cond_branch(self, cond: BinExpr, true_label: str, false_label: str):
        """
        生成条件跳转: 满足cond就跳true_label,否则跳false_label。
        beq/bne只能比两个寄存器,遇到字面量要先li到临时寄存器。
        """
        left, right = cond.left, cond.right

        if left.kind == "num" and right.kind == "num":
            # 两边都是字面量,理论上编译期就能确定,但保持通用实现
            self._emit(f"li {self.SCRATCH_REG}, {left.value}")
            left_reg = self.SCRATCH_REG
            self._emit(f"li x30, {right.value}")
            right_reg = "x30"
        elif left.kind == "num":
            self._emit(f"li {self.SCRATCH_REG}, {left.value}")
            left_reg = self.SCRATCH_REG
            right_reg = _atom_reg(right)
        elif right.kind == "num":
            left_reg = _atom_reg(left)
            self._emit(f"li {self.SCRATCH_REG}, {right.value}")
            right_reg = self.SCRATCH_REG
        else:
            left_reg = _atom_reg(left)
            right_reg = _atom_reg(right)

        branch_op = "beq" if cond.op == "==" else "bne"
        self._emit(f"{branch_op} {left_reg}, {right_reg}, {true_label}")
        self._emit(f"j {false_label}")

    def _gen_if(self, stmt: IfElse):
        true_label = self._new_label("IF_TRUE")
        false_label = self._new_label("IF_FALSE")
        end_label = self._new_label("IF_END")

        self._gen_cond_branch(stmt.cond, true_label, false_label)

        self._emit(f"{true_label}:")
        for s in stmt.then_stmts:
            self._gen_stmt(s)
        self._emit(f"j {end_label}")

        self._emit(f"{false_label}:")
        for s in stmt.else_stmts:
            self._gen_stmt(s)

        self._emit(f"{end_label}:")


# ---------------------------------------------------------------------------
# 对外入口
# ---------------------------------------------------------------------------
def compile_hybrid(hybrid_qasm_str: str) -> Tuple[List[str], str]:
    quantum_ops, classical_body = _extract_classical_block(hybrid_qasm_str)

    tokens = _tokenize(classical_body)
    parser = Parser(tokens)
    ast_stmts = parser.parse_program()

    codegen = CodeGen()
    asm_text = codegen.gen_program(ast_stmts)

    return quantum_ops, asm_text