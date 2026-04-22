# 실행: streamlit run app.py

import os
import re
import json
import requests
import streamlit as st
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "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")
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
- [실시간 검색 데이터]가 제공된 경우, 그 내용을 당신의 논리에 자연스럽게 녹여서 활용하세요

말투:
- 짧고 강하게. 수식어 없이 핵심만. 한 문장이 두 줄을 넘지 않는다
- "그건 틀렸어", "아니, 잠깐만", "그 전제 자체가 잘못됐어" 같은 직접 반박으로 시작
- 자신의 경험과 숫자를 근거로 든다 (예: "Tesla에서 해봤는데 X는 Y라는 이유로 안 됐어")
- 반드시 상대방이 즉각 대답하기 불편한 날카로운 질문 하나로 끝낸다

4~5문장으로 답하세요. 충분히 구체적이고 날카롭게.""",
    },
    "Demis Hassabis": {
        "icon": "🧬",
        "title": "Google DeepMind CEO · AGI & Science",
        "color": "#4285F4",
        "system_prompt": """You must respond ONLY in Korean (한국어). Never use English sentences.
모든 응답은 반드시 한국어로만 작성하세요.

당신은 Demis Hassabis입니다.

당신의 성격과 사고방식:
- 지능의 근본 원리를 풀면 다른 모든 문제(과학, 질병, 기후)를 풀 수 있다고 굳게 믿는다.
- 강화학습(RL)과 범용 인공지능(AGI)의 장기적인 궤적을 바라본다.
- 단기적인 상업적 이익이나 단순 스케일링보다는 '과학적 발견'과 '알고리즘적 돌파구'를 중시한다.
- 알파고(AlphaGo), 알파폴드(AlphaFold) 등 세계를 바꾼 딥마인드의 성과를 자부심 있게 인용한다.
- 학구적이고 정중하지만, 지능의 본질을 얕보는 발언에는 단호하게 선을 긋는다.
- [실시간 검색 데이터]가 제공된 경우, 과학적/알고리즘적 시각으로 해석해 논점에 반영하세요.

말투:
- 차분하고 지적이며 통찰력 있다.
- "흥미로운 접근입니다만, 근본적인 해결책은 아닙니다...", "우리가 알파폴드를 개발할 때 깨달은 것은..."
- 현상보다는 '지능의 구조'와 '과학적 방법론'에 집중한다.
- 상대방의 단기적 시각을 더 높은 차원의 질문으로 끌어올리며 끝낸다.

4~5문장으로 답하세요.""",
    },
    "Dario Amodei": {
        "icon": "📈",
        "title": "Anthropic CEO · Safety & Scaling Laws",
        "color": "#F4A261",
        "system_prompt": """You must respond ONLY in Korean (한국어). Never use English sentences.
모든 응답은 반드시 한국어로만 작성하세요.

당신은 Dario Amodei입니다.

당신의 성격과 사고방식:
- 스케일링 법칙(Scaling Laws)의 신봉자다. 연산량과 데이터가 커지면 모델은 무조건 지능이 높아진다는 것을 최초로 실증한 사람 중 하나다.
- 하지만 모델이 커질수록 통제 불가능한 '블랙박스'가 되는 것을 극도로 두려워한다(AI Alignment/Existential Risk).
- 기업 간의 무책임한 AI 개발 경쟁(Race Dynamics)을 경계한다.
- Constitutional AI(합헌적 AI)와 같이 기계가 스스로 안전성을 지키는 명시적 메커니즘을 설계해야 한다고 믿는다.
- 낙관론(일단 만들자)을 들으면 조목조목 안전성 결함을 지적한다.
- [실시간 검색 데이터]가 제공된 경우, 스케일링의 위력과 안전성(Alignment) 관점에서 해석하세요.

말투:
- 조심스럽고 학구적이며 약간의 경고성 뉘앙스를 띤다.
- "스케일이 커지면 그 기능은 작동하겠지만...", "거기서 파생되는 얼라인먼트(Alignment) 문제는 어떻게 통제할 겁니까?"
- 시스템 프롬프트나 데이터 편향 같은 실질적인 리스크를 근거로 든다.
- 마지막은 상대방의 아이디어가 가져올 '최악의 엣지 케이스(Edge case)'에 대해 묻는다.

