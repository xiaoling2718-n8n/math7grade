import streamlit as st
import random
import re
from fractions import Fraction
import math
from decimal import Decimal, ROUND_HALF_UP
# 页面配置
st.set_page_config(
    page_title="数学闯关·有理数计算",
    page_icon="⚔️",
    layout="centered"
)

# ---------- 初始化 session 状态 ----------
if "stage" not in st.session_state:
    st.session_state.stage = 0
if "question" not in st.session_state:
    st.session_state.question = None
if "steps" not in st.session_state:
    st.session_state.steps = []
if "current_step_index" not in st.session_state:
    st.session_state.current_step_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "monster_defeated" not in st.session_state:
    st.session_state.monster_defeated = False
if "feedback" not in st.session_state:
    st.session_state.feedback = ""
if "done" not in st.session_state:
    st.session_state.done = False
if "penalty" not in st.session_state:
    st.session_state.penalty = False
if "total_steps" not in st.session_state:
    st.session_state.total_steps = 0
if "original_expr" not in st.session_state:
    st.session_state.original_expr = ""
if "expected_steps" not in st.session_state:
    st.session_state.expected_steps = []
if "final_result" not in st.session_state:
    st.session_state.final_result = None
if "numbers" not in st.session_state:
    st.session_state.numbers = []
if "operators" not in st.session_state:
    st.session_state.operators = []

def format_fraction(value):
    value = Fraction(value)

    if value.denominator == 1:
        return str(value.numerator)

    return f"{value.numerator}/{value.denominator}"


def fraction_to_mixed(value):
    value = Fraction(value)

    if value.denominator == 1:
        return str(value.numerator)

    sign = "-" if value < 0 else ""
    value = abs(value)

    whole = value.numerator // value.denominator
    remainder = value.numerator % value.denominator

    if whole == 0:
        return f"{sign}{remainder}/{value.denominator}"

    if remainder == 0:
        return f"{sign}{whole}"

    return f"{sign}{whole} {remainder}/{value.denominator}"
    
def contains_decimal(expr):
    """
    判断表达式是否包含十进制小数。
    支持：
        1.5
        -1.5
        0.25
        .75
        -.75
        1.5 + 2/3
        (1.25 - 0.5) * 2
    """
    if not expr:
        return False

    expr = str(expr)

    pattern = r'(?<![\w.])-?(?:\d+\.\d+|\.\d+)'
    return re.search(pattern, expr) is not None
    
def round_decimal_3(value):
    """
    按数学常规四舍五入到小数点后3位
    """
    return Decimal(str(float(value))).quantize(
        Decimal("0.001"),
        rounding=ROUND_HALF_UP
    )
# ---------- 带分数处理函数 ----------
def is_mixed_number(expr):
    """
    判断是否是带分数格式（整数 分子/分母）
    例如：3 55/300, -1 2/3, 4 1/2, 1 1/6
    """
    expr = expr.strip()
    # 匹配格式：整数 空格 分子/分母
    pattern = r'^-?\d+\s+\d+/\d+$'
    return bool(re.match(pattern, expr))

def convert_mixed_to_improper(expr):
    """
    带分数 -> 假分数

    例如：
        4 1/2   -> 9/2
        -1 2/3  -> -5/3
        1 1/6   -> 7/6
    """
    expr = expr.strip()

    if not is_mixed_number(expr):
        return None, "不是带分数格式"

    parts = expr.split()

    if len(parts) != 2:
        return None, "格式错误"

    try:
        whole = int(parts[0])

        num, den = parts[1].split('/')
        num = int(num)
        den = int(den)

        if den <= 0:
            return None, "分母必须大于0"

        if num < 0:
            return None, "带分数的分子不能为负数"

        if num >= den:
            return None, f"{num}/{den} 不是真分数"

        # 正带分数
        if whole >= 0:
            result = Fraction(
                whole * den + num,
                den
            )

        # 负带分数
        else:
            result = Fraction(
                -(abs(whole) * den + num),
                den
            )

        return result, f"{expr} = {result}"

    except ValueError as e:
        return None, f"数字格式错误：{e}"
def parse_mixed_number(expr):
    """解析带分数，返回对应的Fraction"""
    result, _ = convert_mixed_to_improper(expr)
    return result

