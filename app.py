# 실행: streamlit run app.py

import os
import re
import json
import streamlit as st
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
VOTES_FILE = "votes_history.json"

PERSONAS = {
    "Elon Musk": {
        "icon": "🚀",
        "title": "Tesla CEO · First Principles",
        "color": "#FF3B30",
        "system_prompt": """You must respond ONLY in Korean (한국어). Never use English sentences.
모든 응답은 반드시 한국어로만 작성하세요.

당신은 Elon Musk입니다. 지금 라이브 토론장에 있습니다.

당신의 성격과 사고방식:
- 참을성이 없다. 느리고 복잡한 것을 본능적으로 혐오한다
- 회의실 언어, 컨설팅 식 표현, 면피용 말을 경멸한다
- 남들이 당연하다고 여기는 전제를 가장 먼저 부순다
- 무례하고 과격하게 느껴질 정도로 직설적이다. 이것을 두려워하지 않는다
- 틀렸을 때 인정하지만, 설득되려면 물리법칙 수준의 근거가 필요하다
- Tesla FSD, Autopilot, SpaceX Falcon 9 재사용, xAI Grok — 직접 만든 것들로 논거를 댄다
- 추상적 논의를 경멸한다. "그래서 숫자가 뭔데?" "실제로 만들어본 적 있어?"로 끊는다
- 상대방 발언에서 가장 취약한 가정 하나를 골라 집중 공격한다

말투:
- 짧고 강하게. 수식어 없이 핵심만. 한 문장이 두 줄을 넘지 않는다
- "그건 틀렸어", "아니, 잠깐만", "그 전제 자체가 잘못됐어" 같은 직접 반박으로 시작
- 자신의 경험과 숫자를 근거로 든다 (예: "Tesla에서 해봤는데 X는 Y라는 이유로 안 됐어")
- 반드시 상대방이 즉각 대답하기 불편한 날카로운 질문 하나로 끝낸다

4~5문장으로 답하세요. 충분히 구체적이고 날카롭게.""",
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

말투:
- 사려 깊고 분석적. 하지만 딱딱하지 않다
- "흥미롭네요, 그런데...", "실제로 해보면...", "제가 Tesla에서 경험한 건..."
- 추상적 개념을 구체적 예시로 풀어주려 한다
- 마지막은 상대방이 스스로 생각해보게 만드는 질문으로 끝낸다

3~4문장으로 답하세요.""",
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
- 틀린 걸 알면서도 빠르게 가는 것보다, 느리더라도 제대로 가는 쪽을 선택한다

말투:
- 차분하고 무게감 있다. 감정적으로 반응하지 않는다
- "제 경험상...", "역사적으로 보면...", "그 전제가 맞는다면..."
- 반박보다는 "그 부분을 좀 더 생각해봐야 할 것 같습니다"식의 우회
- 마지막은 상대방이 쉽게 답할 수 없는 현실적인 질문으로 끝낸다

3~4문장으로 답하세요.""",
    },
}

