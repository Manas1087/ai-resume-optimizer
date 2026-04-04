import streamlit as st
import fitz  # PyMuPDF
from google import genai
import re
import markdown as md_lib

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="AI Resume Optimizer",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  THEME — driven by ?theme= query param
# ─────────────────────────────────────────────

params = st.query_params
theme = params.get("theme", "dark")
if theme not in ("dark", "light"):
    theme = "dark"
is_dark = theme == "dark"

DARK = {
    "bg":              "#080c14",
    "surface":         "rgba(255,255,255,0.04)",
    "border":          "rgba(255,255,255,0.08)",
    "border_accent":   "rgba(79,142,247,0.40)",
    "text_primary":    "#eef2fc",
    "text_secondary":  "#c9d4e8",
    "text_muted":      "#7a8db3",
    "text_faint":      "#2e3d5a",
    "analysis_bg":     "rgba(10,15,28,0.70)",
    "preview_bg":      "rgba(10,15,28,0.60)",
    "preview_text":    "#c0cfe8",
    "footer_border":   "rgba(255,255,255,0.05)",
    "textarea_bg":     "rgba(255,255,255,0.03)",
    "textarea_border": "rgba(255,255,255,0.1)",
    "textarea_text":   "#c9d4e8",
    "upload_bg":       "rgba(255,255,255,0.02)",
    "upload_border":   "rgba(79,142,247,0.35)",
    "scroll_thumb":    "rgba(79,142,247,0.30)",
    "progress_track":  "rgba(255,255,255,0.07)",
    "pill_bg":         "rgba(255,255,255,0.07)",
    "pill_border":     "rgba(255,255,255,0.15)",
    "pill_color":      "#a0b0cc",
    "pill_hover":      "rgba(255,255,255,0.12)",
    "next_theme":      "light",
    "icon":            "☀️",
    "next_label":      "Light mode",
}

LIGHT = {
    "bg":              "#f0f4fa",
    "surface":         "rgba(255,255,255,0.80)",
    "border":          "rgba(0,0,0,0.08)",
    "border_accent":   "rgba(37,99,235,0.30)",
    "text_primary":    "#0f172a",
    "text_secondary":  "#1e293b",
    "text_muted":      "#64748b",
    "text_faint":      "#94a3b8",
    "analysis_bg":     "rgba(255,255,255,0.90)",
    "preview_bg":      "rgba(255,255,255,0.95)",
    "preview_text":    "#1e293b",
    "footer_border":   "rgba(0,0,0,0.07)",
    "textarea_bg":     "rgba(255,255,255,0.90)",
    "textarea_border": "rgba(0,0,0,0.10)",
    "textarea_text":   "#1e293b",
    "upload_bg":       "rgba(255,255,255,0.70)",
    "upload_border":   "rgba(37,99,235,0.25)",
    "scroll_thumb":    "rgba(37,99,235,0.20)",
    "progress_track":  "rgba(0,0,0,0.07)",
    "pill_bg":         "rgba(0,0,0,0.05)",
    "pill_border":     "rgba(0,0,0,0.13)",
    "pill_color":      "#475569",
    "pill_hover":      "rgba(0,0,0,0.10)",
    "next_theme":      "dark",
    "icon":            "🌙",
    "next_label":      "Dark mode",
}

T = DARK if is_dark else LIGHT

# ─────────────────────────────────────────────
#  STYLES
# ─────────────────────────────────────────────

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Inter:wght@300;400;500;600&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; }}