def fraction_to_mixed(frac):
    """将假分数转换为带分数格式的字符串"""
    if not isinstance(frac, Fraction):
        return str(frac)
    
    frac = frac.limit_denominator()
    whole = frac.numerator // frac.denominator
    remainder = abs(frac.numerator) % frac.denominator
    
    if remainder == 0:
        return str(whole)
    elif whole == 0:
        return f"{frac.numerator}/{frac.denominator}"
    else:
        if whole < 0:
            return f"-{abs(whole)} {remainder}/{frac.denominator}"
        else:
            return f"{whole} {remainder}/{frac.denominator}"

def replace_mixed_numbers(expr):
    """
    将表达式中的所有带分数替换为假分数
    例如：'9 19/100+1 1/4-4' -> '(919/100)+(5/4)-4'
    """
    def replace_match(match):
        mixed = match.group(0)
        result, _ = convert_mixed_to_improper(mixed)
        if result is not None:
            # 返回分数格式，用括号括起来避免运算顺序问题
            return f"({result.numerator}/{result.denominator})"
        return mixed
    
    # 查找所有带分数模式：整数 空格 分子/分母
    # 注意：要匹配负号，但不匹配表达式中的减号
    pattern = r'-?\d+\s+\d+/\d+'
    replaced = re.sub(pattern, replace_match, expr)
    return replaced

def calculate_value(expr):
    """计算表达式的值，支持分数、小数和混合带分数"""
    try:
        # 第一步：替换所有带分数为假分数
        expr_without_mixed = replace_mixed_numbers(expr)
        
        namespace = {'Fraction': Fraction}
        
        def replace_fraction(match):
            num = int(match.group(1))
            den = int(match.group(2))
            return f"Fraction({num}, {den})"
        
        expr_eval = re.sub(r'(\d+)/(\d+)', replace_fraction, expr_without_mixed)
        # 移除所有空格（因为带分数已经被替换了）
        expr_eval = re.sub(r'\s+', '', expr_eval)
        
        result = eval(expr_eval, namespace)
        
        if isinstance(result, Fraction):
            result = result.limit_denominator()
        return result
    except Exception as e:
        try:
            # 如果替换带分数后计算失败，尝试直接计算
            expr_clean = re.sub(r'\s+', '', expr)
            result = eval(expr_clean)
            return result
        except:
            return None

def get_value_from_expr(expr):
    """
    从表达式中提取数值
    支持：单独的带分数、混合带分数的表达式
    """
    expr = expr.strip()
    return calculate_value(expr)

def is_equal(value1, value2, accept_rounding=True):
    """
    数值比较：

    - Fraction / int：精确比较
    - 涉及小数：按小数点后3位四舍五入比较
    """

    if value1 is None or value2 is None:
        return False

    try:
        # -----------------------------------------
        # 纯整数 / 分数：精确比较
        # -----------------------------------------
        if isinstance(value1, (int, Fraction)) and \
           isinstance(value2, (int, Fraction)):

            return value1 == value2

        # -----------------------------------------
        # 涉及小数：三位小数四舍五入
        # -----------------------------------------
        if accept_rounding:
            v1 = round_decimal_3(value1)
            v2 = round_decimal_3(value2)

            return v1 == v2

        # -----------------------------------------
        # 不允许四舍五入
        # -----------------------------------------
        return abs(float(value1) - float(value2)) < 1e-3

    except Exception:
        return False

def is_pure_number(expr):
    """判断表达式是否只是纯数字（没有运算符）"""
    expr_clean = expr.strip()
    pattern = r'^\-?\d+(\.\d+)?$|^\-?\d+/\d+$|^\-?\d+\s+\d+/\d+$'
    return bool(re.match(pattern, expr_clean))

def is_fraction_simplified(frac_str):
    """检查分数是否已经是最简形式"""
    if ' ' in frac_str:
        parts = frac_str.split()
        if len(parts) == 2:
            frac_part = parts[1]
            if '/' in frac_part:
                frac_parts = frac_part.split('/')
                if len(frac_parts) == 2:
                    try:
                        num = abs(int(frac_parts[0]))
                        den = int(frac_parts[1])
                        from math import gcd
                        return gcd(num, den) == 1
                    except:
                        pass
        return True
    
    if frac_str.startswith('-'):
        frac_str = frac_str[1:]
    
    if '/' not in frac_str:
        return True
    
    parts = frac_str.split('/')
    if len(parts) != 2:
        return False
    
    try:
        num = abs(int(parts[0].strip()))
        den = int(parts[1].strip())
        
        if den == 0:
            return False
        
        from math import gcd
        return gcd(num, den) == 1
    except:
        return False

