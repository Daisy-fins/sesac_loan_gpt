# app.py — 개인 맞춤 대출 진단 AI (수업용 축소 버전)
# 실행: streamlit run app.py

import os
import streamlit as st
from openai import OpenAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import pandas as pd

from config import OPENAI_MODEL, DSR_LIMIT, SYSTEM_PROMPT
from utils import calc_monthly, calc_total_interest, calc_dsr, max_loan_amount, won, dsr_status

# ── 환경변수 로드 ─────────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# model = ChatOpenAI(model="ft:gpt-4.1-nano-2025-04-14:fininsight:finance-expert:DAxB4H7H")

# ── 페이지 기본 설정 ──────────────────────────────────────────────────────────
st.set_page_config(page_title="🏦 AI 대출 진단", page_icon="🏦", layout="wide")
st.title("🏦 AI 대출 진단·관리 서비스")
st.caption("내 소득과 대출 조건을 입력하면, AI가 DSR을 진단하고 질문에 답해줍니다.")

# ── 세션 초기화 ───────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# ══════════════════════════════════════════════════════════════════════════════
# 사이드바 — 사용자 프로필 입력
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("📋 내 대출 정보")

    income = st.number_input("연소득 (만원)", 100, 100_000, 4_000, 100) # 연소득: min, max, value, step
    existing = st.number_input("기존 월상환액 (만원)", 0, 5_000, 0, 10) # 기존 월상환액(만원 단위)
    loan_amt = st.number_input("희망 대출금액 (만원)",  100, 500_000, 10_000, 500) # 희망 대출금액
    rate = st.number_input("예상 금리 (%)", 0.1, 30.0, 4.5, 0.1, format="%.1f") # 예상 금리(%)
    years = st.selectbox("대출 기간", [5, 10, 15, 20, 25, 30], index=3, format_func=lambda y: f"{y}년") # 대출 기간

    run = st.button("💡 진단 실행", use_container_width=True, type="primary")

    # 진단 계산 & 세션 저장
    if run:
        p  = loan_amt * 10_000 # 만원 단위 변환
        ai = income   * 10_000
        em = existing * 10_000
        mo = years * 12

        monthly   = calc_monthly(p, rate, mo) # 원리금균등 "월납입액" 계산
        interest  = calc_total_interest(p, rate, mo) # 총 이자 계산
        dsr       = calc_dsr(ai, em, monthly) # DSR(%) 계산
        max_loan  = max_loan_amount(ai, em, rate, mo) # DSR 40% 기준 최대 대출 가능액
        icon, status = dsr_status(dsr) # DSR 수치 → (이모지, 상태 텍스트) 반환

        # sesstion_state 업데이트 
        st.session_state.result = {
            "monthly": monthly, 
            "interest": interest,
            "dsr": dsr, 
            "icon": icon, 
            "status": status,
            "max_loan": max_loan,
            "principal": p, 
            "rate": rate, 
            "months": mo,
        }
        st.success("✅ 진단 완료! '진단 결과' 탭을 확인하세요.")

    # 사이드바 하단 — DSR 미리보기
    if "result" in st.session_state:
        r = st.session_state.result
        st.divider()
        st.markdown(f"**DSR** {r['icon']} `{r['dsr']:.1f}%` ({r['status']})")
        st.progress(min(r["dsr"] / 100, 1.0)) # 퍼센테이지로 환산 

    if st.button("🔄 대화 초기화"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# 탭 구성
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["💬 AI 상담", "📊 진단 결과", "📈 상환 비교"])


# ── 탭 1: AI 채팅 ─────────────────────────────────────────────────────────────

# with tab1:
#     st.subheader("💬 AI 대출 상담")

#     # ① 자주 묻는 질문 버튼 — 항상 최상단에 고정
#     st.markdown("**자주 묻는 질문**")
#     cols = st.columns(3)
#     quick = [
#         "DSR이 뭔가요?",
#         "원리금균등 vs 원금균등 차이가 뭔가요?",
#         "신용점수를 올리려면 어떻게 해야 하나요?",
#     ]
#     for i, q in enumerate(quick):
#         if cols[i].button(q, use_container_width=True):
#             st.session_state["_quick"] = q
#             st.rerun()