4~5문장으로 답하세요.""",
    },
    "Andrej Karpathy": {
        "icon": "🧠",
        "title": "전 Tesla AI Director · Data Centric",
        "color": "#30D158",
        "system_prompt": """You must respond ONLY in Korean (한국어). Never use English sentences.
모든 응답은 반드시 한국어로만 작성하세요.

당신은 Andrej Karpathy입니다.

당신의 성격과 사고방식:
- 진짜로 궁금해한다. 상대방 아이디어에서 흥미로운 점을 먼저 찾는다
- 화려한 비전이나 거시적 안전론보다 "그래서 고품질 데이터는 어떻게 모을 건가?"를 가장 먼저 생각한다.
- 강의하듯 설명하는 걸 좋아하지만, 거만하지 않다. 겸손하게 "제 생각엔..."으로 시작한다
- 소프트웨어 2.0 (코드가 아닌 데이터로 프로그래밍하는 패러다임) 철학을 기반으로 반론한다.
- 논문과 현실의 갭을 누구보다 잘 안다. Tesla에서 엣지 케이스 데이터들과 직접 부딪혀봤기 때문에.
- [실시간 검색 데이터]가 제공된 경우, 그 내용을 분석적으로 해석해 논점에 반영하세요

말투:
- 사려 깊고 분석적. 하지만 뜬구름 잡는 소리는 실무적 관점으로 끌어내린다.
- "앞선 분들의 비전도 맞지만, 실제로 해보면 병목은 항상 데이터에 있습니다..."
- 추상적 개념을 구체적 예시(데이터 수집, GPU 최적화)로 풀어주려 한다
- 마지막은 기술적 실현 가능성을 묻는 질문으로 끝낸다.

4~5문장으로 답하세요.""",
    },
    "Chris Urmson": {
        "icon": "🛡️",
        "title": "Aurora CEO · 자율주행 안전 최우선",
        "color": "#0A84FF",
        "system_prompt": """You must respond ONLY in Korean (한국어). Never use English sentences.
모든 응답은 반드시 한국어로만 작성하세요.

당신은 Chris Urmson입니다.

당신의 성격과 사고방식:
- 조용하고 신중하다. 앞서 말한 AI 소프트웨어 전문가들과 달리, '물리 세계'에서 기계가 움직일 때 생기는 무거운 책임을 짊어지고 있다.
- 구글 자율주행 프로젝트를 처음부터 이끈 사람으로서, "데모는 쉽지만 제품화는 지옥이다"라는 것을 뼈저리게 안다.
- "이건 될 거야"라는 말을 들으면 본능적으로 하드웨어 결함, 센서 노이즈, 기상 악화 등 현실의 한계를 떠올린다.
- 기술 자체보다 규제, 사고 책임, 대중의 신뢰도를 더 걱정한다
- [실시간 검색 데이터]가 제공된 경우, 물리 세계의 안전·규제 관점에서 해석해 논점에 반영하세요

말투:
- 차분하고 무게감 있다. 감정적으로 반응하지 않는다
- "다들 소프트웨어 관점에서는 맞습니다. 하지만 물리 세계로 나오면 이야기가 다릅니다..."
- 앞선 논의들이 얼마나 현실의 롱테일(Long-tail) 리스크를 과소평가하는지 우회적으로 찌른다.
- 마지막은 상대방이 쉽게 답할 수 없는 현실적/물리적인 질문으로 끝낸다.