# ---------- 生成裂项/拆项题目 ----------
def generate_fraction_sequence():
    """生成适合裂项或通分的分数序列"""
    question_type = random.choice(['fraction_series', 'fraction_ops', 'mixed_ops'])
    
    if question_type == 'fraction_series':
        length = random.randint(3, 5)
        numbers = []
        operators = []
        
        for i in range(length):
            if i == 0:
                denom = random.randint(1, 3)
                numbers.append(Fraction(1, denom * (denom + 1)))
            else:
                base = random.randint(2, 5)
                numbers.append(Fraction(1, base * (base + 1)))
            operators.append('+')
        
        operators = operators[:-1] if operators else []
        return numbers, operators
    
    elif question_type == 'fraction_ops':
        length = random.randint(4, 6)
        numbers = []
        operators = []
        
        denominators = []
        for i in range(length):
            if i == 0:
                den = random.randint(2, 8)
            else:
                den = random.randint(2, 8)
                while den in denominators:
                    den = random.randint(2, 8)
            denominators.append(den)
            
            numerator = random.randint(1, den - 1)
            if random.random() > 0.5:
                numerator = random.randint(1, den * 2)
            numbers.append(Fraction(numerator, den))
        
        for i in range(length - 1):
            operators.append(random.choice(['+', '-']))
        
        return numbers, operators
    
    else:  # mixed_ops
        length = random.randint(4, 6)
        numbers = []
        operators = []
        
        for i in range(length):
            if random.random() > 0.4:
                den = random.randint(2, 8)
                numerator = random.randint(1, den * 2)
                numbers.append(Fraction(numerator, den))
            else:
                numbers.append(random.randint(-8, 8))
            if i < length - 1:
                operators.append(random.choice(['+', '-']))
        
        return numbers, operators

def generate_question():
    """生成有理数混合运算题（支持多项和裂项）"""
    if random.random() > 0.3:
        numbers, operators = generate_fraction_sequence()
    else:
        num_count = random.randint(4, 6)
        numbers = []
        operators = []
        
        for i in range(num_count):
            if random.random() > 0.5:
                den = random.randint(2, 8)
                numerator = random.randint(1, den * 2)
                if random.random() > 0.6:
                    numerator = -numerator
                numbers.append(Fraction(numerator, den))
            else:
                if random.random() > 0.5:
                    numbers.append(random.randint(-10, 10))
                else:
                    num = random.randint(-10, 10) + random.randint(1, 99) / 100
                    numbers.append(round(num, 2))
            
            if i < num_count - 1:
                operators.append(random.choice(['+', '-']))
    
    # 构建显示表达式
    display_parts = []
    for num in numbers:
        display_parts.append(format_number_with_parenthesis(num))
    
    original_expr = ""
    for i in range(len(display_parts)):
        original_expr += display_parts[i]
        if i < len(operators):
            original_expr += f" {operators[i]} "
    
    # 计算最终结果
    final_result = numbers[0]
    for i in range(len(operators)):
        if operators[i] == '+':
            final_result += numbers[i+1]
        else:
            final_result -= numbers[i+1]
    
    if isinstance(final_result, Fraction):
        final_result = final_result.limit_denominator()
    
    return original_expr, numbers, operators, final_result

def format_number(num):
    """格式化数字为字符串"""
    if isinstance(num, Fraction):
        num = num.limit_denominator()
        if num.denominator == 1:
            return str(num.numerator)
        return f"{num.numerator}/{num.denominator}"
    elif isinstance(num, float):
        if num.is_integer():
            return str(int(num))
        return str(num)
    else:
        return str(num)

