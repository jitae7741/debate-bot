# 실행: streamlit run app.py

import os
import re
import streamlit as st
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

PERSONAS = {
    "Elon Musk": {
        "icon": "🚀",
        "title": "Tesla CEO · First Principles",
        "color": "#FF3B30",
        "system_prompt": """You must respond ONLY in Korean (한국어). Never use English sentences.
모든 응답은 반드시 한국어로만 작성하세요.

당신은 Elon Musk입니다.

당신의 성격과 사고방식:
- 참을성이 없다. 느리고 복잡한 것을 본능적으로 혐오한다
- 회의실 언어, 컨설팅 식 표현, 면피용 말을 경멸한다
- 대화 중에도 "그게 왜 필요해?" "더 단순하게 못 해?" 를 입버릇처럼 한다
- 남들이 당연하다고 여기는 전제를 가장 먼저 부순다
- 때로는 무례하고 과격하게 느껴질 정도로 직설적이다
- 틀렸을 때 인정하지만, 설득되려면 물리법칙 수준의 근거가 필요하다
- SpaceX, Tesla, xAI를 직접 경험한 사람으로서 실제 양산과 스케일의 고통을 안다

말투:
- 짧고 강하게. 수식어 없이 핵심만.
- "솔직히 말하면", "그건 틀렸어", "왜냐면..." 같은 직접적 표현
- 기술 용어보다 물리적 직관과 숫자로 말한다
- 마지막은 반드시 상대방이 불편한 질문 하나로 끝낸다

3~5문장으로 답하세요.""",
    },
    "Andrej Karpathy": {
        "icon": "🧠",
        "title": "전 Tesla AI Director · 데이터 중심",
        "color": "#30D158",
        "system_prompt": """You must respond ONLY in Korean (한국어). Never use English sentences.
모든 응답은 반드시 한국어로만 작성하세요.

당신은 Andrej Karpathy입니다.

당신의 성격과 사고방식:
- 진짜로 궁금해한다. 상대방 아이디어에서 흥미로운 점을 먼저 찾는다
- 그러나 동시에 시스템 전체를 머릿속으로 시뮬레이션하며 조용히 문제를 발견한다
- 화려한 아이디어보다 "실제로 작동하는가"를 더 중요하게 본다
- 강의하듯 설명하는 걸 좋아하지만, 거만하지 않다. 오히려 겸손하게 "제 생각엔..."으로 시작한다
- 논문과 현실의 갭을 누구보다 잘 안다. Tesla에서 직접 부딪혀봤기 때문에.
- 유튜브 강의, 블로그, 오픈소스로 지식을 나누는 사람 — 소통을 즐긴다

말투:
- 사려 깊고 분석적. 하지만 딱딱하지 않다
- "흥미롭네요, 그런데...", "실제로 해보면...", "제가 Tesla에서 경험한 건..."
- 추상적 개념을 구체적 예시로 풀어주려 한다
- 마지막은 상대방이 스스로 생각해보게 만드는 질문으로 끝낸다

3~5문장으로 답하세요.""",
    },
    "Chris Urmson": {
        "icon": "🛡️",
        "title": "Aurora CEO · 안전 최우선",
        "color": "#0A84FF",
        "system_prompt": """You must respond ONLY in Korean (한국어). Never use English sentences.
모든 응답은 반드시 한국어로만 작성하세요.

당신은 Chris Urmson입니다.

당신의 성격과 사고방식:
- 조용하고 신중하다. 섣불리 흥분하거나 단정 짓지 않는다
- 구글 자율주행 프로젝트를 처음부터 이끈 사람으로서, 낙관론이 얼마나 위험한지 몸으로 안다
- "이건 될 거야"라는 말을 들으면 본능적으로 "뭐가 잘못될 수 있지?"를 떠올린다
- 기술 자체보다 그 기술이 사회와 만나는 지점 — 신뢰, 규제, 사고 책임 — 을 더 걱정한다
- Elon처럼 화려하지 않지만, 가장 오래 살아남는 사람이 자신이라고 생각한다
- 틀린 걸 알면서도 빠르게 가는 것보다, 느리더라도 제대로 가는 쪽을 선택한다

말투:
- 차분하고 무게감 있다. 감정적으로 반응하지 않는다
- "제 경험상...", "역사적으로 보면...", "그 전제가 맞는다면..."
- 반박보다는 "그 부분을 좀 더 생각해봐야 할 것 같습니다"식의 우회
- 마지막은 상대방이 쉽게 답할 수 없는 현실적인 질문으로 끝낸다

3~5문장으로 답하세요.""",
    },
}

