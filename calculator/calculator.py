
def add(a, b):
    return float(a) + float(b)


def subtract(a, b):
    return float(a) - float(b)


def multiply(a, b):
    return float(a) * float(b)


def divide(a, b):
    b = float(b)
    if b == 0:
        raise ValueError("Деление на ноль запрещено")
    return float(a) / b


def calculate(expression: str) -> float:
    expr = expression.strip()

    import re
    match = re.match(r'^([+-]?\d*\.?\d+)\s*([+\-*/])\s*([+-]?\d*\.?\d+)$', expr)

    if not match:
        raise ValueError("формат не вереный")

    left_str, op, right_str = match.groups()

    try:
        left = float(left_str)
        right = float(right_str)
    except ValueError:
        raise ValueError("Некооректные числа")

    if op == '+':
        return add(left, right)
    elif op == '-':
        return subtract(left, right)
    elif op == '*':
        return multiply(left, right)
    elif op == '/':
        return divide(left, right)
    else:
        raise ValueError(f"Не коректная ошибка: {op}")