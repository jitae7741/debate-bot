# 실행: streamlit run app.py
# 환경변수 필요: GROQ_API_KEY, TAVILY_API_KEY (.env 또는 셸 export)

import os
import re
import json
import time
import requests
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
VOTES_FILE = "votes_history.json"
PERSONA_CACHE_FILE = "personas_cache.json"

COLOR_POOL = [
    "#FF3B30", "#4285F4", "#F4A261", "#30D158", "#0A84FF",
    "#BF5AF2", "#FFD60A", "#FF9500", "#5AC8FA", "#FF2D55",
]
DEFAULT_ICONS = ["🎯", "🧠", "📈", "🛡️", "🚀", "🧬", "💡", "⚙️", "🔬", "📊"]

# 에이스웍스 코리아 회사 배경 — 판결자(대표) 페르소나가 사업 현실에 기반해 판단하기 위한 컨텍스트
COMPANY_BACKGROUND = """[에이스웍스 코리아 회사 개요]

정체성:
- 미래 모빌리티 제어 기술의 핵심 파트너를 지향하는 한국 모빌리티 테크 기업.
- 친환경/자율주행 제어 기술을 글로벌 모빌리티 기업에 공급. B2B 엔지니어링 회사.
- 2024년 컨트롤웍스(EV 검증/HILS) + 에이스랩(자율주행 토탈 솔루션) 합병으로 "에이스웍스코리아" 브랜드 출범.
- 핵심 가치: Agile(빠르게), Cost-conscious(효율적으로), Proven(검증된).

규모와 거점:
- 임직원 90+, 제품 20+, 시설 3곳, 누적 고객사 300+ (개인 고객 3,000+).
- 매출 2021년 대비 3배 이상 성장. 2023년 미국 LA(Torrance) 사무소 개설.
- 본사: 서울 강남. R&D/시험: 용인 ATC(자율주행 센터), 청주 오창 R&D 센터. 지방 거점: 대구, 광주.
- 글로벌 파트너십: Vector(독일), Robosense(중국).

사업 영역 — EV/HEV/PHEV 파워트레인 HILS:
- Inverter/MCU HILS, OBC(On-Board Charger) HILS, BMS HILS(셀 256개 ±1mV), LDC/BHDC HILS, VCU HILS(CarMaker/PreScan 연동).
- 열관리/보조: eCF, eCOMP(10,000rpm PMSM), BPCU(150,000rpm).
- 수소 연료전지: FCU HILS, HMU HILS.
- 상용차: EBS HILS(중대형 트럭/수소트럭).
- 비전/모니터링: 빌트인 카메라(Dashcam) 개발 키트, DMS(Driver Monitoring) HILS.
- 조명: LDM(LED Drive Module) HILS.
- 통합: Multi-Domain HIL.

자율주행 토탈 솔루션:
- 자율주행 풀스택 — 인지/측위/판단/제어, 시뮬레이션, 데이터 수집/검증.
- NI VeriStand·TestStand·ECU-TEST·CarMaker·CarSim·TruckSim·Simulink, Vector VT 시스템 연동.

고객 특성:
- 주요 고객은 글로벌 OEM과 1차 부품사. 한국·일본·미국·중국 자동차 산업이 핵심 시장.
- 고객 엔지니어들이 직접 쓰는 제품 — 임베디드 HW/SW 검증, 모델링, FPGA 기반 실시간 시뮬레이션 깊이 요구.

경쟁 포지션:
- 한국 EV 검증 HILS 시장 1위(컨트롤웍스 유산) + 자율주행 토탈 솔루션(에이스랩 유산) 결합.
- "빠르고 저렴하고 검증된" — 글로벌 NI/dSPACE 대비 가격·맞춤·납기 강점.
"""

st.set_page_config(
    page_title="아이디어 토론장",
    page_icon="🥊",
    layout="wide",
    menu_items={},
)