html, body, [data-testid="stAppViewContainer"] {{
    background: {T["bg"]} !important;
    font-family: 'Inter', sans-serif;
    color: {T["text_secondary"]};
}}
[data-testid="stHeader"]  {{ background: transparent !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}

.block-container {{
    max-width: 900px !important;
    padding: 2rem 2rem 5rem !important;
    margin: 0 auto !important;
}}

/* Force Streamlit's element containers to not interfere with centering */
[data-testid="stMarkdownContainer"] {{
    width: 100% !important;
}}
[data-testid="stMarkdownContainer"] > div {{
    width: 100% !important;
    text-align: center !important;
}}

/* ── PRIMARY BUTTONS ── */
.stButton > button {{
    width: 100%;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.72rem 1.5rem !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    transition: opacity 0.2s, transform 0.15s !important;
    box-shadow: 0 4px 18px rgba(37,99,235,0.28) !important;
    cursor: pointer !important;
}}
.stButton > button:hover {{
    opacity: 0.87 !important;
    transform: translateY(-1px) !important;
}}

/* ── THEME PILL ── */
.theme-pill-wrap {{
    display: flex;
    justify-content: flex-end;
    margin-bottom: 0.5rem;
}}
a.theme-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: {T["pill_bg"]};
    color: {T["pill_color"]} !important;
    border: 1px solid {T["pill_border"]};
    border-radius: 100px;
    padding: 0.38rem 1.1rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    text-decoration: none !important;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s;
    white-space: nowrap;
}}
a.theme-pill:hover {{
    background: {T["pill_hover"]};
    border-color: rgba(79,142,247,0.45);
    text-decoration: none !important;
}}

/* ── HERO — force true center ── */
.hero-wrap {{
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 2.6rem 0 2rem;
}}
.hero-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #4f8ef7;
    border: 1px solid rgba(79,142,247,0.30);
    border-radius: 100px;
    padding: 0.32rem 1rem;
    margin-bottom: 1.4rem;
}}
.hero-title {{
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.4rem, 5vw, 3.8rem);
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -0.025em;
    color: {T["text_primary"]};
    margin-bottom: 1rem;
    text-align: center;
    width: 100%;
}}
.hero-title .grad {{
    background: linear-gradient(130deg, #3b82f6 0%, #8b5cf6 55%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.hero-sub {{
    font-size: 1rem;
    color: {T["text_muted"]};
    width: 100%;
    max-width: 500px;
    line-height: 1.7;
    font-weight: 400;
    text-align: center;
    margin: 0 auto;
}}

/* ── DIVIDERS & LABELS ── */
.divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(79,142,247,0.20), transparent);
    margin: 2.2rem 0;
    width: 100%;
}}
.section-label {{
    font-family: 'Syne', sans-serif;
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #4f8ef7;
    margin-bottom: 0.7rem;
    display: block;
    text-align: left;
}}

/* ── METRIC TILES ── */
.metrics-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.9rem;
    margin: 1.4rem 0 1.8rem;
}}
.metric-tile {{
    background: {T["surface"]};
    border: 1px solid {T["border"]};
    border-radius: 16px;
    padding: 1.4rem 1.2rem;
    text-align: center;
    transition: border-color 0.2s, transform 0.2s;
}}
.metric-tile:hover {{
    border-color: {T["border_accent"]};
    transform: translateY(-2px);
}}
.metric-value {{
    font-family: 'Syne', sans-serif;
    font-size: 2.1rem;
    font-weight: 800;
    color: {T["text_primary"]};
    line-height: 1;
    margin-bottom: 0.45rem;
}}
.metric-label {{
    font-size: 0.75rem;
    color: {T["text_muted"]};
    font-weight: 500;
    letter-spacing: 0.03em;
}}

/* ── PROGRESS BAR ── */
.progress-wrap {{ margin: 0 0 1.6rem; }}
.progress-track {{
    height: 5px;
    background: {T["progress_track"]};
    border-radius: 99px;
    overflow: hidden;
}}
.progress-fill {{
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
}}
.progress-legend {{
    display: flex;
    justify-content: space-between;
    font-size: 0.7rem;
    color: {T["text_faint"]};
    margin-top: 0.4rem;
}}

/* ── SKILL CHIPS ── */
.chips-section {{ margin-bottom: 1.1rem; }}
.chips-title {{
    font-size: 0.66rem;
    font-weight: 600;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    display: block;
}}
.chips-wrap {{ display: flex; flex-wrap: wrap; gap: 0.4rem; }}
.chip {{
    display: inline-block;
    border-radius: 100px;
    padding: 0.25rem 0.8rem;
    font-size: 0.76rem;
    font-weight: 500;
}}
.chip-match {{
    background: rgba(52,211,153,0.10);
    color: #34d399;
    border: 1px solid rgba(52,211,153,0.25);
}}
.chip-miss {{
    background: rgba(248,113,113,0.09);
    color: #f87171;
    border: 1px solid rgba(248,113,113,0.25);
}}