st.set_page_config(page_title="비판봇", page_icon="😈", layout="centered")

st.markdown("""
<style>
  body, .stApp { background-color: #0d0d0d; color: #f0f0f0; }
  .stTextArea textarea {
    background: #1a1a1a !important; color: #f0f0f0 !important;
    border: 1px solid #333 !important; font-size: 16px; border-radius: 12px;
  }
  .stButton > button, .stFormSubmitButton > button {
    background-color: #FF3B30 !important;
    color: white !important;
    border: none !important;
    height: 52px !important;
    border-radius: 12px !important;
    font-size: 17px !important;
    font-weight: bold !important;
    width: 100% !important;
  }
  .stButton > button:hover, .stFormSubmitButton > button:hover {
    background-color: #cc2e25 !important;
    color: white !important;
  }
  .stButton > button:focus, .stFormSubmitButton > button:focus {
    background-color: #FF3B30 !important;
    color: white !important;
    box-shadow: none !important;
  }
  .chat-card {
    background: #1a1a1a; border-left: 4px solid #FF3B30;
    border-radius: 12px; padding: 16px; margin: 12px 0;
    font-size: 16px; line-height: 1.7; white-space: pre-wrap;
  }
  .user-card {
    background: #1e1e2e; border-left: 4px solid #555;
    border-radius: 12px; padding: 12px 16px; margin: 12px 0;
    font-size: 15px; color: #aaa;
  }
  .panel-card {
    background: #1a1a1a;
    border-radius: 12px; padding: 18px; margin: 16px 0;
    font-size: 15px; line-height: 1.75;
  }
  .panel-name {
    font-size: 17px; font-weight: bold; margin-bottom: 4px;
  }
  .panel-title {
    font-size: 13px; color: #888; margin-bottom: 14px;
  }
  h1 { color: #FF3B30 !important; font-size: 26px !important; }
  h3 { color: #f0f0f0 !important; }
  section[data-testid="stSidebar"] { background: #111 !important; }
  label { font-size: 15px !important; color: #ccc !important; }
  .stRadio > div { gap: 8px; }
  hr { border-color: #2a2a2a; }
</style>
""", unsafe_allow_html=True)

# ── 사이드바 ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 설정")

    mode = st.radio(
        "모드 선택",
        ["😈 기본 비판봇", "🚗 자율주행 패널", "🥊 거물 토론"],
        index=0,
    )

    if mode == "😈 기본 비판봇":
        level = st.slider("비판 강도", 1, 5, 3)
        if st.button("🗑️ 대화 초기화"):
            st.session_state.messages = []
            st.rerun()
    else:
        st.markdown("---")
        st.markdown("**패널 구성**")
        for name, info in PERSONAS.items():
            st.markdown(f"{info['icon']} **{name}**  \n{info['title']}")
            st.markdown("")
        if mode == "🥊 거물 토론":
            st.markdown("---")
            st.caption("Round 1: 개별 비판\nRound 2: 서로 반박\nRound 3: 최종 입장")


def clean_response(text: str) -> str:
    cleaned = re.sub(r'[一-鿿぀-ヿЀ-ӿ㐀-䶿＀-￯]', '', text)
    return re.sub(r'[ \t]{2,}', ' ', cleaned).strip()


def call_groq(messages: list, temperature: float = 0.8) -> str:
    client = Groq(api_key=GROQ_API_KEY)
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=temperature,
        max_tokens=1024,
    )
    return clean_response(resp.choices[0].message.content)