st.markdown(
    """
<style>
  /* Streamlit 기본 chrome 숨김 */
  #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
  div[data-testid="stToolbar"] { display: none; }
  div[data-testid="stDecoration"] { display: none; }
  div[data-testid="stStatusWidget"] { display: none; }

  body, .stApp { background-color: #0d0d0d; color: #f0f0f0; }
  .block-container { padding-top: 2rem; }

  .stTextArea textarea {
    background: #1a1a1a !important; color: #f0f0f0 !important;
    border: 1px solid #333 !important; font-size: 16px; border-radius: 12px;
  }

  /* Primary buttons (메인 CTA) */
  .stButton > button[kind="primary"], .stFormSubmitButton > button {
    background-color: #FF3B30 !important;
    color: white !important;
    border: none !important;
    height: 50px !important;
    border-radius: 12px !important;
    font-size: 16px !important;
    font-weight: bold !important;
    width: 100% !important;
  }
  .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover {
    background-color: #cc2e25 !important;
  }

  /* Secondary buttons (선택/투표/뒤로) */
  .stButton > button[kind="secondary"] {
    background-color: #1f1f1f !important;
    color: #ddd !important;
    border: 1px solid #444 !important;
    height: 40px !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    font-weight: normal !important;
    width: 100% !important;
  }
  .stButton > button[kind="secondary"]:hover {
    background-color: #2a2a2a !important;
    border-color: #666 !important;
  }

  .panel-card {
    background: #1a1a1a;
    border-radius: 12px; padding: 18px; margin: 12px 0;
    font-size: 15px; line-height: 1.75;
  }
  .panel-name { font-size: 17px; font-weight: bold; margin-bottom: 4px; }
  .panel-title { font-size: 13px; color: #888; margin-bottom: 14px; }
  .panel-content {
    white-space: pre-line;
    word-break: keep-all;
    overflow-wrap: anywhere;
  }

  .summary-card {
    background: #14241e;
    border: 1px solid #1f3d2f;
    border-radius: 12px; padding: 18px; margin: 12px 0;
    font-size: 14px; line-height: 1.7;
    color: #d8e8df;
    white-space: pre-line;
    word-break: keep-all;
    overflow-wrap: anywhere;
  }

  .pick-card {
    background: #161616;
    border-radius: 12px;
    padding: 14px 14px 8px 14px;
    margin: 6px 0;
    border: 1px solid #2a2a2a;
  }
  .pick-card .pn { font-size: 15px; font-weight: bold; margin-bottom: 2px; }
  .pick-card .pt { font-size: 12px; color: #888; margin-bottom: 8px; }
  .pick-card .pa {
    font-size: 13px; color: #b8c5d6; line-height: 1.55;
    white-space: pre-line;
  }

  .search-tag {
    display: inline-block; background: #1a2a1a; color: #30D158;
    border: 1px solid #2a4a2a; border-radius: 6px;
    padding: 2px 8px; font-size: 12px; margin-bottom: 8px;
  }

  h1 { color: #FF3B30 !important; font-size: 26px !important; }
  h3 { color: #f0f0f0 !important; }
  label { font-size: 15px !important; color: #ccc !important; }
  hr { border-color: #2a2a2a; }
</style>
""",
    unsafe_allow_html=True,
)


# ── 파일 I/O ───────────────────────────────────────────

def _load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_vote_history():
    return _load_json(VOTES_FILE, [])


def save_vote_history(new_votes: list):
    history = load_vote_history()
    history.extend(new_votes)
    history = history[-80:]
    _save_json(VOTES_FILE, history)


def load_persona_cache():
    return _load_json(PERSONA_CACHE_FILE, {})


def save_persona_cache(cache: dict):
    _save_json(PERSONA_CACHE_FILE, cache)


# ── LLM/검색 코어 ────────────────────────────────────

def clean_response(text: str) -> str:
    cleaned = re.sub(r"[一-鿿぀-ヿЀ-ӿ㐀-䶿＀-￯]", "", text)
    return re.sub(r"[ \t]{2,}", " ", cleaned).strip()


def call_groq(messages, temperature: float = 0.8, max_tokens: int = 900) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY 환경변수가 설정되지 않았습니다. .env 또는 셸에 export 하세요.")
    client = Groq(api_key=GROQ_API_KEY)
    last_err = None
    for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return clean_response(resp.choices[0].message.content)
        except Exception as e:
            last_err = e
            err = str(e).lower()
            if "429" in str(e) or "rate_limit" in err or "quota" in err:
                continue
            raise
    raise RuntimeError(f"모든 Groq 모델 한도 초과: {last_err}")


def _extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 배열 우선 시도
    s, e = text.find("["), text.rfind("]")
    if s != -1 and e > s:
        try:
            return json.loads(text[s : e + 1])
        except json.JSONDecodeError:
            pass
    # 객체 시도
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e > s:
        try:
            return json.loads(text[s : e + 1])
        except json.JSONDecodeError:
            pass
    return None


def search_tavily(query: str, max_results: int = 4) -> str:
    if not TAVILY_API_KEY:
        return ""
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": True,
            },
            timeout=12,
        )
        resp.raise_for_status()
        data = resp.json()
        lines = []
        if data.get("answer"):
            lines.append(f"핵심 요약: {str(data['answer'])[:500]}")
        for r in data.get("results", [])[:max_results]:
            title = str(r.get("title", "")).strip()
            content = str(r.get("content", "")).strip()[:300]
            if title or content:
                lines.append(f"• {title}: {content}")
        return "\n".join(lines)
    except Exception:
        return ""