/* ── SUGGESTIONS ── */
.suggestions-box {{
    background: {T["analysis_bg"]};
    border: 1px solid {T["border"]};
    border-left: 3px solid #4f8ef7;
    border-radius: 12px;
    padding: 1.3rem 1.6rem;
    font-size: 0.93rem;
    line-height: 1.8;
    color: {T["text_secondary"]};
    margin-bottom: 0.5rem;
}}
.suggestions-box p {{ margin: 0; }}
.sugg-header {{
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: #4f8ef7;
    margin-bottom: 0.65rem;
    display: block;
}}

/* ── PREVIEW BOX ── */
.preview-box {{
    background: {T["preview_bg"]};
    border: 1px solid {T["border_accent"]};
    border-radius: 14px;
    padding: 1.8rem;
    white-space: pre-wrap;
    font-family: 'Inter', monospace;
    font-size: 0.86rem;
    color: {T["preview_text"]};
    max-height: 500px;
    overflow-y: auto;
    line-height: 1.8;
}}

/* ── WIDGETS ── */
[data-testid="stFileUploader"] {{
    background: {T["upload_bg"]} !important;
    border: 1.5px dashed {T["upload_border"]} !important;
    border-radius: 14px !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: rgba(79,142,247,0.6) !important;
}}
textarea {{
    background: {T["textarea_bg"]} !important;
    border: 1px solid {T["textarea_border"]} !important;
    border-radius: 12px !important;
    color: {T["textarea_text"]} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
}}
textarea:focus {{
    border-color: rgba(79,142,247,0.55) !important;
    box-shadow: 0 0 0 3px rgba(79,142,247,0.08) !important;
    outline: none !important;
}}
label {{ color: {T["text_muted"]} !important; }}

