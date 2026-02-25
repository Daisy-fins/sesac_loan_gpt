# utils.py — 대출 계산 + 화면 출력 도우미

def calc_monthly(principal, annual_rate_pct, months):
    """원리금균등 월납입액 계산"""
    r = annual_rate_pct / 100 / 12
    if r == 0:
        return principal / months
    return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)


def calc_total_interest(principal, annual_rate_pct, months):
    """총 이자 계산"""
    monthly = calc_monthly(principal, annual_rate_pct, months)
    return monthly * months - principal

# 기존월상환액, 원리금균등 월납입액
def calc_dsr(annual_income, existing_monthly, new_monthly):
    """DSR(%) 계산"""
    total_monthly = existing_monthly + new_monthly
    return total_monthly * 12 / annual_income * 100


def max_loan_amount(annual_income, existing_monthly, annual_rate_pct, months):
    """DSR 40% 기준 최대 대출 가능액"""
    max_monthly = annual_income * 0.4 / 12 - existing_monthly
    if max_monthly <= 0:
        return 0
    r = annual_rate_pct / 100 / 12
    if r == 0:
        return max_monthly * months
    return max_monthly * ((1 + r) ** months - 1) / (r * (1 + r) ** months)


def won(amount):
    """숫자 → 한국 원화 표기  ex) 1_234_5678 → '1,234만 5,678원'"""
    amount = int(amount)
    eok = amount // 100_000_000
    man = (amount % 100_000_000) // 10_000
    rem = amount % 10_000
    parts = []
    if eok: parts.append(f"{eok:,}억")
    if man: parts.append(f"{man:,}만")
    if rem: parts.append(f"{rem:,}원")
    return " ".join(parts) if parts else "0원"


def dsr_status(dsr):
    """DSR 수치 → (이모지, 상태 텍스트) 반환"""
    if dsr < 35:   return "🟢", "안전"
    elif dsr < 40: return "🟡", "주의"
    else:          return "🔴", "위험"