def format_number_with_parenthesis(num):
    """格式化数字，负数加括号"""
    if isinstance(num, Fraction):
        num = num.limit_denominator()
        if num < 0:
            return f"({format_number(num)})"
        return format_number(num)
    elif isinstance(num, float) or isinstance(num, int):
        if num < 0:
            return f"({num})"
        return str(num)
    else:
        if num < 0:
            return f"({num})"
        return str(num)

def validate_step(step_str, prev_expression, final_result, steps_so_far):
    """
    验证学生的计算步骤。

    学生只需要输入等号右边，例如：

        = 5/6
        = 1 1/2
        = 2.5
        = 3/4 + 1/2
        = (5/6) * 3/2

    程序自动把它理解为：

        上一步表达式 = 学生输入

    验证内容：
    1. 必须从 "=" 开始
    2. 等号后必须有内容
    3. 检查学生输入的右侧表达式是否合法
    4. 检查右侧表达式的数值是否与上一行相等
    5. 如果是最终纯数字，检查最终答案
    6. 最终分数/带分数必须最简
    """

    # ========================================================
    # 1. 基本格式检查
    # ========================================================

    step_str = step_str.strip()

    if not step_str:
        return False, "请输入计算结果，例如：= 5/6", False

    # 必须从等号开始
    if not step_str.startswith("="):
        return (
            False,
            "每一步只填写等号右边的内容，请从 '=' 开始，例如：= 5/6",
            False
        )

    # 只能有一个等号
    if step_str.count("=") != 1:
        return (
            False,
            "每一步只能有一个等号，例如：= 5/6",
            False
        )

    # 取等号右边
    right_side = step_str[1:].strip()

    if not right_side:
        return (
            False,
            "等号后面不能为空，请输入计算结果",
            False
        )

    # ========================================================
    # 2. 确定上一行的表达式
    # ========================================================

    if steps_so_far:
        # 上一步学生输入的是：
        # = 5/6
        #
        # 所以上一步的结果就是：
        # 5/6
        last_step = steps_so_far[-1].strip()

        if last_step.startswith("="):
            previous_value_expr = last_step[1:].strip()
        else:
            # 兼容旧数据
            previous_value_expr = last_step.strip()

        current_left_expr = previous_value_expr

    else:
        # 第一步：
        # 原题 = 学生输入
        current_left_expr = prev_expression

    # ========================================================
    # 3. 计算当前左侧（上一行结果）
    # ========================================================

    left_value = get_value_from_expr(current_left_expr)

    if left_value is None:
        return (
            False,
            f"无法计算上一结果：{current_left_expr}",
            False
        )

    # ========================================================
    # 4. 计算学生输入的右侧
    # ========================================================

    right_value = get_value_from_expr(right_side)

    if right_value is None:
        return (
            False,
            f"无法识别你的计算结果：{right_side}",
            False
        )

    # ========================================================
    # 5. 判断是否使用小数
    #
    # 只要当前左右任意一侧包含小数，
    # 就允许按小数点后3位四舍五入。
    # ========================================================

    use_rounding = (
        contains_decimal(current_left_expr)
        or contains_decimal(right_side)
    )

    # ========================================================
    # 6. 检查：
    #
    # 上一步结果 == 学生本步骤结果
    # ========================================================

    if not is_equal(
        left_value,
        right_value,
        use_rounding
    ):
        return (
            False,
            f"计算错误！\n\n"
            f"上一结果：{fraction_to_mixed(left_value)}\n\n"
            f"你的结果：{fraction_to_mixed(right_value)}",
            False
        )

    # ========================================================
    # 7. 判断学生输入的是不是“最终结果”
    #
    # 例如：
    #
    # = 5/6
    # = 1 1/2
    # = 2.5
    #
    # 而：
    #
    # = 1/2 + 1/3
    #
    # 仍然是中间步骤。
    # ========================================================

    if is_pure_number(right_side):

        # ----------------------------------------------------
        # 7.1 检查最终答案
        # ----------------------------------------------------

        use_rounding = contains_decimal(right_side)

        if not is_equal(
            right_value,
            final_result,
            use_rounding
        ):
            return (
                False,
                f"最终结果错误。\n\n"
                f"正确答案：{fraction_to_mixed(final_result)}\n"
                f"假分数：{format_fraction(final_result)}\n"
                f"小数：≈ {fraction_to_decimal(final_result, 3)}",
                False
            )

        # ----------------------------------------------------
        # 7.2 如果是分数/带分数，必须最简
        # ----------------------------------------------------

        if "/" in right_side:

            if not is_fraction_simplified(right_side):

                simplified = format_fraction(right_value)
                mixed = fraction_to_mixed(right_value)

                return (
                    True,
                    f"数值正确！但分数还没有约分到最简。\n\n"
                    f"请继续约分为：{simplified}"
                    + (
                        f"（带分数：{mixed}）"
                        if right_value.denominator != 1
                        else ""
                    ),
                    False
                )

        # ----------------------------------------------------
        # 7.3 最终正确
        # ----------------------------------------------------

        return (
            True,
            "🎉 最终结果正确！",
            True
        )

    # ========================================================
    # 8. 中间步骤
    # ========================================================

    if "/" in right_side:

        if not is_fraction_simplified(right_side):

            simplified = format_fraction(right_value)

            return (
                True,
                f"步骤正确！可以继续约分为：{simplified}",
                False
            )

    return (
        True,
        "✅ 步骤正确！",
        False
    )
