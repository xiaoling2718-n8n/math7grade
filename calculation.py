import streamlit as st
import random
import re
from fractions import Fraction
import math

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
    
    # 确保最终结果是最简分数
    if isinstance(final_result, Fraction):
        final_result = final_result.limit_denominator()
    
    return original_expr, numbers, operators, final_result

def format_number(num):
    """格式化数字为字符串"""
    if isinstance(num, Fraction):
        # 确保分数是最简形式
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

def calculate_value(expr):
    """计算表达式的值，支持分数和小数"""
    try:
        namespace = {'Fraction': Fraction}
        
        def replace_fraction(match):
            num = int(match.group(1))
            den = int(match.group(2))
            return f"Fraction({num}, {den})"
        
        expr_eval = re.sub(r'(\d+)/(\d+)', replace_fraction, expr)
        expr_eval = expr_eval.replace('(', '').replace(')', '')
        result = eval(expr_eval, namespace)
        
        # 如果是分数，确保最简形式
        if isinstance(result, Fraction):
            result = result.limit_denominator()
        return result
    except Exception as e:
        try:
            result = eval(expr)
            return result
        except:
            return None

def is_equal(value1, value2):
    """比较两个值是否相等（处理浮点数精度问题和分数约分）"""
    if value1 is None or value2 is None:
        return False
    
    # 如果是分数，先约分再比较
    if isinstance(value1, Fraction):
        value1 = value1.limit_denominator()
    if isinstance(value2, Fraction):
        value2 = value2.limit_denominator()
    
    if isinstance(value1, Fraction) and isinstance(value2, Fraction):
        return value1 == value2
    
    if isinstance(value1, Fraction):
        try:
            if isinstance(value2, (int, float)):
                if isinstance(value2, float):
                    v2_frac = Fraction(round(value2, 10)).limit_denominator(1000)
                    return value1 == v2_frac
                return value1 == value2
        except:
            pass
    
    if isinstance(value2, Fraction):
        try:
            if isinstance(value1, (int, float)):
                if isinstance(value1, float):
                    v1_frac = Fraction(round(value1, 10)).limit_denominator(1000)
                    return v1_frac == value2
                return value1 == value2
        except:
            pass
    
    if isinstance(value1, float) or isinstance(value2, float):
        v1 = float(value1) if not isinstance(value1, Fraction) else float(value1.numerator / value1.denominator)
        v2 = float(value2) if not isinstance(value2, Fraction) else float(value2.numerator / value2.denominator)
        return abs(v1 - v2) < 0.0001
    
    return value1 == value2

def is_final_result(expr):
    """判断表达式是否已经是最终结果（纯数字）"""
    expr_clean = expr.strip()
    pattern = r'^\-?\d+(\.\d+)?$|^\-?\d+/\d+$'
    return bool(re.match(pattern, expr_clean))

def is_fraction_simplified(frac_str):
    """检查分数是否已经是最简形式"""
    # 处理负数
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

def validate_step(step_str, prev_expression, final_result, steps_so_far):
    """验证每一步是否合理"""
    if '=' not in step_str:
        return False, "步骤必须包含等号"
    
    step_clean = re.sub(r'\s+', '', step_str)
    
    if re.search(r'[\+\-][\+\-]', step_clean.replace('(', '').replace(')', '')):
        return False, "两个运算符不能直接相连，请用括号分隔"
    
    parts = step_clean.split('=')
    if len(parts) != 2:
        return False, "格式错误，请使用 '表达式 = 结果' 的格式"
    
    right_side = parts[1]
    
    try:
        right_value = calculate_value(right_side)
        if right_value is None:
            return False, "表达式格式有误"
        
        # 如果是分数，确保数值正确（不管是否约分）
        if isinstance(right_value, Fraction):
            right_value = right_value.limit_denominator()
        
        if steps_so_far:
            last_step = steps_so_far[-1]
            last_step_parts = last_step.split('=')
            if len(last_step_parts) == 2:
                last_value = calculate_value(last_step_parts[1])
                if last_value is not None and not is_equal(right_value, last_value):
                    return False, f"这一步计算有误，表达式的值应该保持不变（应为 {format_number(last_value)}）"
        else:
            prev_value = calculate_value(prev_expression)
            if prev_value is not None and not is_equal(right_value, prev_value):
                return False, f"第一步计算有误，表达式的值应该保持不变（应为 {format_number(prev_value)}）"
        
        # 检查是否已经是最终结果
        is_final = is_final_result(right_side)
        if is_final:
            # 如果是分数，检查是否已经约分到最简
            if '/' in right_side:
                if not is_fraction_simplified(right_side):
                    # 计算最简形式
                    simplified = format_number(right_value)
                    return False, f"分数 {right_side} 还没有约分到最简！最简形式是 {simplified}"
            
            if not is_equal(right_value, final_result):
                expected_str = format_number(final_result)
                return False, f"最终结果应该是 {expected_str}"
        
        return True, "正确", is_final
    except Exception as e:
        return False, f"表达式格式有误: {str(e)}"

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
        st.session_state.feedback = "✅ 步骤正确！怪物 -1 HP"
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
    - 可以保留分数和小数混用
    - **重要：最终结果必须是最简分数！** 
      - ✅ 正确：`-219/35`
      - ❌ 错误：`-438/70`（还能约分）
    - 每一步都要逐步化简表达式（去括号、合并同类项、通分等）
    - 每一步必须包含等号 `=`
    - 负数可以用括号括起来，如 `(-3)` 或直接写 `-3`
    - 两个运算符不能直接相连（如 `-3+-5` 是错误的）
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
                st.info("📌 包含分数和小数，可以混合使用，最终结果必须是最简分数")
            elif has_fraction:
                st.info("📌 包含分数，注意通分和约分，最终结果必须是最简分数")
            elif has_decimal:
                st.info("📌 包含小数，注意小数点位置")
            
            fraction_count = sum(1 for n in st.session_state.numbers if isinstance(n, Fraction))
            if fraction_count >= 3:
                st.info(f"📌 包含 {fraction_count} 个分数，建议先通分再计算")
            
            # 显示最终结果的提示
            expected = format_number(st.session_state.final_result)
            st.info(f"🎯 最终结果（最简形式）：{expected}")
        
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
                    placeholder="例如：= 1/2 + 1/3 + 1/4 或 = 1/2 + 7/12 或 = 13/12",
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
                
            st.warning("⚠️ 中间步骤可以不是最简分数，但最终结果必须是最简分数！")
            st.caption("💡 例如：`-438/70` 还可以约分，应该写成 `-219/35`")
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