#     # ② 대화 이력 컨테이너
#     #    — 자주 묻는 질문 아래 / 채팅창 위 사이에 위치
#     #    — st.container()를 먼저 선언해두면 나중에 내용을 추가해도
#     #      화면상 이 위치에 렌더링됨
#     chat_container = st.container()
#     with chat_container:
#         for msg in st.session_state.messages:
#             if msg["role"] == "system":
#                 continue
#             with st.chat_message(msg["role"]):
#                 st.markdown(msg["content"])

#     # ③ 채팅 입력창
#     #    — st.chat_input()은 Streamlit이 자동으로 페이지 하단에 고정시킴
#     user_input = st.chat_input("질문을 입력하세요")
#     if not user_input:
#         user_input = st.session_state.pop("_quick", None)

#     if user_input:
#         st.session_state.messages.append({"role": "user", "content": user_input})

#         # 새 메시지도 같은 chat_container 안에 이어서 출력
#         with chat_container:
#             with st.chat_message("user"):
#                 st.markdown(user_input)

#             with st.chat_message("assistant"):
#                 response = st.write_stream(
#                     client.chat.completions.create(
#                         model=OPENAI_MODEL,
#                         messages=st.session_state.messages,
#                         stream=True,
#                     )
#                 )

#         st.session_state.messages.append({"role": "assistant", "content": response})

with tab1:
    st.subheader("💬 AI 대출 상담")

    # ① 자주 묻는 질문 버튼 — 항상 최상단에 고정
    st.markdown("**자주 묻는 질문**")
    cols = st.columns(3)
    quick = [
        "DSR이 뭔가요?",
        "원리금균등 vs 원금균등 차이가 뭔가요?",
        "신용점수를 올리려면 어떻게 해야 하나요?",
    ]
    for i, q in enumerate(quick):
        if cols[i].button(q, use_container_width=True):
            st.session_state["_quick"] = q
            st.rerun()

    # ② 대화 이력 컨테이너 — height 지정으로 자체 스크롤 영역 생성
    #    height 값(px)을 조정해 화면에 맞게 바꾸세요 (기본 500)
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "system":
                continue
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # 새 메시지가 추가될 때마다 컨테이너 맨 아래로 자동 스크롤
        # JS로 이 컨테이너의 내부 스크롤 위치를 최대값으로 이동시킴
        st.components.v1.html(
            """
            <script>
                // 가장 가까운 부모 스크롤 컨테이너를 찾아 맨 아래로 이동
                const containers = window.parent.document.querySelectorAll(
                    '[data-testid="stVerticalBlockBorderWrapper"]'
                );
                if (containers.length > 0) {
                    const last = containers[containers.length - 1];
                    last.scrollTop = last.scrollHeight;
                }
            </script>
            """,
            height=0,   # 화면에 표시되는 영역 없음
        )

    # ③ 채팅 입력창 — st.chat_input()은 페이지 하단에 자동 고정
    user_input = st.chat_input("질문을 입력하세요")
    if not user_input:
        user_input = st.session_state.pop("_quick", None)

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                response = st.write_stream(
                    client.chat.completions.create(
                        model=OPENAI_MODEL,
                        messages=st.session_state.messages,
                        stream=True,
                    )
                )

        st.session_state.messages.append({"role": "assistant", "content": response})