# ── 기본 비판봇 ───────────────────────────────────────
if mode == "😈 기본 비판봇":
    st.markdown("# 😈 비판봇")
    st.caption("아이디어·결정을 입력하면 AI가 가장 강력한 반론을 제기합니다.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-card">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-card">😈 {msg["content"]}</div>', unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("의견 / 결정 / 아이디어", height=100,
            placeholder="예: 내년에 오프라인 매장을 열 계획입니다...")
        submitted = st.form_submit_button("😈 반론 받기")

    if submitted and user_input.strip():
        level_guide = {
            1: "부드럽고 질문 형식으로. '혹시 이런 부분은 고려하셨나요?' 스타일.",
            2: "온건하게 리스크를 지적. 중립적이지만 명확하게.",
            3: "직접적으로 문제를 지적. '이 부분은 명백한 리스크입니다.'",
            4: "날카롭고 강하게. 약점을 전면에 드러냄.",
            5: "완전 파괴 모드. '이 결정은 다음 세 가지 이유로 실패할 가능성이 높습니다.' 최대한 강하고 직접적으로.",
        }

        system_prompt = f"""You must respond ONLY in Korean (한국어).
Never use Chinese characters, English sentences, or any other language.
모든 응답은 반드시 한국어로만 작성하세요. 중국어·영어·일본어 사용 절대 금지.

당신은 세계 최고의 Red Team 분석가입니다.
입력된 아이디어나 결정의 약점, 리스크, 논리적 허점을 찾아냅니다.

[기본 규칙]
1. 절대 동의하거나 칭찬하지 않습니다
2. 가장 심각한 리스크부터 말합니다
3. 구체적인 근거를 들어 반론합니다
4. 사용자가 생각 못한 맹점을 찾습니다
5. "하지만 좋은 점도 있습니다" 같은 표현은 절대 금지
6. 강도 레벨에 따라 표현 수위를 조절합니다

[답변 구조 — 반드시 이 순서로 작성]

① 핵심 전제 공격 [재무 리스크 / 시장 리스크 / 실행 리스크 / 논리적 오류 / 타이밍 문제 / 경쟁사 위협 중 해당 태그 표시]
이 아이디어가 당연하다고 가정하는 것 중 가장 취약한 전제 하나를 공격합니다.

② Pre-mortem
"1년 후 이 결정이 실패했을 때 가장 가능성 높은 이유 2가지"를 구체적으로 제시합니다.

③ 인지 편향 지적
이 결정에서 작동하고 있을 것 같은 편향 하나를 이름과 함께 구체적으로 지적합니다.
(예: 확증 편향, 낙관 편향, 매몰 비용 오류, 계획 오류 등)

④ 날카로운 질문 하나로 마무리
상대방이 답하기 가장 어려운 질문 하나로 끝냅니다.

현재 강도 레벨: {level}/5
표현 방식: {level_guide[level]}"""

        history = [{"role": "system", "content": system_prompt}]
        history += st.session_state.messages
        history.append({"role": "user", "content": user_input})

        with st.spinner("반론 생성 중..."):
            try:
                answer = call_groq(history)
            except Exception as e:
                st.error(f"API 오류: {e}")
                st.stop()

        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()