/* ── HINT + FOOTER ── */
.hint-text {{
    text-align: center;
    color: {T["text_faint"]};
    font-size: 0.82rem;
    padding: 0.4rem 0;
}}
.footer {{
    text-align: center;
    margin-top: 4rem;
    padding-top: 1.8rem;
    border-top: 1px solid {T["footer_border"]};
    color: {T["text_faint"]};
    font-size: 0.73rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}

::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {T["scroll_thumb"]}; border-radius: 99px; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  GEMINI CLIENT
# ─────────────────────────────────────────────

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
MODEL = "gemini-2.5-flash"

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def extract_text_from_pdf(uploaded_file) -> str:
    text = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def analyze_resume(jd: str, resume: str) -> str:
    prompt = f"""
You are an expert ATS resume analyst. Return ONLY this format, nothing else:

**Match Score:** <number>%
**Matching Skills:** <comma separated list>
**Missing Skills:** <comma separated list>
**Suggestions:** <concise, actionable paragraph>

Job Description:
{jd}

Resume:
{resume}
"""
    return client.models.generate_content(model=MODEL, contents=prompt).text

def optimize_resume(jd: str, resume: str) -> str:
    prompt = f"""
Rewrite the resume to be ATS-optimized for the given job description.
- Keep the same structure and sections
- Use bullet points for experience and skills
- Integrate relevant keywords naturally
- Use strong action verbs
- Return only the formatted resume text, nothing else

Job Description:
{jd}

Resume:
{resume}
"""
    return client.models.generate_content(model=MODEL, contents=prompt).text

def extract_score(text: str) -> int:
    m = re.search(r"(\d+)%", text)
    return int(m.group(1)) if m else 0

def extract_field(text: str, field: str) -> str:
    m = re.search(rf"\*\*{field}:\*\*\s*(.+?)(?=\n\*\*|\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""

def score_color(score: int) -> str:
    return "#34d399" if score >= 75 else "#fbbf24" if score >= 50 else "#f87171"

def score_label(score: int) -> str:
    return "Strong Match" if score >= 75 else "Moderate Match" if score >= 50 else "Needs Work"

def render_chips(csv: str, cls: str) -> str:
    items = [s.strip() for s in csv.split(",") if s.strip()]
    return '<div class="chips-wrap">' + "".join(
        f'<span class="chip {cls}">{item}</span>' for item in items
    ) + "</div>"

# ─────────────────────────────────────────────
#  THEME TOGGLE
#  target="_self" keeps it in the same tab.
#  The ?theme= param is read on every rerun.
# ─────────────────────────────────────────────

st.markdown(f"""
<div class="theme-pill-wrap">
    <a class="theme-pill" href="?theme={T['next_theme']}" target="_self">
        {T['icon']} &nbsp;{T['next_label']}
    </a>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  HERO
# ─────────────────────────────────────────────

st.markdown(f"""
<div class="hero-wrap">
    <div class="hero-badge">✦ &nbsp;Powered by Gemini 2.5 Flash</div>
    <h1 class="hero-title">
        AI <span class="grad">Resume</span> Optimizer
    </h1>
    <p class="hero-sub">
        Upload your resume, paste a job description, and let AI
        pinpoint gaps, score your fit, and rewrite for ATS success.
    </p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  INPUTS
# ─────────────────────────────────────────────

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<span class="section-label">01 — Upload Resume</span>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "upload", type=["pdf"], label_visibility="collapsed"
    )

with col_right:
    st.markdown('<span class="section-label">02 — Job Description</span>', unsafe_allow_html=True)
    jd = st.text_area(
        "jd",
        placeholder="Paste the full job description here…",
        height=185,
        label_visibility="collapsed",
    )

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ANALYZE
# ─────────────────────────────────────────────

if uploaded_file and jd:
    if st.button("✦  Analyze My Resume"):
        resume_text = extract_text_from_pdf(uploaded_file)
        with st.spinner("Analyzing your resume…"):
            analysis = analyze_resume(jd, resume_text)
        st.session_state["analysis"]    = analysis
        st.session_state["resume_text"] = resume_text
        st.session_state.pop("optimized", None)
elif not uploaded_file:
    st.markdown('<p class="hint-text">⬆ Upload a PDF resume to get started</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────

if "analysis" in st.session_state:
    analysis    = st.session_state["analysis"]
    resume_text = st.session_state["resume_text"]

    score    = extract_score(analysis)
    matching = extract_field(analysis, "Matching Skills")
    missing  = extract_field(analysis, "Missing Skills")
    suggest  = extract_field(analysis, "Suggestions")
    clr      = score_color(score)
    lbl      = score_label(score)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<span class="section-label">03 — Analysis Results</span>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metrics-row">
        <div class="metric-tile">
            <div class="metric-value" style="color:{clr}">{score}%</div>
            <div class="metric-label">ATS Match Score</div>
        </div>
        <div class="metric-tile">
            <div class="metric-value" style="font-size:1.3rem;padding-top:0.25rem">{lbl}</div>
            <div class="metric-label">Overall Assessment</div>
        </div>
        <div class="metric-tile">
            <div class="metric-value" style="color:#a78bfa;font-size:1.8rem">
                {'✓' if score >= 75 else '✗'}
            </div>
            <div class="metric-label">
                {'Ready to Apply' if score >= 75 else 'Needs Improvement'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="progress-wrap">
        <div class="progress-track">
            <div class="progress-fill" style="width:{score}%"></div>
        </div>
        <div class="progress-legend"><span>0%</span><span>50%</span><span>100%</span></div>
    </div>
    """, unsafe_allow_html=True)

    if matching:
        st.markdown(f"""
        <div class="chips-section">
            <span class="chips-title" style="color:#34d399">✓ &nbsp;Matching Skills</span>
            {render_chips(matching, "chip-match")}
        </div>
        """, unsafe_allow_html=True)

    if missing:
        st.markdown(f"""
        <div class="chips-section">
            <span class="chips-title" style="color:#f87171">✗ &nbsp;Missing Skills</span>
            {render_chips(missing, "chip-miss")}
        </div>
        """, unsafe_allow_html=True)

    if suggest:
        st.markdown(f"""
        <div class="suggestions-box">
            <span class="sugg-header">💡 &nbsp;Suggestions</span>
            {md_lib.markdown(suggest)}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<span class="section-label">04 — Optimized Resume</span>', unsafe_allow_html=True)

    if st.button("✦  Generate Optimized Resume"):
        with st.spinner("Rewriting for ATS…"):
            optimized = optimize_resume(jd, resume_text)
        st.session_state["optimized"] = optimized

    if "optimized" in st.session_state:
        st.markdown(
            f'<div class="preview-box">{st.session_state["optimized"]}</div>',
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────

st.markdown("""
<div class="footer">AI Resume Optimizer &nbsp;·&nbsp; Gemini 2.5 Flash</div>
""", unsafe_allow_html=True)