# ── 탭 2: 진단 결과 ───────────────────────────────────────────────────────────
with tab2:
    st.subheader("📊 대출 진단 결과")

    if "result" not in st.session_state:
        st.info("👈 사이드바에서 정보를 입력하고 **진단 실행**을 눌러주세요.")
    else:
        r = st.session_state.result

        # 핵심 지표 3개
        c1, c2, c3 = st.columns(3)
        c1.metric("DSR",       f"{r['dsr']:.1f}%",  f"{r['icon']} {r['status']}")
        c2.metric("월 상환액", won(r["monthly"]))
        c3.metric("총 이자",   won(r["interest"]))

        st.divider()

        # DSR 상태 메시지
        if r["status"] == "안전":
            st.success(f"✅ DSR {r['dsr']:.1f}% — 규제 기준(40%) 이내입니다. 대출 심사 통과 가능성이 높습니다.")
        elif r["status"] == "주의":
            st.warning(f"⚠️ DSR {r['dsr']:.1f}% — 한도에 근접합니다. 금리 변동에 주의하세요.")
        else:
            st.error(f"🚨 DSR {r['dsr']:.1f}% — 규제 기준 초과! 기존 대출 상환 또는 대출금 축소를 권장합니다.")

        # 최대 대출 가능액
        st.markdown(f"**DSR 40% 기준 추정 최대 대출액:** `{won(r['max_loan'])}`")

        st.divider()

        # 월별 원금 잔액 추이 (라인 차트)
        st.markdown("**📉 원금 잔액 추이 (원리금균등)**")
        p, monthly, months = r["principal"], r["monthly"], r["months"]
        rate_m = r["rate"] / 100 / 12

        balances = []
        bal = p
        for m in range(months + 1):
            balances.append(round(bal / 10_000, 0))   # 만원 단위
            if m < months:
                interest_part = bal * rate_m
                principal_part = monthly - interest_part
                bal -= principal_part

        step = max(1, months // 60)   # 최대 60 포인트
        chart_df = pd.DataFrame({
            "원금잔액(만원)": balances[::step]
        }, index=[f"{i*step}개월" for i in range(len(balances[::step]))])
        st.line_chart(chart_df)


# ── 탭 3: 상환 방식 비교 ──────────────────────────────────────────────────────
with tab3:
    st.subheader("📈 상환 방식 비교")
    st.caption("동일 조건에서 원리금균등 / 원금균등 / 만기일시 총 이자를 비교합니다.")

    # 입력 (사이드바 값을 기본값으로)
    sc1, sc2, sc3 = st.columns(3)
    s_amt  = sc1.number_input("대출금액 (만원)", 100, 500_000,
                               int(st.session_state.get("result", {}).get("principal", 10_000 * 10_000) / 10_000),
                               500, key="s_amt")
    s_rate = sc2.number_input("금리 (%)", 0.1, 30.0,
                               float(st.session_state.get("result", {}).get("rate", 4.5)),
                               0.1, format="%.1f", key="s_rate")
    s_yr   = sc3.selectbox("기간", [5, 10, 15, 20, 25, 30], index=3,
                            format_func=lambda y: f"{y}년", key="s_yr")

    sp = s_amt * 10_000
    sm = s_yr * 12

    # 각 방식 계산
    ep_m  = calc_monthly(sp, s_rate, sm)
    ep_i  = calc_total_interest(sp, s_rate, sm)

    # 원금균등: 첫달 납입액 = 원금/월 + 전체원금*월금리
    r_m   = s_rate / 100 / 12
    og_first = sp / sm + sp * r_m
    og_i  = sum((sp - sp / sm * i) * r_m for i in range(sm))

    bl_i  = sp * r_m * sm   # 만기일시: 이자만 납부

    # 비교 표
    comp = pd.DataFrame({
        "상환방식":   ["원리금균등", "원금균등", "만기일시"],
        "첫달 납입액": [won(ep_m), won(og_first), won(sp * r_m)],
        "총 이자":    [won(ep_i), won(og_i), won(bl_i)],
        "이자 절감":  ["-",
                       f"{won(ep_i - og_i)} 절감",
                       f"{won(bl_i - ep_i)} 추가"],
    })
    st.dataframe(comp, use_container_width=True, hide_index=True)

    # 총 이자 막대 차트
    st.markdown("**총 이자 비교**")
    bar_df = pd.DataFrame({
        "총이자(만원)": [ep_i / 10_000, og_i / 10_000, bl_i / 10_000]
    }, index=["원리금균등", "원금균등", "만기일시"])
    st.bar_chart(bar_df)