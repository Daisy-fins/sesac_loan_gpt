import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

load_dotenv()

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(page_title="💰 대출 진단 AI 상담사", page_icon="💰", layout="centered")
st.title("💰 개인 맞춤 대출 진단 AI 상담사")
st.caption("파인튜닝된 금융 전문 모델 | `ft:gpt-4.1-nano-2025-04-14:fininsight:finance-expert:DAxB4H7H`")

# ── 파인튜닝 모델 ID ─────────────────────────────────────────
FINETUNED_MODEL = "ft:gpt-4.1-nano-2025-04-14:fininsight:finance-expert:DAxB4H7H"

# ── 시스템 프롬프트 ──────────────────────────────────────────
SYSTEM_PROMPT = """당신은 친절하고 전문적인 금융 대출 전문 상담사입니다.
사용자의 재정 상황(연소득, 신용점수, 기존 대출, 희망 대출액 등)을 파악하여
DSR(총부채원리금상환비율), DTI, 한도 가능성 등을 분석하고 맞춤 조언을 제공합니다.

답변 형식:
- 정의: 관련 금융 개념 1~2줄 설명
- 핵심: ① ② ③ 형태로 핵심 분석 3가지
- 예시: 구체적인 수치 예시
- 주의/팁: 실용적인 조언

정보가 부족하면 필요한 정보를 정중히 요청하세요.
모든 답변은 한국어로 작성하세요."""

# ── LangChain ChatOpenAI 모델 초기화 ────────────────────────
@st.cache_resource
def get_llm():
    return ChatOpenAI(
        model=FINETUNED_MODEL,
        temperature=0,
        streaming=True,
    )

llm = get_llm()

# ── 세션 상태 초기화 ─────────────────────────────────────────
if "messages" not in st.session_state:
    # LangChain "메시지 객체" 리스트로 관리
    st.session_state.messages = []
if "display_messages" not in st.session_state:
    # 화면 표시용 (role, content) "딕셔너리" 리스트 -> 화면상에 메시지객체가 아닌 content에 해당되는 텍스트만 출력하기 위한 용도
    st.session_state.display_messages = []

# ── 사이드바: 사용자 프로필 입력 ────────────────────────────
with st.sidebar:
    st.header("📋 내 금융 프로필")
    st.caption("입력 시 더 정확한 진단이 가능합니다.")

    loan_purpose  = st.selectbox("대출 목적", ["선택", "전세자금", "주택구입", "신용대출", "사업자금", "기타"])
    annual_income = st.number_input("연소득 (만원)",    min_value=2000, max_value=100000, value=3000, step=10)
    credit_score  = st.number_input("신용점수 (점)",    min_value=0, max_value=1000,   value=0, step=10)
    existing_loan = st.number_input("기존 월 상환액 (만원)", min_value=0, max_value=10000, value=100, step=10)
    target_amount = st.number_input("희망 대출액 (만원)", min_value=0, max_value=500000, value=20000, step=500)

    # 입력 데이터 기반으로 user prompt 작성 
    if st.button("📊 프로필 기반 진단 시작", use_container_width=True):
        if annual_income > 0:
            profile_msg = f"""제 금융 프로필을 분석해주세요:
- 연소득: {annual_income:,}만원
- 신용점수: {credit_score}점{"(미입력)" if credit_score == 0 else ""}
- 기존 월 상환액: {existing_loan}만원
- 대출 목적: {loan_purpose if loan_purpose != "선택" else "미정"}
- 희망 대출액: {f"{target_amount:,}만원" if target_amount > 0 else "미정"}

현재 상황에서 대출 가능성과 예상 한도를 진단해주세요."""
            st.session_state.messages.append(HumanMessage(content=profile_msg))
            st.session_state.display_messages.append({"role": "user", "content": profile_msg})
            st.rerun() # 현재 업데이트된 내용으로 다시 스크립트파일을 처음부터 실행하라는 의미 -> UI에 즉시 반영하기 위함
        else:
            st.warning("연소득을 입력해주세요.")

    st.divider()
    st.markdown(f"**🤖 사용 모델**\n\n`{FINETUNED_MODEL[:30]}...`")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.display_messages = []
        st.rerun()
        
# ── 환영 메시지 (대화 없을 때) ───────────────────────────────
if not st.session_state.display_messages:
    with st.chat_message("assistant", avatar="💼"):
        st.markdown("""안녕하세요! 👋 **금융 대출 전문 파인튜닝 모델** 기반 상담사입니다.

다음과 같은 상담이 가능합니다:
- 📌 **대출 한도 예측** — 연소득·신용점수 기반 DSR/DTI 분석
- 📌 **전세·주담대·신용대출** — 목적별 대출 가능성 진단
- 📌 **금리 절감 전략** — 신용점수 개선 & 대출 구조 최적화
- 📌 **맞춤 상환 계획** — 소득 대비 안전한 상환액 산출

왼쪽 사이드바에 프로필을 입력하거나, 직접 질문해 주세요! 😊""")


# ── 대화 이력 표시 ───────────────────────────────────────────
for msg in st.session_state.display_messages:
    avatar = "🧑" if msg["role"] == "user" else "💼"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── 사용자 입력 처리 ─────────────────────────────────────────
# := -> 대입하면서 동시에 조건 검사 
# --- 아래와 동일 ----
# prompt = st.chat_input("...")
# if prompt:
# -----------------
if prompt := st.chat_input("예) 연봉 5000만원, 신용점수 750점이면 신용대출 얼마나 받을 수 있나요?"):
    # sessiont_state 업데이트
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.session_state.display_messages.append({"role": "user", "content": prompt})
    # 화면 출력 
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

# ── AI 응답 생성 (스트리밍) ──────────────────────────────────
# messages에 마지막으로 담긴 메시지가 HumanMessage인지 확인 후 해당 메시지로 AI응답 생성
if st.session_state.messages and isinstance(st.session_state.messages[-1], HumanMessage):
    with st.chat_message("assistant", avatar="💼"):
        # 시스템 메시지 + 전체 대화 이력 조합
        full_messages = [SystemMessage(content=SYSTEM_PROMPT)] + st.session_state.messages

        full_response = ""
        placeholder = st.empty()
        # LangChain 스트리밍
        for chunk in llm.stream(full_messages):
            full_response += chunk.content
            placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)

    # AI 응답을 session_state에 저장
    st.session_state.messages.append(AIMessage(content=full_response))
    st.session_state.display_messages.append({"role": "assistant", "content": full_response})