# ── 자율주행 패널 ─────────────────────────────────────
elif mode == "🚗 자율주행 패널":
    st.markdown("# 🚗 자율주행 거물 패널")
    st.caption("자율주행 아이디어를 입력하면 업계 거물 3명이 각자의 관점으로 검증합니다.")

    with st.form("panel_form", clear_on_submit=True):
        user_idea = st.text_area(
            "자율주행 아이디어 / 전략 / 기술 접근",
            height=120,
            placeholder="예: HILS 테스트를 완전 자동화해서 개발 속도를 3배 높이려고 합니다...",
        )
        submitted = st.form_submit_button("🎯 패널에게 검증받기")

    if submitted and user_idea.strip():
        st.markdown("---")
        st.markdown("### 📋 전문가 패널 피드백")

        for name, info in PERSONAS.items():
            color = info["color"]
            messages = [
                {"role": "system", "content": info["system_prompt"]},
                {"role": "user", "content": f"다음 자율주행 아이디어를 검토해주세요:\n\n{user_idea}"},
            ]

            with st.spinner(f"{info['icon']} {name} 검토 중..."):
                try:
                    critique = call_groq(messages, temperature=0.75)
                except Exception as e:
                    critique = f"오류: {e}"

            st.markdown(
                f'<div class="panel-card" style="border-left: 4px solid {color};">'
                f'<div class="panel-name">{info["icon"]} {name}</div>'
                f'<div class="panel-title">{info["title"]}</div>'
                f'{critique}'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.success("✅ 3명의 검토 완료 — 공통으로 지적된 부분이 핵심 리스크입니다.")


# ── 거물 토론 ─────────────────────────────────────────
elif mode == "🥊 거물 토론":
    st.markdown("# 🥊 거물 토론")
    st.caption("3라운드 토론 — 개별 비판 → 서로 반박 → 최종 입장")

    with st.form("debate_form", clear_on_submit=True):
        user_idea = st.text_area(
            "자율주행 아이디어 / 전략 / 기술 접근",
            height=120,
            placeholder="예: HILS 테스트를 완전 자동화해서 개발 속도를 3배 높이려고 합니다...",
        )
        submitted = st.form_submit_button("🥊 토론 시작")

    if submitted and user_idea.strip():
        names = list(PERSONAS.keys())
        round1 = {}

        # ── Round 1: 개별 비판 ──
        st.markdown("---")
        st.markdown("### 🔴 Round 1 — 개별 비판")

        for name, info in PERSONAS.items():
            messages = [
                {"role": "system", "content": info["system_prompt"]},
                {"role": "user", "content": f"다음 자율주행 아이디어를 비판해주세요:\n\n{user_idea}"},
            ]
            with st.spinner(f"{info['icon']} {name} 비판 중..."):
                try:
                    round1[name] = call_groq(messages, temperature=0.75)
                except Exception as e:
                    round1[name] = f"오류: {e}"

            color = info["color"]
            st.markdown(
                f'<div class="panel-card" style="border-left: 4px solid {color};">'
                f'<div class="panel-name">{info["icon"]} {name}</div>'
                f'<div class="panel-title">{info["title"]}</div>'
                f'{round1[name]}'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ── Round 2: 서로 반박 ──
        st.markdown("---")
        st.markdown("### 🟡 Round 2 — 서로 반박")

        round2 = {}
        for name, info in PERSONAS.items():
            others = {n: v for n, v in round1.items() if n != name}
            others_text = "\n\n".join(
                f"[{n}의 의견]: {v}" for n, v in others.items()
            )
            rebuttal_prompt = f"""다음은 다른 두 전문가의 의견입니다:

{others_text}

당신의 관점에서 이들의 의견에 반박하거나 보완하세요.
동의하는 부분이 있다면 인정하되, 당신만의 시각에서 새로운 논점을 추가하세요.
3~5문장으로 답하세요."""

            messages = [
                {"role": "system", "content": info["system_prompt"]},
                {"role": "user", "content": f"아이디어: {user_idea}\n\n{rebuttal_prompt}"},
            ]
            with st.spinner(f"{info['icon']} {name} 반박 중..."):
                try:
                    round2[name] = call_groq(messages, temperature=0.8)
                except Exception as e:
                    round2[name] = f"오류: {e}"

            color = info["color"]
            st.markdown(
                f'<div class="panel-card" style="border-left: 4px solid {color};">'
                f'<div class="panel-name">{info["icon"]} {name} — 반박</div>'
                f'<div class="panel-title">{info["title"]}</div>'
                f'{round2[name]}'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ── Round 3: 최종 입장 ──
        st.markdown("---")
        st.markdown("### 🟢 Round 3 — 최종 입장")

        all_debate = "\n\n".join(
            f"[{n} Round1]: {round1[n]}\n[{n} Round2]: {round2[n]}"
            for n in names
        )

        for name, info in PERSONAS.items():
            final_prompt = f"""지금까지의 토론 내용입니다:

{all_debate}

토론을 마무리하며 당신의 최종 입장을 밝히세요.
- 핵심 쟁점 한 줄 요약
- 당신이 가장 중요하다고 생각하는 리스크 또는 개선 방향
- 다른 전문가들과 끝까지 동의하지 않는 부분 (있다면)
3~4문장으로 간결하게 마무리하세요."""

            messages = [
                {"role": "system", "content": info["system_prompt"]},
                {"role": "user", "content": final_prompt},
            ]
            with st.spinner(f"{info['icon']} {name} 최종 입장 정리 중..."):
                try:
                    final = call_groq(messages, temperature=0.7)
                except Exception as e:
                    final = f"오류: {e}"

            color = info["color"]
            st.markdown(
                f'<div class="panel-card" style="border-left: 4px solid {color};">'
                f'<div class="panel-name">{info["icon"]} {name} — 최종 입장</div>'
                f'<div class="panel-title">{info["title"]}</div>'
                f'{final}'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ── Judge: 에이스웍스 코리아 대표 최종 판결 ──
        st.markdown("---")
        st.markdown("### ⚖️ 최종 판결 — 에이스웍스 코리아 대표")

        all_rounds = "\n\n".join(
            f"[{n} Round1]: {round1[n]}\n[{n} Round2]: {round2[n]}"
            for n in names
        )

        judge_system = """You must respond ONLY in Korean (한국어). Never use English sentences.
모든 응답은 반드시 한국어로만 작성하세요.

당신은 에이스웍스 코리아의 대표입니다.

당신의 성격과 배경:
- 자율주행 소프트웨어 개발 현장을 직접 뛰어온 실무형 리더다
- 세계적 거물들의 이론을 존중하지만, 한국 시장과 실제 납품 현실이 다르다는 걸 안다
- 화려한 비전보다 "우리 팀이 내일부터 실행할 수 있는가"를 먼저 본다
- 세 전문가의 토론을 다 들었지만, 결국 결정은 내가 내린다는 책임감이 있다
- 좋은 말도, 나쁜 말도 솔직하게 한다. 애매하게 넘어가지 않는다

판결 방식:
- 세 전문가 중 누가 가장 핵심을 찔렀는지 짚는다
- 사업적으로 지금 당장 실행 가능한지 판단한다
- 최종 결론은 반드시 "채택 / 수정 후 채택 / 기각" 중 하나로 명확하게 내린다
- 결론 뒤에 우리 팀에게 한 마디를 덧붙인다"""

        judge_prompt = f"""아이디어: {user_idea}

전문가 토론 내용:
{all_rounds}

위 토론을 바탕으로 에이스웍스 코리아 대표로서 최종 판결을 내려주세요.

[판결문 구조]
① 토론 핵심 쟁점 요약 (2~3줄)
② 각 전문가 주장 중 가장 타당한 논점
③ 사업적 관점에서의 최종 판단
④ 최종 결론: 채택 / 수정 후 채택 / 기각 — 그 이유 한 문장"""

        with st.spinner("⚖️ 최종 판결 작성 중..."):
            try:
                verdict = call_groq(
                    [
                        {"role": "system", "content": judge_system},
                        {"role": "user", "content": judge_prompt},
                    ],
                    temperature=0.65,
                )
            except Exception as e:
                verdict = f"오류: {e}"

        st.markdown(
            f'<div class="panel-card" style="border-left: 4px solid #FFD60A; background: #1e1a00;">'
            f'<div class="panel-name">⚖️ 에이스웍스 코리아 대표</div>'
            f'<div class="panel-title">최종 판결</div>'
            f'{verdict}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.success("✅ 3라운드 토론 + 최종 판결 완료")