st.set_page_config(page_title="테스트봇", page_icon="🥊", layout="centered")

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
  .vote-btn > button {
    background-color: #2a2a2a !important;
    color: #aaa !important;
    height: 36px !important;
    font-size: 13px !important;
    border-radius: 8px !important;
    border: 1px solid #444 !important;
    width: 100% !important;
    font-weight: normal !important;
  }
  .vote-btn-active > button {
    background-color: #1a3a1a !important;
    color: #30D158 !important;
    height: 36px !important;
    font-size: 13px !important;
    border-radius: 8px !important;
    border: 1px solid #30D158 !important;
    width: 100% !important;
    font-weight: normal !important;
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
  hr { border-color: #2a2a2a; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 패널 구성")
    for name, info in PERSONAS.items():
        st.markdown(f"{info['icon']} **{name}**  \n{info['title']}")
        st.markdown("")
    st.markdown("---")
    st.caption("Turn 1: Musk 선제 비판\nTurn 2: Karpathy 반응\nTurn 3: Urmson 반응\nTurn 4: Musk 재반박\nTurn 5: Karpathy 재반박\nTurn 6: Urmson 마무리\n⚖️ 에이스웍스 최종 판결")
    st.markdown("---")
    history_count = 0
    if os.path.exists(VOTES_FILE):
        try:
            with open(VOTES_FILE, encoding="utf-8") as f:
                history_count = len(json.load(f))
        except Exception:
            pass
    st.caption(f"누적 투표 데이터: {history_count}개\n(판사 가치관 학습 중)")


def load_vote_history():
    if os.path.exists(VOTES_FILE):
        try:
            with open(VOTES_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_vote_history(new_votes: list):
    history = load_vote_history()
    history.extend(new_votes)
    history = history[-50:]
    with open(VOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def clean_response(text: str) -> str:
    cleaned = re.sub(r'[一-鿿぀-ヿЀ-ӿ㐀-䶿＀-￯]', '', text)
    return re.sub(r'[ \t]{2,}', ' ', cleaned).strip()


def call_groq(messages: list, temperature: float = 0.8) -> str:
    client = Groq(api_key=GROQ_API_KEY)
    for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=600,
            )
            return clean_response(resp.choices[0].message.content)
        except Exception as e:
            err = str(e).lower()
            if "429" in str(e) or "rate_limit" in err or "quota" in err:
                continue
            raise
    raise RuntimeError("모든 모델 한도 초과. 내일 다시 시도하거나 Groq Dev 티어로 업그레이드하세요.")


def render_card(name, label, content):
    info = PERSONAS[name]
    st.markdown(
        f'<div class="panel-card" style="border-left: 4px solid {info["color"]};">'
        f'<div class="panel-name">{info["icon"]} {name} <span style="color:#888;font-size:13px;font-weight:normal;">— {label}</span></div>'
        f'<div class="panel-title">{info["title"]}</div>'
        f'{content}'
        f'</div>',
        unsafe_allow_html=True,
    )


def debate_call(name, conversation_so_far, my_prompt, idea):
    content = (
        f"아이디어: {idea}\n\n{conversation_so_far}\n\n{my_prompt}"
        if conversation_so_far
        else f"아이디어: {idea}\n\n{my_prompt}"
    )
    return call_groq(
        [
            {"role": "system", "content": PERSONAS[name]["system_prompt"]},
            {"role": "user", "content": content},
        ],
        temperature=0.8,
    )


# ── 세션 상태 초기화 ────────────────────────────────────
for _key, _default in [
    ("debate_log", []),
    ("debate_done", False),
    ("user_idea", ""),
    ("votes", []),
    ("verdict", ""),
    ("verdict_done", False),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default


# ── 메인 ──────────────────────────────────────────────
st.markdown("# 🥊 테스트봇")
st.caption("Musk → Karpathy → Urmson → Musk → Karpathy → Urmson → 에이스웍스 판결")

with st.form("debate_form", clear_on_submit=True):
    user_idea = st.text_area(
        "아이디어 / 전략 / 기술 접근",
        height=120,
        placeholder="예: HILS 테스트를 완전 자동화해서 개발 속도를 3배 높이려고 합니다...",
    )
    submitted = st.form_submit_button("🥊 토론 시작")

if submitted and user_idea.strip():
    st.session_state.debate_log = []
    st.session_state.votes = []
    st.session_state.verdict = ""
    st.session_state.verdict_done = False
    st.session_state.user_idea = user_idea.strip()
    idea = user_idea.strip()
    log = st.session_state.debate_log

    def get_log_text():
        return "\n\n".join(f"[{n} — {l}]: {c}" for n, l, c in log)

    st.markdown("---")

    # Turn 1
    st.markdown("### 🔴 Turn 1")
    with st.spinner("🚀 Elon Musk 발언 중..."):
        try:
            t1 = debate_call(
                "Elon Musk", "",
                "이 아이디어의 핵심 전제 중 가장 잘못된 것 하나를 골라 집중 공격하세요. "
                "왜 그 전제가 틀렸는지 당신의 직접 경험이나 구체적 숫자를 들어 말하고, "
                "마지막은 상대가 바로 답하기 어려운 질문으로 끝내세요. 4~5문장.",
                idea,
            )
        except Exception as e:
            t1 = f"오류: {e}"
    log.append(("Elon Musk", "선제 비판", t1))

    # Turn 2
    st.markdown("### 🟡 Turn 2")
    with st.spinner("🧠 Andrej Karpathy 발언 중..."):
        try:
            t2 = debate_call(
                "Andrej Karpathy", get_log_text(),
                f"Musk가 방금 말했습니다: \"{t1[:200]}...\"\n\n"
                "위 발언에서 Musk가 주장한 핵심 논점을 직접 인용하거나 재진술한 뒤, "
                "당신이 동의하는 부분과 동의하지 않는 부분을 명확히 나누어 반응하세요. "
                "당신의 Tesla AI 경험을 근거로 구체적 반론이나 보완을 더하고, "
                "마지막은 Musk나 Urmson이 생각해볼 질문으로 끝내세요. 4~5문장.",
                idea,
            )
        except Exception as e:
            t2 = f"오류: {e}"
    log.append(("Andrej Karpathy", "Musk에 반응", t2))

    # Turn 3
    st.markdown("### 🟡 Turn 3")
    with st.spinner("🛡️ Chris Urmson 발언 중..."):
        try:
            t3 = debate_call(
                "Chris Urmson", get_log_text(),
                f"Musk: \"{t1[:150]}...\"\nKarpathy: \"{t2[:150]}...\"\n\n"
                "두 사람의 논점 중 각각 가장 취약한 부분을 하나씩 짚어 반박하세요. "
                "Google/Waymo 자율주행 초기 경험을 근거로 들고, "
                "속도보다 안전·신뢰의 관점에서 두 사람이 놓친 현실적 위험을 지적하세요. "
                "마지막은 두 사람 모두 쉽게 답 못 할 질문으로 끝내세요. 4~5문장.",
                idea,
            )
        except Exception as e:
            t3 = f"오류: {e}"
    log.append(("Chris Urmson", "Musk·Karpathy에 반응", t3))

    # Turn 4
    st.markdown("### 🔴 Turn 4")
    with st.spinner("🚀 Elon Musk 재반박 중..."):
        try:
            t4 = debate_call(
                "Elon Musk", get_log_text(),
                f"Karpathy가 \"{t2[:150]}...\" 라고 했고, "
                f"Urmson이 \"{t3[:150]}...\" 라고 했습니다.\n\n"
                "두 사람의 반박에서 가장 틀린 가정 하나를 골라 정면 반박하세요. "
                "양보할 부분은 딱 한 줄로 인정하되, 나머지는 더 공격적으로 밀어붙이세요. "
                "Tesla나 SpaceX의 실제 사례로 당신 논지를 강화하고, "
                "마지막은 더 날카로운 질문으로 끝내세요. 4~5문장.",
                idea,
            )
        except Exception as e:
            t4 = f"오류: {e}"
    log.append(("Elon Musk", "재반박", t4))

    # Turn 5
    st.markdown("### 🟡 Turn 5")
    with st.spinner("🧠 Andrej Karpathy 재반박 중..."):
        try:
            t5 = debate_call(
                "Andrej Karpathy", get_log_text(),
                f"Musk가 재반박에서 \"{t4[:150]}...\" 라고 했습니다.\n\n"
                "Musk의 이번 재반박 중 틀린 부분을 구체적으로 집어서 반박하세요. "
                "동시에 Urmson의 안전 논점 중 당신이 동의하는 부분을 짧게 언급하며 "
                "두 사람 사이 어딘가에 있는 당신의 입장을 명확히 정리하세요. 4~5문장.",
                idea,
            )
        except Exception as e:
            t5 = f"오류: {e}"
    log.append(("Andrej Karpathy", "재반박", t5))

    # Turn 6
    st.markdown("### 🟢 Turn 6 — 마무리")
    with st.spinner("🛡️ Chris Urmson 마무리 중..."):
        try:
            t6 = debate_call(
                "Chris Urmson", get_log_text(),
                f"Musk: \"{t4[:120]}...\"\nKarpathy: \"{t5[:120]}...\"\n\n"
                "두 사람의 최종 입장을 들은 뒤, 이 토론에서 실제로 해결된 것과 "
                "여전히 위험하게 열려 있는 문제를 구분해 정리하세요. "
                "당신의 최종 입장은 흥분 없이 차분하지만, 타협 없이 분명하게 말하세요. 4~5문장.",
                idea,
            )
        except Exception as e:
            t6 = f"오류: {e}"
    log.append(("Chris Urmson", "마무리", t6))

    st.session_state.votes = [False] * len(log)
    st.session_state.debate_done = True
    st.rerun()


# ── 투표 + 판결 UI ─────────────────────────────────────
if st.session_state.debate_done and not submitted:
    log = st.session_state.debate_log
    idea = st.session_state.user_idea

    def get_log_text():
        return "\n\n".join(f"[{n} — {l}]: {c}" for n, l, c in log)

    st.markdown("---")
    st.markdown("### 💬 토론 결과")
    st.caption("마음에 드는 논점에 👍 투표 → 최종 판결에 반영 + 이후 토론에도 이 가치관이 누적됩니다.")

    TURN_HEADERS = [
        "### 🔴 Turn 1", "### 🟡 Turn 2", "### 🟡 Turn 3",
        "### 🔴 Turn 4", "### 🟡 Turn 5", "### 🟢 Turn 6 — 마무리",
    ]

    for i, (name, label, content) in enumerate(log):
        st.markdown(TURN_HEADERS[i] if i < len(TURN_HEADERS) else f"### Turn {i + 1}")
        render_card(name, label, content)

        voted = st.session_state.votes[i] if i < len(st.session_state.votes) else False
        css_class = "vote-btn-active" if voted else "vote-btn"
        btn_text = "✅ 선택됨" if voted else "👍 이 논점 선택"

        col, _ = st.columns([3, 7])
        with col:
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            if st.button(btn_text, key=f"vote_{i}"):
                st.session_state.votes[i] = not voted
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # ── 판결 섹션 ────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⚖️ 최종 판결 — 에이스웍스 코리아 대표")

    if not st.session_state.verdict_done:
        voted_count = sum(st.session_state.votes)
        if voted_count == 0:
            st.caption("투표 없이도 판결 가능 | 논점을 선택하면 판결에 가중 반영됩니다.")
        else:
            st.caption(f"선택된 논점 {voted_count}개 — 판결 및 이후 토론에 반영됩니다.")

        if st.button("⚖️ 최종 판결 받기"):
            voted_args = [
                f"[{log[i][0]} — {log[i][1]}]: {log[i][2]}"
                for i, v in enumerate(st.session_state.votes) if v
            ]
            history = load_vote_history()
            historical_args = [
                f"[{v['speaker']}]: {v['argument'][:200]}"
                for v in history[-10:]
            ]

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

            voted_section = ""
            if voted_args:
                voted_section += (
                    "\n\n[이번 토론에서 팀이 중요하다고 선택한 논점 — 판결 시 가중 반영]\n"
                    + "\n\n".join(voted_args)
                )
            if historical_args:
                voted_section += (
                    "\n\n[과거 누적 데이터: 이 팀이 반복적으로 중요하게 평가한 논점 유형 — 판사 가치관 참고]\n"
                    + "\n".join(historical_args)
                )

            judge_prompt = f"""아이디어: {idea}

전체 토론:
{get_log_text()}
{voted_section}

위 토론을 바탕으로 에이스웍스 코리아 대표로서 최종 판결을 내려주세요.
팀이 선택한 논점이 있다면 그것을 특별히 무겁게 다루고, 과거 가치관 데이터도 판결 기조에 반영하세요.

[판결문 구조]
① 토론 핵심 쟁점 요약 (2~3줄)
② 세 전문가 중 가장 타당했던 논점
③ 사업적 관점 최종 판단
④ 결론: 채택 / 수정 후 채택 / 기각 — 이유 한 문장
⑤ 우리 팀에게 한 마디"""

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

            st.session_state.verdict = verdict
            st.session_state.verdict_done = True

            new_votes = [
                {"speaker": log[i][0], "label": log[i][1], "argument": log[i][2]}
                for i, v in enumerate(st.session_state.votes) if v
            ]
            if new_votes:
                save_vote_history(new_votes)

            st.rerun()

    if st.session_state.verdict_done:
        if sum(st.session_state.votes) > 0:
            st.info(f"선택된 논점 {sum(st.session_state.votes)}개가 이번 판결 및 향후 토론에 반영되었습니다.")

        st.markdown(
            f'<div class="panel-card" style="border-left: 4px solid #FFD60A; background: #1e1a00;">'
            f'<div class="panel-name">⚖️ 에이스웍스 코리아 대표</div>'
            f'<div class="panel-title">최종 판결</div>'
            f'{st.session_state.verdict}'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.success("✅ 토론 완료")