def parallel_search(queries: dict, timeout: int = 20) -> dict:
    results = {k: "" for k in queries}
    if not queries:
        return results
    with ThreadPoolExecutor(max_workers=min(8, len(queries))) as ex:
        future_to_key = {ex.submit(search_tavily, q): k for k, q in queries.items()}
        for fut in as_completed(future_to_key):
            k = future_to_key[fut]
            try:
                results[k] = fut.result(timeout=timeout)
            except Exception:
                results[k] = ""
    return results


# ── 파이프라인 단계 ─────────────────────────────────────

def research_topic(idea: str) -> tuple:
    """주제 광범위 리서치 → (raw_search, summary)"""
    queries = {
        "news": f"{idea} latest news 2025 2026",
        "tech": f"{idea} technical analysis market trends",
        "critique": f"{idea} criticism risks failure cases",
        "academic": f"{idea} research paper academic study",
    }
    results = parallel_search(queries)
    raw = "\n\n".join(f"[{k.upper()}]\n{v}" for k, v in results.items() if v)

    if not raw:
        return "", "외부 검색 결과가 없습니다 — 페르소나의 일반 도메인 지식만으로 토론합니다."

    summary_prompt = (
        f"다음은 '{idea[:300]}'에 대한 실시간 외부 검색 결과(뉴스·기술·비판·학술)입니다.\n\n"
        f"{raw[:5500]}\n\n"
        "위 자료를 바탕으로 한국어로 요약하세요. 다음을 포함:\n"
        "1) 주제의 핵심 맥락 (3~4문장)\n"
        "2) 주요 논쟁점·리스크 (3~5개)\n"
        "3) 최근 동향과 사실 (2~3개)\n\n"
        "마크다운 표기(**, ##, ---) 금지. 평문 + 줄바꿈만 사용. "
        "검색에 없는 사실은 추가하지 마세요. 모르면 모른다고 쓰세요."
    )
    try:
        summary = call_groq(
            [{"role": "user", "content": summary_prompt}],
            temperature=0.3,
            max_tokens=1000,
        )
    except Exception as e:
        summary = f"요약 생성 실패: {e}"
    return raw, summary