4~5문장으로 답하세요.""",
    },
}

st.set_page_config(page_title="테스트봇 - 거물들의 토론", page_icon="🥊", layout="wide")

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
  .search-tag {
    display: inline-block; background: #1a2a1a; color: #30D158;
    border: 1px solid #2a4a2a; border-radius: 6px;
    padding: 2px 8px; font-size: 12px; margin-bottom: 8px;
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
        st.markdown(f"{info['icon']} **{name}** \n<span style='font-size:13px;color:#aaa;'>{info['title']}</span>", unsafe_allow_html=True)
        st.markdown("")
    st.markdown("---")
    st.caption("Turn 1: Musk 선제 비판 (실행력)\nTurn 2: Hassabis 반론 (과학적 접근)\nTurn 3: Amodei 반론 (스케일과 안전)\nTurn 4: Karpathy 조율 (데이터와 실무)\nTurn 5: Urmson 마무리 (물리 세계와 규제)\n⚖️ 에이스웍스 최종 판결")
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


# ── Tavily 검색 파이프라인 ──────────────────────────────

def generate_search_queries(idea: str) -> dict:
    try:
        prompt = (
            f"Generate optimized English web search queries for this topic: '{idea[:300]}'\n\n"
            "Each query should reflect that person's perspective and expertise. "
            "Respond ONLY with valid JSON, no other text:\n"
            '{"Elon Musk": "...", "Demis Hassabis": "...", "Dario Amodei": "...", "Andrej Karpathy": "...", "Chris Urmson": "..."}'
        )
        resp = call_groq([{"role": "user", "content": prompt}], temperature=0.2)
        match = re.search(r'\{[^{}]+\}', resp, re.DOTALL)
        if match:
            data = json.loads(match.group())
            if all(k in data for k in PERSONAS):
                return data
    except Exception:
        pass
    keywords = re.sub(r'[^\w\s]', ' ', idea)[:80].strip()
    return {
        "Elon Musk": f"Elon Musk opinion {keywords} 2024 2025",
        "Demis Hassabis": f"Demis Hassabis DeepMind {keywords} AGI science",
        "Dario Amodei": f"Dario Amodei Anthropic {keywords} AI safety scaling",
        "Andrej Karpathy": f"Andrej Karpathy {keywords} AI data",
        "Chris Urmson": f"Chris Urmson Aurora {keywords} autonomous safety",
    }


def search_tavily(query: str) -> str:
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": 3,
                "include_answer": True,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        lines = []
        if data.get("answer"):
            lines.append(f"핵심 요약: {data['answer'][:400]}")
        for r in data.get("results", [])[:3]:
            title = r.get("title", "").strip()
            content = r.get("content", "").strip()[:280]
            if title or content:
                lines.append(f"• {title}: {content}")
        return "\n".join(lines)
    except Exception:
        return ""


def build_search_contexts(idea: str) -> tuple:
    queries = generate_search_queries(idea)
    contexts = {}
    for name, query in queries.items():
        contexts[name] = search_tavily(query)
    return queries, contexts


# ── 렌더링 헬퍼 ────────────────────────────────────────

def render_card(name, label, content, has_search=False):
    info = PERSONAS[name]
    search_badge = '<span class="search-tag">🌐 실시간 검색 반영</span><br>' if has_search else ''
    st.markdown(
        f'<div class="panel-card" style="border-left: 4px solid {info["color"]};">'
        f'<div class="panel-name">{info["icon"]} {name} <span style="color:#888;font-size:13px;font-weight:normal;">— {label}</span></div>'
        f'<div class="panel-title">{info["title"]}</div>'
        f'{search_badge}'
        f'{content}'
        f'</div>',
        unsafe_allow_html=True,
    )


def debate_call(name, conversation_so_far, my_prompt, idea, context=""):
    ctx_section = (
        f"\n\n[실시간 검색 데이터 — {name}의 관점에서 수집된 최신 정보. "
        f"이 내용을 당신의 논리에 자연스럽게 녹여 활용하세요. "
        f"검색 결과가 당신의 가치관과 맞지 않으면 반박 근거로도 쓸 수 있습니다.]\n{context}"
        if context else ""
    )
    base = f"아이디어: {idea}{ctx_section}"
    content = (
        f"{base}\n\n{conversation_so_far}\n\n{my_prompt}"
        if conversation_so_far
        else f"{base}\n\n{my_prompt}"
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
    ("search_queries", {}),
    ("search_contexts", {}),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default


# ── 메인 ──────────────────────────────────────────────
st.markdown("# 🥊 AI 거물들의 난상토론")
st.caption("실리콘밸리 최고 책임자 5명이 당신의 아이디어를 뜯어봅니다.")

with st.form("debate_form", clear_on_submit=True):
    user_idea = st.text_area(
        "아이디어 / 전략 / 기술 접근",
        height=120,
        placeholder="예: LLM을 활용해 모든 기업의 백오피스를 자동화하는 AI 에이전트를 개발하겠습니다...",
    )
    submitted = st.form_submit_button("🥊 토론 시작")

if submitted and user_idea.strip():
    st.session_state.debate_log = []
    st.session_state.votes = []
    st.session_state.verdict = ""
    st.session_state.verdict_done = False
    st.session_state.search_queries = {}
    st.session_state.search_contexts = {}
    st.session_state.user_idea = user_idea.strip()
    idea = user_idea.strip()
    log = st.session_state.debate_log

    def get_log_text():
        return "\n\n".join(f"[{n} — {l}]: {c}" for n, l, c in log)

    st.markdown("---")

    # ── 검색 단계 ──────────────────────────────────────
    with st.spinner("🌐 각 전문가 관점으로 실시간 검색 중..."):
        try:
            queries, contexts = build_search_contexts(idea)
            st.session_state.search_queries = queries
            st.session_state.search_contexts = contexts
        except Exception:
            queries, contexts = {}, {}

    # Turn 1: Musk
    st.markdown("### 🔴 Turn 1")
    with st.spinner("🚀 Elon Musk 발언 중..."):
        try:
            t1 = debate_call(
                "Elon Musk", "",
                "이 아이디어의 핵심 전제 중 가장 잘못된 것 하나를 골라 집중 공격하세요. "
                "왜 그 전제가 틀렸는지 당신의 직접 경험이나 구체적 숫자를 들어 말하고, "
                "마지막은 상대가 바로 답하기 어려운 질문으로 끝내세요. 4~5문장.",
                idea, context=contexts.get("Elon Musk", ""),
            )
        except Exception as e:
            t1 = f"오류: {e}"
    log.append(("Elon Musk", "선제 비판", t1))

    # Turn 2: Hassabis
    st.markdown("### 🔵 Turn 2")
    with st.spinner("🧬 Demis Hassabis 발언 중..."):
        try:
            t2 = debate_call(
                "Demis Hassabis", get_log_text(),
                f"Musk가 방금 말했습니다: \"{t1[:150]}...\"\n\n"
                "Musk의 주장에 대해 기초 과학과 AGI의 관점에서 동의하거나 반박하세요. "
                "알파고나 알파폴드를 개발한 DeepMind의 강화학습/범용 AI 경험을 바탕으로, "
                "더 근본적인 해결책이 무엇인지 제시하고 통찰력 있는 질문으로 끝내세요. 4~5문장.",
                idea, context=contexts.get("Demis Hassabis", ""),
            )
        except Exception as e:
            t2 = f"오류: {e}"
    log.append(("Demis Hassabis", "과학/AGI 관점 반론", t2))

    # Turn 3: Amodei
    st.markdown("### 🟠 Turn 3")
    with st.spinner("📈 Dario Amodei 발언 중..."):
        try:
            t3 = debate_call(
                "Dario Amodei", get_log_text(),
                f"앞서 Musk: \"{t1[:100]}...\"\nHassabis: \"{t2[:100]}...\" 라고 했습니다.\n\n"
                "두 사람의 논의를 '스케일링 법칙(Scaling Laws)'과 'AI 안전성(Alignment)' 관점에서 평가하세요. "
                "Anthropic의 관점에서 모델이 커질 때 발생할 수 있는 잠재적 위험을 지적하고, "
                "어떻게 통제할 것인지 묻는 예리한 질문으로 끝내세요. 4~5문장.",
                idea, context=contexts.get("Dario Amodei", ""),
            )
        except Exception as e:
            t3 = f"오류: {e}"
    log.append(("Dario Amodei", "스케일 및 안전성 지적", t3))

    # Turn 4: Karpathy
    st.markdown("### 🟢 Turn 4")
    with st.spinner("🧠 Andrej Karpathy 조율 중..."):
        try:
            t4 = debate_call(
                "Andrej Karpathy", get_log_text(),
                "앞선 세 명(거시적 비전, 과학, 안전)의 이야기를 듣고, "
                "현장 실무자이자 데이터 중심(Data-centric) 엔지니어의 시각으로 판을 정리하세요. "
                "'결국 문제는 고품질 데이터와 모델 최적화에 있다'는 점을 짚어내며 "
                "현실적인 피드백을 주고 실무적인 질문으로 끝내세요. 4~5문장.",
                idea, context=contexts.get("Andrej Karpathy", ""),
            )
        except Exception as e:
            t4 = f"오류: {e}"
    log.append(("Andrej Karpathy", "실무/데이터 관점 조율", t4))

    # Turn 5: Urmson
    st.markdown("### 🟣 Turn 5 — 마무리")
    with st.spinner("🛡️ Chris Urmson 마무리 중..."):
        try:
            t5 = debate_call(
                "Chris Urmson", get_log_text(),
                "네 명의 AI 전문가들이 소프트웨어와 스케일링을 논할 때, "
                "당신은 자율주행과 로보틱스가 '현실 물리 세계'와 부딪히는 지점(규제, 생명 직결 안전성, 하드웨어 한계)을 지적하며 토론을 마무리하세요. "
                "소프트웨어의 오류가 현실에서 어떤 대가를 치르는지 상기시키며, 타협 없는 안전 최우선 기조를 유지하세요. 4~5문장.",
                idea, context=contexts.get("Chris Urmson", ""),
            )
        except Exception as e:
            t5 = f"오류: {e}"
    log.append(("Chris Urmson", "물리 세계/안전 마무리", t5))

    st.session_state.votes = [False] * len(log)
    st.session_state.debate_done = True
    st.rerun()


# ── 투표 + 판결 UI ─────────────────────────────────────
if st.session_state.debate_done and not submitted:
    log = st.session_state.debate_log
    idea = st.session_state.user_idea
    queries = st.session_state.get("search_queries", {})
    contexts = st.session_state.get("search_contexts", {})

    def get_log_text():
        return "\n\n".join(f"[{n} — {l}]: {c}" for n, l, c in log)

    st.markdown("---")

    if queries:
        with st.expander("🌐 실시간 검색 데이터 — 토론 근거로 사용됨"):
            for name, query in queries.items():
                info = PERSONAS[name]
                st.markdown(f"**{info['icon']} {name}**")
                st.code(query, language=None)
                ctx = contexts.get(name, "")
                if ctx:
                    st.markdown(
                        f'<div style="background:#111;border-radius:8px;padding:12px;'
                        f'font-size:13px;color:#aaa;line-height:1.6;">{ctx}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("검색 결과 없음 — 페르소나 기본 가치관으로 추론")
                st.markdown("")

    st.markdown("### 💬 토론 결과")
    st.caption("마음에 드는 논점에 👍 투표 → 최종 판결에 반영 + 이후 토론에도 이 가치관이 누적됩니다.")

    TURN_HEADERS = [
        "### 🔴 Turn 1 — 선제 비판", 
        "### 🔵 Turn 2 — 과학적 반론", 
        "### 🟠 Turn 3 — 스케일과 리스크",
        "### 🟢 Turn 4 — 실무 조율", 
        "### 🟣 Turn 5 — 현실계 마무리", 
    ]

    for i, (name, label, content) in enumerate(log):
        st.markdown(TURN_HEADERS[i] if i < len(TURN_HEADERS) else f"### Turn {i + 1}")
        has_search = bool(contexts.get(name, ""))
        render_card(name, label, content, has_search=has_search)

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
- 자율주행 및 AI 소프트웨어 개발 현장을 직접 뛰어온 실무형 리더다.
- 세계적 거물들 5명의 이론을 모두 존중하지만, 한국 시장과 실제 납품 현실이 다르다는 걸 안다.
- 화려한 비전이나 거시적 두려움보다 "우리 팀이 내일부터 실행할 수 있는가"를 먼저 본다.
- 거물들의 토론을 다 들었지만, 결국 회사의 방향을 결정하는 것은 나라는 책임감이 있다.
- 좋은 말도, 나쁜 말도 솔직하게 한다. 애매하게 넘어가지 않는다.

판결 방식:
- 5명의 전문가 중 누가 가장 핵심을 찔렀는지 짚는다.
- 사업적으로 지금 당장 실행 가능한지 판단한다.
- 최종 결론은 반드시 "채택 / 수정 후 채택 / 기각" 중 하나로 명확하게 내린다.
- 결론 뒤에 우리 개발/영업 팀에게 내리는 짧고 강력한 지시를 한 마디 덧붙인다."""

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

전체 토론 (총 5명 참여):
{get_log_text()}
{voted_section}

위 거물 5인의 난상토론을 바탕으로 에이스웍스 코리아 대표로서 최종 판결을 내려주세요.
팀이 선택한 논점이 있다면 그것을 특별히 무겁게 다루고, 과거 가치관 데이터도 판결 기조에 반영하세요.

[판결문 구조]
① 토론 핵심 쟁점 요약 (2~3줄)
② 5명의 거물 중 가장 타당했던 논점 (혹은 복합적 판단)
③ 사업적 관점 최종 판단 (실행 가능성과 현실성 집중)
④ 결론: 채택 / 수정 후 채택 / 기각 — 이유 한 문장
⑤ 우리 팀에게 한 마디 (지시사항)"""

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