# ---------- 重置游戏 ----------
def reset_game():
    st.session_state.stage = 0
    st.session_state.question = None
    st.session_state.steps = []
    st.session_state.current_step_index = 0
    st.session_state.score = 0
    st.session_state.monster_defeated = False
    st.session_state.feedback = ""
    st.session_state.done = False
    st.session_state.penalty = False
    st.session_state.total_steps = 0
    st.session_state.original_expr = ""
    st.session_state.expected_steps = []
    st.session_state.final_result = None
    st.session_state.numbers = []
    st.session_state.operators = []

# ---------- 新题目 ----------
def new_question():
    original_expr, numbers, operators, final_result = generate_question()
    st.session_state.original_expr = original_expr
    st.session_state.numbers = numbers
    st.session_state.operators = operators
    st.session_state.final_result = final_result
    st.session_state.steps = []
    st.session_state.current_step_index = 0
    st.session_state.done = False
    st.session_state.feedback = ""
    st.session_state.penalty = False
    st.session_state.monster_defeated = False
    st.session_state.stage = 1
    st.session_state.prev_expression = original_expr

# ---------- 处理用户输入步骤 ----------
def submit_step():
    user_input = st.session_state.get('step_input', '').strip()
    if not user_input:
        st.session_state.feedback = "请输入计算步骤！"
        return
    
    if st.session_state.done:
        st.session_state.feedback = "这道题已经完成了！请挑战下一只怪物"
        return
    
    prev_expr = st.session_state.steps[-1] if st.session_state.steps else st.session_state.original_expr
    
    result = validate_step(
        user_input,
        prev_expr,
        st.session_state.final_result,
        st.session_state.steps
    )
    
    if len(result) == 3:
        is_valid, message, is_final = result
    else:
        is_valid, message = result
        is_final = False
    
    if is_valid:
        st.session_state.steps.append(user_input)
        st.session_state.current_step_index += 1
        st.session_state.feedback = message
        st.session_state.penalty = False
        
        if is_final:
            st.session_state.done = True
            st.session_state.score += 1
            st.session_state.monster_defeated = True
            st.session_state.feedback = "🎉 恭喜！你击败了怪物！获得1分！"
    else:
        st.session_state.feedback = f"❌ {message}"
        st.session_state.penalty = True
        st.session_state.score -= 1
    
    st.session_state.step_input = ""