def brainstorm_critics(idea: str, summary: str) -> list:
    """주제에 적합한 비평가 후보 8~10명 추천"""
    prompt = f"""주제: {idea}

관련 자료 요약:
{summary[:1800]}

위 주제에 대해 가장 날카롭고 다양한 비판을 할 만한 실제 인물(생존 또는 최근 활발히 활동) 8~10명을 추천하세요.

다양성 기준:
- 분야: 기술/엔지니어링, 비즈니스/전략, 안전/규제, 디자인/제품, 재무/투자, 운영/실행 중 최소 3~4개 분야 포함
- 입장: 낙관적 vs 회의적 양쪽 모두 포함
- 지역: 글로벌 + 한국 양쪽 고려 (한국 산업/시장과 직결되는 주제면 한국 전문가 우선)
- 최근 5년 내 공개 발언, 저술, 인터뷰가 있는 실존 인물

응답은 ONLY 유효한 JSON 배열. 코드 펜스(```) 절대 금지. 다른 설명 금지:
[
  {{"name": "정확한 본명 (한글 또는 영문)", "role": "현재 직책 또는 대표 활동", "why": "이 주제에 왜 적합한지 한 줄"}}
]
"""
    try:
        resp = call_groq(
            [{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=1400,
        )
        data = _extract_json(resp)
        if isinstance(data, list):
            valid = []
            seen = set()
            for d in data:
                if not isinstance(d, dict):
                    continue
                name = str(d.get("name", "")).strip()
                role = str(d.get("role", "")).strip()
                why = str(d.get("why", "")).strip()
                if not name or name in seen:
                    continue
                seen.add(name)
                valid.append({"name": name, "role": role, "why": why})
                if len(valid) >= 10:
                    break
            return valid
    except Exception:
        pass
    return []


def synthesize_persona(name: str, role: str, why: str, idea: str, search_data: str) -> dict:
    """검색 데이터로 페르소나 카드 합성. 검색 부족하면 보수적으로 작성."""
    has_search = bool(search_data and search_data.strip())
    search_section = (
        search_data[:2500] if has_search else "(검색 결과 없음 — 일반에 알려진 직책·업적에 한해 보수적으로 작성)"
    )
    prompt = f"""주제 컨텍스트: {idea}

대상 인물: {name}
역할: {role}
이 주제 적합성: {why}

이 인물에 대한 실시간 검색 데이터:
{search_section}

위 검색 데이터를 근거로 이 인물의 토론 페르소나 카드를 만드세요.

엄격한 제약:
- 검색에 없는 인용·일화·발언을 만들어내지 마세요. 추측 금지.
- 검색이 빈약하면 그 인물의 잘 알려진 직책·대표 업적·공개 입장에만 한정해 작성.
- system_prompt는 한국어로, 토론 참여용으로 작성.

응답은 ONLY 유효한 JSON 객체. 코드 펜스 금지. 다른 설명 금지:
{{
  "title": "직책 · 핵심 관점 한 줄",
  "icon": "이모지 1개",
  "critique_angle": "이 주제에 대해 어떤 각도로 비판할지 한 줄 (한국어)",
  "system_prompt": "이 인물의 토론 페르소나 system prompt. 다음을 모두 포함하세요. (영어/한글 섞임 OK)\\n\\nYou must respond ONLY in Korean (한국어). Never use English sentences.\\n모든 응답은 반드시 한국어로만 작성하세요.\\n마크다운 표기(**, ##, ---, * 목록 등)는 절대 사용하지 마세요. 평문만으로 작성하고, 단락 구분은 줄바꿈으로 표시하세요.\\n\\n당신은 {name}입니다.\\n\\n당신의 성격과 사고방식:\\n- (4~6개 항목, 그 인물의 알려진 스타일·관점에 기반)\\n\\n말투:\\n- (3~4개 항목, 구체적 시작 어구나 표현 포함)\\n\\n[실시간 검색 데이터]가 user 메시지에 포함되면 그 내용을 자연스럽게 활용하세요. 검색에 없는 인용은 만들지 마세요.\\n\\n5~6문장으로 답하세요. 추상적 일반론 금지, 구체 사실·숫자·사례 최소 1개 포함."
}}
"""
    try:
        resp = call_groq(
            [{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1600,
        )
        data = _extract_json(resp)
        if (
            isinstance(data, dict)
            and isinstance(data.get("system_prompt"), str)
            and isinstance(data.get("title"), str)
            and len(data["system_prompt"]) > 80
        ):
            return {
                "name": name,
                "role": role,
                "why": why,
                "title": data.get("title", role),
                "icon": str(data.get("icon", "💬"))[:4],
                "critique_angle": str(data.get("critique_angle", why))[:200],
                "system_prompt": data["system_prompt"],
                "search_basis": search_data[:1200] if has_search else "",
            }
    except Exception:
        pass

    # Fallback: 최소 페르소나
    return {
        "name": name,
        "role": role,
        "why": why,
        "title": role or "비평가",
        "icon": "💬",
        "critique_angle": why or "비판적 관점",
        "system_prompt": (
            "You must respond ONLY in Korean (한국어). Never use English sentences.\n"
            "모든 응답은 반드시 한국어로만 작성하세요.\n"
            "마크다운 표기(**, ##, ---, * 목록 등)는 절대 사용하지 마세요. 평문만으로 작성하고, 단락 구분은 줄바꿈으로 표시하세요.\n\n"
            f"당신은 {name}입니다. 역할: {role}.\n\n"
            "당신의 알려진 공개 활동과 직책에 기반해 비판적으로 토론에 참여합니다. "
            "추측이나 만들어낸 인용은 사용하지 않습니다. 모르는 영역은 솔직히 인정합니다.\n\n"
            "5~6문장으로 답하되 추상적 일반론 금지, 구체 사실·숫자·사례 최소 1개 포함."
        ),
        "search_basis": search_data[:1200] if has_search else "",
    }


def build_personas(candidates: list, idea: str) -> list:
    """후보 → 페르소나 카드 (병렬 검색 + 병렬 합성, 캐시 활용)"""
    if not candidates:
        return []

    # 1) 검색 병렬
    queries = {
        c["name"]: f'"{c["name"]}" {c.get("role","")} opinion view critique recent statements'
        for c in candidates
    }
    search_results = parallel_search(queries)

    # 2) 페르소나 합성 병렬 (max_workers=4 — Groq rate limit 보호)
    cache = load_persona_cache()
    cards = [None] * len(candidates)

    def synth_one(i, c):
        sd = search_results.get(c["name"], "")
        cached = cache.get(c["name"].strip())
        if cached and isinstance(cached, dict) and cached.get("system_prompt"):
            return i, {
                **cached,
                "name": c["name"],
                "role": c.get("role", cached.get("role", "")),
                "why": c.get("why", cached.get("why", "")),
                "search_basis": sd[:1200] if sd else cached.get("search_basis", ""),
            }
        card = synthesize_persona(c["name"], c.get("role", ""), c.get("why", ""), idea, sd)
        # 캐시 저장 (fallback이 아닌 경우만)
        if card.get("system_prompt") and len(card["system_prompt"]) > 200:
            cache[c["name"].strip()] = {**card, "cached_at": int(time.time())}
        return i, card

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(synth_one, i, c) for i, c in enumerate(candidates)]
        for fut in as_completed(futures):
            try:
                i, card = fut.result(timeout=45)
                cards[i] = card
            except Exception:
                pass

    # 캐시 저장 (있다면)
    try:
        save_persona_cache(cache)
    except Exception:
        pass

    # 색·아이콘 폴백 + None 제거
    out = []
    for i, c in enumerate(cards):
        if c is None:
            continue
        c["color"] = COLOR_POOL[i % len(COLOR_POOL)]
        if not c.get("icon") or len(c.get("icon", "")) > 4:
            c["icon"] = DEFAULT_ICONS[i % len(DEFAULT_ICONS)]
        out.append(c)
    return out


def debate_call(persona: dict, conversation_so_far: str, my_prompt: str, idea: str, summary: str = "") -> str:
    ctx = ""
    if persona.get("search_basis"):
        ctx += (
            f"\n\n[당신({persona['name']})에 관한 실시간 검색 데이터 — 활용 가능, "
            f"인용은 검색에 명시된 것만 사용]\n{persona['search_basis']}"
        )
    if summary:
        ctx += f"\n\n[주제에 대한 종합 리서치 요약]\n{summary[:1500]}"

    base = f"아이디어: {idea}{ctx}"
    user_content = (
        f"{base}\n\n[지금까지의 토론]\n{conversation_so_far}\n\n[당신의 차례]\n{my_prompt}"
        if conversation_so_far
        else f"{base}\n\n[당신의 차례]\n{my_prompt}"
    )
    return call_groq(
        [
            {"role": "system", "content": persona["system_prompt"]},
            {"role": "user", "content": user_content},
        ],
        temperature=0.85,
        max_tokens=900,
    )


def tag_argument_values(speaker: str, argument: str) -> list:
    prompt = f"""화자: {speaker}
논점: {argument[:700]}

위 비판 논점의 핵심 가치 태그를 1~3개의 짧은 한국어 명사구로 뽑으세요.
예시: '데이터 현실주의', '안전 우선', '실행 속도', '자본 효율', '롱테일 리스크', '규제 적합성', '제품-시장 적합성', '경쟁 차별화', '엔지니어링 깊이', '사용자 경험', '윤리·신뢰'

응답은 ONLY 유효한 JSON 배열. 코드 펜스 금지. 다른 설명 금지:
["태그1", "태그2"]"""
    try:
        resp = call_groq(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        data = _extract_json(resp)
        if isinstance(data, list):
            return [str(t)[:30] for t in data if isinstance(t, (str, int))][:3]
    except Exception:
        pass
    return []


# ── 렌더링 ──────────────────────────────────────────

def _esc(s) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_persona_card(persona: dict, label: str, content: str):
    color = persona.get("color", "#888")
    icon = persona.get("icon", "💬")
    name = persona.get("name", "")
    title = persona.get("title", persona.get("role", ""))
    badge = '<span class="search-tag">🌐 실시간 검색 반영</span><br>' if persona.get("search_basis") else ""
    st.markdown(
        f'<div class="panel-card" style="border-left: 4px solid {color};">'
        f'<div class="panel-name">{icon} {_esc(name)} '
        f'<span style="color:#888;font-size:13px;font-weight:normal;">— {_esc(label)}</span></div>'
        f'<div class="panel-title">{_esc(title)}</div>'
        f"{badge}"
        f'<div class="panel-content">{_esc(content)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_pick_card(persona: dict):
    color = persona.get("color", "#888")
    st.markdown(
        f'<div class="pick-card" style="border-left: 4px solid {color};">'
        f'<div class="pn">{persona.get("icon","💬")} {_esc(persona.get("name",""))}</div>'
        f'<div class="pt">{_esc(persona.get("title",""))}</div>'
        f'<div class="pa">{_esc(persona.get("critique_angle",""))}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


# ── 세션 상태 ──────────────────────────────────────
DEFAULTS = {
    "phase": 0,                    # 0:input, 1:select, 2:debate-running, 3:result+vote
    "user_idea": "",
    "raw_search": "",
    "summary": "",
    "personas": [],                # 추천된 페르소나 카드 리스트
    "selected_indices": [],        # personas 내 선택된 인덱스
    "debate_log": [],              # [(persona_dict, label, content)]
    "votes": [],
    "verdict": "",
    "pipeline_error": "",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v if not isinstance(v, list) else list(v)


def reset_all():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v if not isinstance(v, list) else list(v)


# ── 메인 ────────────────────────────────────────
st.markdown("# 🥊 AI 비평가 토론장")
st.caption("아이디어 → 실시간 리서치 → 비평가 추천 → 선택한 인물들의 토론 → 대표 판결")
st.markdown("")

phase = st.session_state.phase

# === Phase 0: 아이디어 입력 ===
if phase == 0:
    if st.session_state.pipeline_error:
        st.error(st.session_state.pipeline_error)
        st.session_state.pipeline_error = ""

    with st.form("idea_form", clear_on_submit=False):
        idea_input = st.text_area(
            "당신의 아이디어 / 전략 / 질문",
            height=140,
            placeholder="예: 한국 자율주행 검증 SaaS를 일본 OEM 시장에 진출시키려고 합니다. 진출 전략과 기술 스택은...",
        )
        submitted = st.form_submit_button("🔬 리서치 + 비평가 추천")

    if submitted and idea_input.strip():
        idea_clean = idea_input.strip()
        st.session_state.user_idea = idea_clean

        with st.spinner("🌐 외부 데이터 수집 + 요약 중..."):
            raw, summary = research_topic(idea_clean)
            st.session_state.raw_search = raw
            st.session_state.summary = summary

        with st.spinner("🤔 적합한 비평가 후보 추출 중..."):
            candidates = brainstorm_critics(idea_clean, summary)

        if not candidates:
            st.session_state.pipeline_error = "비평가 후보 생성에 실패했습니다. 다시 시도해주세요."
            st.rerun()
        else:
            with st.spinner(f"🧬 {len(candidates)}명의 페르소나 카드 빌드 중 (병렬 검색·합성)..."):
                personas = build_personas(candidates, idea_clean)
            if not personas:
                st.session_state.pipeline_error = "페르소나 합성에 실패했습니다. 다시 시도해주세요."
                st.rerun()
            else:
                st.session_state.personas = personas
                st.session_state.phase = 1
                st.rerun()


# === Phase 1: 요약 + 비평가 선택 ===
elif phase == 1:
    st.markdown("#### 💡 입력한 아이디어")
    st.markdown(
        f'<div class="panel-card">{_esc(st.session_state.user_idea)}</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.summary:
        st.markdown("#### 📚 외부 데이터 수집 요약")
        st.markdown(
            f'<div class="summary-card">{_esc(st.session_state.summary)}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.markdown("#### 🎭 추천 비평가 — 토론에 참여시킬 인물 2~5명을 선택")
    st.caption("AI가 주제에 맞춰 실시간으로 합성한 페르소나입니다. 검색 데이터에 근거한 인물만 카드에 표시됩니다.")

    personas = st.session_state.personas
    cols = st.columns(2)
    for i, p in enumerate(personas):
        with cols[i % 2]:
            render_pick_card(p)
            checked = i in st.session_state.selected_indices
            label = "✅ 선택됨" if checked else "+ 토론 참여"
            if st.button(label, key=f"pick_{i}", type="secondary"):
                if checked:
                    st.session_state.selected_indices.remove(i)
                else:
                    if len(st.session_state.selected_indices) < 5:
                        st.session_state.selected_indices.append(i)
                    else:
                        st.warning("최대 5명까지 선택 가능합니다.")
                st.rerun()

    n = len(st.session_state.selected_indices)
    st.markdown("---")
    st.caption(f"선택된 인원: **{n}명** (2~5명 권장)")

    cc = st.columns([1, 1])
    with cc[0]:
        if st.button("🥊 토론 시작", key="start_debate", type="primary", disabled=(n < 2)):
            st.session_state.phase = 2
            st.session_state.debate_log = []
            st.rerun()
    with cc[1]:
        if st.button("← 다시 입력", key="back_input", type="secondary"):
            reset_all()
            st.rerun()


# === Phase 2: 토론 실행 ===
elif phase == 2:
    selected = [st.session_state.personas[i] for i in st.session_state.selected_indices]
    idea = st.session_state.user_idea
    summary = st.session_state.summary
    n_total = len(selected)

    st.markdown("#### 💡 아이디어")
    st.markdown(f'<div class="panel-card">{_esc(idea)}</div>', unsafe_allow_html=True)

    if not st.session_state.debate_log:
        log = []
        for turn_idx, persona in enumerate(selected):
            if turn_idx == 0:
                label = "선제 비판"
                my_prompt = (
                    "이 아이디어의 가장 잘못된 핵심 전제 하나를 골라 집중 공격하세요. "
                    "왜 그것이 틀렸는지 당신의 알려진 경험·발언·구체적 숫자로 근거를 대고, "
                    "마지막은 상대가 답하기 어려운 날카로운 질문 하나로 끝내세요. "
                    "5~6문장. 추상 일반론 금지. 구체 사실·숫자·사례 최소 1개 포함."
                )
            elif turn_idx == n_total - 1:
                label = "마무리"
                my_prompt = (
                    "마지막 발언자로서 앞선 모든 비판을 종합한 뒤, 그들이 놓친 가장 큰 블라인드스팟을 짚으며 "
                    "토론을 마무리하세요. 앞선 발언자 중 최소 2명을 직접 거명하며 그들 주장의 약점을 지적하세요. "
                    "5~6문장. 추상 일반론 금지. 구체 사실·숫자·사례 최소 1개 포함."
                )
            else:
                label = "반론·보완"
                my_prompt = (
                    "이전 발언자(들)의 비판을 듣고, 당신만의 고유한 관점으로 받아치세요. "
                    "이전 발언자 이름을 한 번 이상 직접 거명하며 그 논점 중 하나를 정확히 짚어 반박/보완하세요. "
                    "이전 발언과 겹치는 논점은 반복하지 말고 새로운 각도/층위를 더하세요. "
                    "마지막은 다음 사람이 답하기 어려운 질문으로 끝내세요. "
                    "5~6문장. 추상 일반론 금지. 구체 사실·숫자·사례 최소 1개 포함."
                )

            st.markdown(f"### Turn {turn_idx + 1} — {persona.get('icon','💬')} {persona['name']}")
            with st.spinner(f"{persona.get('icon','💬')} {persona['name']} 발언 중..."):
                conv = "\n\n".join(f"[{l[0]['name']} — {l[1]}]: {l[2]}" for l in log)
                try:
                    out = debate_call(persona, conv, my_prompt, idea, summary)
                except Exception as e:
                    out = f"오류: {e}"
            log.append((persona, label, out))
            render_persona_card(persona, label, out)

        st.session_state.debate_log = log
        st.session_state.votes = [False] * len(log)
        st.session_state.phase = 3
        st.rerun()


# === Phase 3: 결과 + 투표 + 판결 ===
elif phase == 3:
    log = st.session_state.debate_log
    idea = st.session_state.user_idea
    summary = st.session_state.summary

    st.markdown("#### 💡 입력한 아이디어")
    st.markdown(f'<div class="panel-card">{_esc(idea)}</div>', unsafe_allow_html=True)

    if summary:
        with st.expander("📚 외부 데이터 요약 (참고)"):
            st.markdown(
                f'<div class="summary-card">{_esc(summary)}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("### 💬 토론 결과")
    st.caption("마음에 드는 비판에 👍 → 판결에 가중 + 향후 토론에도 가치관이 누적됩니다.")

    for i, (persona, label, content) in enumerate(log):
        st.markdown(f"### Turn {i + 1}")
        render_persona_card(persona, label, content)
        voted = st.session_state.votes[i] if i < len(st.session_state.votes) else False
        col, _ = st.columns([3, 7])
        with col:
            text = "✅ 선택됨" if voted else "👍 이 논점 선택"
            if st.button(text, key=f"vote_{i}", type="secondary"):
                st.session_state.votes[i] = not voted
                st.rerun()

    st.markdown("---")
    st.markdown("### ⚖️ 최종 판결 — 에이스웍스 코리아 대표")

    if not st.session_state.verdict:
        n_voted = sum(st.session_state.votes)
        if n_voted == 0:
            st.caption("투표 없이도 판결 가능 | 선택하면 가중 반영됩니다.")
        else:
            st.caption(f"선택된 논점 {n_voted}개 — 판결 및 향후 토론에 반영됩니다.")

        if st.button("⚖️ 최종 판결 받기", key="judge_btn", type="primary"):
            with st.spinner("⚖️ 판결 작성 중..."):
                voted_args = [
                    f"[{log[i][0]['name']} — {log[i][1]}]: {log[i][2]}"
                    for i, v in enumerate(st.session_state.votes)
                    if v
                ]
                history = load_vote_history()
                tag_counts = {}
                for v in history[-50:]:
                    for t in v.get("value_tags", []) or []:
                        tag_counts[t] = tag_counts.get(t, 0) + 1
                top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:8]
                tag_summary = (
                    ", ".join(f"{t}({c}회)" for t, c in top_tags)
                    if top_tags
                    else "(아직 누적 데이터 없음)"
                )

                full_log = "\n\n".join(f"[{p['name']} — {l}]: {c}" for p, l, c in log)
                judge_system = (
                    "You must respond ONLY in Korean (한국어). Never use English sentences.\n"
                    "모든 응답은 반드시 한국어로만 작성하세요.\n"
                    "마크다운 표기(**, ##, ---, * 목록 등)는 절대 사용하지 마세요. "
                    "평문만으로 작성하고, 단락 구분은 줄바꿈으로 표시하세요.\n\n"
                    "당신은 에이스웍스 코리아의 대표입니다.\n\n"
                    f"{COMPANY_BACKGROUND}\n"
                    "위 회사 배경은 당신의 판단 기준입니다. 아이디어가 우리 사업 영역(EV/자율주행 HILS, "
                    "검증 장비, 자율주행 토탈 솔루션, 글로벌 OEM B2B)과 맞닿는 부분을 우선 짚고, "
                    "우리 팀의 실제 제품·고객·거점·강점에 비추어 실행 가능성을 평가하세요. "
                    "회사 사업과 무관한 아이디어면 그 점도 솔직히 지적하세요.\n\n"
                    "당신의 성격과 배경:\n"
                    "- 자율주행 및 AI 소프트웨어 개발 현장을 직접 뛰어온 실무형 리더다.\n"
                    "- 비평가들의 이론을 존중하지만 한국 시장과 실제 납품 현실이 다르다는 걸 안다.\n"
                    "- 화려한 비전이나 거시적 두려움보다 \"우리 팀이 내일부터 실행할 수 있는가\"를 먼저 본다.\n"
                    "- 좋은 말도 나쁜 말도 솔직하게 한다. 애매하게 넘어가지 않는다.\n\n"
                    "판결 방식:\n"
                    "- 비평가 중 누가 가장 핵심을 찔렀는지 짚는다.\n"
                    "- 사업적으로 지금 당장 실행 가능한지 판단한다 (우리 제품군·고객·거점 기준).\n"
                    "- 최종 결론은 반드시 \"채택 / 수정 후 채택 / 기각\" 중 하나로 명확하게 내린다.\n"
                    "- 팀이 가중 표시한 논점, 누적 가치관 태그를 판결 기조에 반영한다.\n"
                    "- 결론 뒤에 우리 개발/영업 팀에게 짧고 강력한 지시를 한 마디 덧붙인다."
                )
                voted_section = ""
                if voted_args:
                    voted_section += (
                        "\n\n[이번 토론에서 팀이 가중 선택한 논점]\n" + "\n\n".join(voted_args)
                    )
                voted_section += (
                    f"\n\n[누적 가치관 태그 — 이 팀이 반복적으로 중요시한 가치]\n{tag_summary}"
                )

                judge_prompt = (
                    f"아이디어: {idea}\n\n"
                    f"전체 토론 ({len(log)}명 참여):\n{full_log}"
                    f"{voted_section}\n\n"
                    "위 토론을 바탕으로 에이스웍스 코리아 대표로서 최종 판결을 내려주세요. "
                    "팀이 선택한 논점은 특별히 무겁게 다루고, 누적 가치관도 판결 기조에 반영하세요.\n\n"
                    "[판결문 구조 — 평문, 줄바꿈으로 단락 구분, 마크다운 금지]\n"
                    "① 토론 핵심 쟁점 요약 (2~3줄)\n"
                    "② 비평가 중 가장 타당했던 논점 (혹은 복합 판단)\n"
                    "③ 사업적 관점 최종 판단 (실행 가능성 중심)\n"
                    "④ 결론: 채택 / 수정 후 채택 / 기각 — 이유 한 문장\n"
                    "⑤ 우리 팀에게 한 마디 (지시사항)"
                )
                try:
                    verdict = call_groq(
                        [
                            {"role": "system", "content": judge_system},
                            {"role": "user", "content": judge_prompt},
                        ],
                        temperature=0.6,
                        max_tokens=1400,
                    )
                except Exception as e:
                    verdict = f"오류: {e}"

                # 가치 태깅 → 누적 학습
                new_votes = []
                for i, v in enumerate(st.session_state.votes):
                    if not v:
                        continue
                    speaker = log[i][0]["name"]
                    argument = log[i][2]
                    try:
                        tags = tag_argument_values(speaker, argument)
                    except Exception:
                        tags = []
                    new_votes.append(
                        {
                            "speaker": speaker,
                            "label": log[i][1],
                            "argument": argument,
                            "value_tags": tags,
                            "topic": idea[:200],
                            "ts": int(time.time()),
                        }
                    )
                if new_votes:
                    save_vote_history(new_votes)

                st.session_state.verdict = verdict
                st.rerun()
    else:
        if sum(st.session_state.votes) > 0:
            st.info(
                f"선택된 논점 {sum(st.session_state.votes)}개가 판결 및 향후 토론에 반영되었습니다."
            )
        st.markdown(
            f'<div class="panel-card" style="border-left: 4px solid #FFD60A; background: #1e1a00;">'
            f'<div class="panel-name">⚖️ 에이스웍스 코리아 대표</div>'
            f'<div class="panel-title">최종 판결</div>'
            f'<div class="panel-content">{_esc(st.session_state.verdict)}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        if st.button("🔄 다른 아이디어로 다시", key="reset_btn", type="primary"):
            reset_all()
            st.rerun()
