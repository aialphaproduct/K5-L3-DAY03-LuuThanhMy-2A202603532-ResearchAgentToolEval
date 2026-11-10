from __future__ import annotations

import ast
import operator
from typing import Any

from tools._shared import err

# Only these operators are allowed. Anything else (names, calls, attributes)
# is rejected, so the tool can never execute arbitrary Python.
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError("Chỉ cho phép số")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Biểu thức không được hỗ trợ (chỉ số học cơ bản)")


def calculate(expression: str = "") -> dict[str, Any]:
    """Tính một biểu thức số học cơ bản (+ - * / // % ** và ngoặc).

    An toàn: không dùng eval() của Python, chỉ duyệt AST các phép toán cho phép,
    nên không thể chạy mã tuỳ ý. Đầu vào xấu trả về dict lỗi, không raise.
    """
    try:
        expr = (expression or "").strip()
        if not expr:
            raise ValueError("Biểu thức rỗng")
        tree = ast.parse(expr, mode="eval")
        result = _eval(tree.body)
        return {"tool": "calculate", "expression": expr, "result": result}
    except Exception as exc:  # noqa: BLE001 — lỗi là bằng chứng, trả dict thay vì raise
        return err("calculate", exc)