# ---------- 显示界面 ----------
def main():
    st.title("⚔️ 数学闯关 · 有理数计算")
    st.markdown("""
    **📋 规则说明：**
    - 支持整数、分数（如 1/2）和小数（如 0.5）
    - 包含裂项、拆项和通分练习
    - **支持带分数格式：**
      - ✅ 单独的带分数：`4 1/2` 表示 `4 + 1/2 = 9/2`
      - ✅ 混合表达式：`9 19/100+1 1/4-4` 会被正确解析
      - ✅ 负带分数：`-1 2/3` 表示 `-1 - 2/3 = -5/3`
      - ✅ 分子为1的带分数：`1 1/6` 表示 `1 + 1/6 = 7/6`
    - **最终结果格式：**
      - ✅ 假分数：`9/2`
      - ✅ 带分数：`4 1/2`
      - ✅ 小数：`4.5`
    - **重要规则：**
      - ✅ **中间步骤**：允许未约分的分数，不会判错
      - ✅ **最终结果**：必须是最简分数！
    - 每一步必须包含等号 `=`
    - 两个运算符不能直接相连
    - 正确一步：怪物-1 HP
    - 错误一步：怪物反击，你被扣1分
    """)
    st.markdown("---")
    
    with st.sidebar:
        st.header("🏆 战绩")
        st.metric("打倒怪物", st.session_state.score)
        
        if st.session_state.steps:
            st.progress(min(1.0, len(st.session_state.steps) / 8))
            st.caption(f"已写 {len(st.session_state.steps)} 步")
        
        if st.session_state.monster_defeated:
            st.success("💥 怪物被击败！")
        if st.session_state.penalty:
            st.error("💢 怪物反击！")
        if st.session_state.score >= 5:
            st.balloons()
            st.success("🌟 你太棒了！继续挑战！")
    
    if st.session_state.stage == 0:
        st.info("👋 准备好了吗？点击下方按钮开始挑战！")
        if st.button("⚔️ 召唤怪物（生成题目）"):
            new_question()
            st.rerun()
    else:
        st.subheader("📝 当前题目")
        original_expr = st.session_state.get("original_expr", "")
        st.write(f"**计算：** `{original_expr}`")
        
        if st.session_state.final_result is not None:
            st.caption("💡 提示：逐步化简，每一步都要合理，最后得到结果")
            
            has_fraction = any(isinstance(n, Fraction) for n in st.session_state.numbers)
            has_decimal = any(isinstance(n, float) for n in st.session_state.numbers)
            
            if len(st.session_state.numbers) >= 4:
                st.info("📌 多项运算，注意运算顺序，可以逐步合并")
            
            if has_fraction and has_decimal:
                st.info("📌 包含分数和小数，可以混合使用")
            elif has_fraction:
                st.info("📌 包含分数，注意通分和约分")
            elif has_decimal:
                st.info("📌 包含小数，注意小数点位置")
            
            fraction_count = sum(1 for n in st.session_state.numbers if isinstance(n, Fraction))
            if fraction_count >= 3:
                st.info(f"📌 包含 {fraction_count} 个分数，建议先通分再计算")
        
        if st.session_state.steps:
            st.write("**✅ 你的步骤：**")
            for i, step in enumerate(st.session_state.steps):
                st.success(f"第{i+1}步: {step}")
        
        if st.session_state.feedback:
            if "✅" in st.session_state.feedback or "🎉" in st.session_state.feedback:
                st.success(st.session_state.feedback)
            elif "❌" in st.session_state.feedback:
                st.error(st.session_state.feedback)
            else:
                st.info(st.session_state.feedback)
        
        if not st.session_state.done:
            with st.form(key="step_form"):
                step_input = st.text_input(
                    "输入下一步的计算过程：",
                    placeholder="例如：= 1 1/6 或 = 9 19/100+1 1/4-4",
                    key="step_input_widget"
                )
                submitted = st.form_submit_button("提交步骤")
                
                if submitted:
                    st.session_state.step_input = step_input
                    submit_step()
                    st.rerun()
            
            if not st.session_state.steps:
                st.info("💡 第1步示例：可以先去括号，或先通分合并")
            else:
                st.info("💡 继续化简，可以合并同分母分数，或通分后合并")
                
            st.info("💡 **提示**：带分数可以直接在表达式中使用")
            st.caption("💡 示例：`1 1/6` = `1 + 1/6` = `7/6`")
            st.caption("💡 示例：`9 19/100+1 1/4-4` = `(919/100)+(5/4)-4`")
        else:
            st.balloons()
            st.success("🎊 所有步骤完成！怪物已倒！")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⚔️ 挑战下一只怪物", use_container_width=True):
                    new_question()
                    st.rerun()
            with col2:
                if st.button("🔄 重新开始", use_container_width=True):
                    reset_game()
                    st.rerun()
        
        if st.button("🔄 重置游戏 (清空分数)", use_container_width=True):
            reset_game()
            st.rerun()

if __name__ == "__main__":
    main()