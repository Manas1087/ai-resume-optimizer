import streamlit as st
import fitz  # PyMuPDF
from google import genai
import re
import markdown as md_lib  # pip install markdown

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
#  THEME STATE  (default → dark)
# ─────────────────────────────────────────────

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

is_dark = st.session_state["theme"] == "dark"

# ─────────────────────────────────────────────
#  CSS VARIABLE TOKENS  (dark / light)
# ─────────────────────────────────────────────

DARK = {
    "bg":              "#080c14",
    "surface":         "rgba(255,255,255,0.04)",
    "surface_hover":   "rgba(255,255,255,0.07)",
    "border":          "rgba(255,255,255,0.07)",
    "border_accent":   "rgba(79,142,247,0.40)",
    "text_primary":    "#eef2fc",
    "text_secondary":  "#c9d4e8",
    "text_muted":      "#7a8db3",
    "text_faint":      "#3a4a6a",
    "analysis_bg":     "rgba(10,15,28,0.70)",
    "preview_bg":      "rgba(10,15,28,0.60)",
    "preview_text":    "#c0cfe8",
    "footer_border":   "rgba(255,255,255,0.05)",
    "textarea_bg":     "rgba(255,255,255,0.025)",
    "textarea_border": "rgba(255,255,255,0.08)",
    "textarea_text":   "#c9d4e8",
    "upload_bg":       "rgba(255,255,255,0.025)",
    "upload_border":   "rgba(79,142,247,0.35)",
    "scroll_thumb":    "rgba(79,142,247,0.30)",
    "progress_track":  "rgba(255,255,255,0.07)",
    "icon":            "☀️",
    "label":           "Light Mode",
}

LIGHT = {
    "bg":              "#f4f6fb",
    "surface":         "rgba(0,0,0,0.03)",
    "surface_hover":   "rgba(0,0,0,0.06)",
    "border":          "rgba(0,0,0,0.08)",
    "border_accent":   "rgba(37,99,235,0.35)",
    "text_primary":    "#0f172a",
    "text_secondary":  "#1e293b",
    "text_muted":      "#475569",
    "text_faint":      "#94a3b8",
    "analysis_bg":     "rgba(255,255,255,0.85)",
    "preview_bg":      "rgba(255,255,255,0.90)",
    "preview_text":    "#1e293b",
    "footer_border":   "rgba(0,0,0,0.07)",
    "textarea_bg":     "rgba(255,255,255,0.80)",
    "textarea_border": "rgba(0,0,0,0.10)",
    "textarea_text":   "#1e293b",
    "upload_bg":       "rgba(255,255,255,0.70)",
    "upload_border":   "rgba(37,99,235,0.30)",
    "scroll_thumb":    "rgba(37,99,235,0.25)",
    "progress_track":  "rgba(0,0,0,0.08)",
    "icon":            "🌙",
    "label":           "Dark Mode",
}

T = DARK if is_dark else LIGHT

# ─────────────────────────────────────────────
#  INJECT STYLES
# ─────────────────────────────────────────────

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [data-testid="stAppViewContainer"] {{
    background: {T["bg"]} !important;
    font-family: 'DM Sans', sans-serif;
    color: {T["text_secondary"]};
    transition: background 0.35s ease, color 0.35s ease;
}}

[data-testid="stHeader"] {{ background: transparent !important; }}

.block-container {{
    max-width: 960px !important;
    padding: 2rem 2rem 4rem !important;
    margin: 0 auto;
}}

/* ── Hero ── */
.hero-wrap {{
    text-align: center;
    padding: 2rem 0 2rem;
}}
.hero-badge {{
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #4f8ef7;
    border: 1px solid rgba(79,142,247,0.35);
    border-radius: 100px;
    padding: 0.35rem 1.1rem;
    margin-bottom: 1.4rem;
}}
.hero-title {{
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.4rem, 5vw, 3.8rem);
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.02em;
    color: {T["text_primary"]};
    margin-bottom: 1rem;
}}
.hero-title span {{
    background: linear-gradient(135deg, #4f8ef7 0%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.hero-sub {{
    font-size: 1.05rem;
    color: {T["text_muted"]};
    max-width: 520px;
    margin: 0 auto;
    line-height: 1.65;
}}

/* ── Divider ── */
.divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(79,142,247,0.25), transparent);
    margin: 2.5rem 0;
}}

/* ── Section labels ── */
.section-label {{
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #4f8ef7;
    margin-bottom: 0.6rem;
}}

/* ── Metric tiles ── */
.metrics-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin: 1.6rem 0;
}}
.metric-tile {{
    background: {T["surface"]};
    border: 1px solid {T["border"]};
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    text-align: center;
    transition: border-color 0.2s;
}}
.metric-tile:hover {{ border-color: {T["border_accent"]}; }}
.metric-value {{
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    color: {T["text_primary"]};
    line-height: 1;
}}
.metric-label {{
    font-size: 0.78rem;
    color: {T["text_muted"]};
    margin-top: 0.4rem;
    letter-spacing: 0.04em;
}}

/* ── Skills chips ── */
.chips-section {{ margin: 0.5rem 0 1.2rem; }}
.chips-title {{
    font-family: 'Syne', sans-serif;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.55rem;
}}
.chips-wrap {{ display: flex; flex-wrap: wrap; gap: 0.45rem; }}
.chip {{
    display: inline-block;
    border-radius: 100px;
    padding: 0.28rem 0.85rem;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.01em;
}}
.chip-match {{
    background: rgba(52,211,153,0.12);
    color: #34d399;
    border: 1px solid rgba(52,211,153,0.3);
}}
.chip-miss {{
    background: rgba(248,113,113,0.10);
    color: #f87171;
    border: 1px solid rgba(248,113,113,0.28);
}}

/* ── Suggestions box ── */
.suggestions-box {{
    background: {T["analysis_bg"]};
    border: 1px solid {T["border"]};
    border-left: 3px solid #4f8ef7;
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    font-size: 0.95rem;
    line-height: 1.8;
    color: {T["text_secondary"]};
    margin-top: 1rem;
}}
.suggestions-box strong {{ color: {T["text_primary"]}; }}

/* ── Progress bar ── */
.progress-wrap {{ margin: 1.4rem 0; }}
.progress-track {{
    height: 6px;
    background: {T["progress_track"]};
    border-radius: 99px;
    overflow: hidden;
}}
.progress-fill {{
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #4f8ef7, #a78bfa);
    transition: width 0.8s cubic-bezier(.4,0,.2,1);
}}
.progress-legend {{
    display: flex;
    justify-content: space-between;
    font-size: 0.73rem;
    color: {T["text_faint"]};
    margin-top: 0.45rem;
}}

/* ── Optimized preview ── */
.preview-box {{
    background: {T["preview_bg"]};
    border: 1px solid {T["border_accent"]};
    border-radius: 12px;
    padding: 1.8rem;
    white-space: pre-wrap;
    font-family: 'DM Sans', monospace;
    font-size: 0.88rem;
    color: {T["preview_text"]};
    max-height: 480px;
    overflow-y: auto;
    line-height: 1.75;
}}

/* ── Widget overrides ── */
[data-testid="stFileUploader"] {{
    background: {T["upload_bg"]} !important;
    border: 1.5px dashed {T["upload_border"]} !important;
    border-radius: 14px !important;
    padding: 1.2rem !important;
    transition: border-color 0.2s;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: rgba(79,142,247,0.65) !important;
}}

textarea {{
    background: {T["textarea_bg"]} !important;
    border: 1px solid {T["textarea_border"]} !important;
    border-radius: 12px !important;
    color: {T["textarea_text"]} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.93rem !important;
    padding: 1rem !important;
}}
textarea:focus {{
    border-color: rgba(79,142,247,0.5) !important;
    box-shadow: 0 0 0 3px rgba(79,142,247,0.1) !important;
}}

.stButton > button {{
    width: 100%;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 1.5rem !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em !important;
    cursor: pointer !important;
    transition: opacity 0.2s, transform 0.15s !important;
    box-shadow: 0 4px 20px rgba(37,99,235,0.3) !important;
}}
.stButton > button:hover {{
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}}
.stButton > button:active {{ transform: translateY(0) !important; }}

/* hint */
.hint-text {{
    text-align: center;
    color: {T["text_faint"]};
    font-size: 0.85rem;
    margin-top: 0.5rem;
}}

/* footer */
.footer {{
    text-align: center;
    margin-top: 4rem;
    padding-top: 2rem;
    border-top: 1px solid {T["footer_border"]};
    color: {T["text_faint"]};
    font-size: 0.78rem;
    letter-spacing: 0.06em;
}}

/* scrollbar */
::-webkit-scrollbar {{ width: 6px; }}
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

def safe_rerun():
    """Compatibility shim: st.rerun() was added in Streamlit 1.27."""
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()


def extract_text_from_pdf(uploaded_file) -> str:
    text = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text


def analyze_resume(jd: str, resume: str) -> str:
    prompt = f"""
You are an expert ATS resume analyst. Return your response in EXACTLY this format and nothing else:

**Match Score:** <number>%
**Matching Skills:** <comma separated list>
**Missing Skills:** <comma separated list>
**Suggestions:** <concise, actionable paragraph>

Job Description:
{jd}

Resume:
{resume}
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text


def optimize_resume(jd: str, resume: str) -> str:
    prompt = f"""
Rewrite the resume to be ATS-optimized for the given job description.

Guidelines:
- Keep the same overall structure and sections
- Use clear bullet points for experience and skills
- Integrate relevant keywords from the job description naturally
- Be concise and impactful (strong action verbs)
- Return only the formatted resume text, nothing else

Job Description:
{jd}

Resume:
{resume}
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text


def extract_score(text: str) -> int:
    match = re.search(r"(\d+)%", text)
    return int(match.group(1)) if match else 0


def extract_field(text: str, field: str) -> str:
    """Pull a single **Field:** value from the analysis markdown."""
    pattern = rf"\*\*{field}:\*\*\s*(.+?)(?=\n\*\*|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def score_color(score: int) -> str:
    if score >= 75:
        return "#34d399"
    elif score >= 50:
        return "#fbbf24"
    return "#f87171"


def score_label(score: int) -> str:
    if score >= 75:
        return "Strong Match"
    elif score >= 50:
        return "Moderate Match"
    return "Needs Work"


def render_chips(csv: str, chip_class: str) -> str:
    items = [s.strip() for s in csv.split(",") if s.strip()]
    chips = "".join(f'<span class="chip {chip_class}">{item}</span>' for item in items)
    return f'<div class="chips-wrap">{chips}</div>'


# ─────────────────────────────────────────────
#  THEME TOGGLE  (top-right)
# ─────────────────────────────────────────────

_, toggle_col = st.columns([8, 2])
with toggle_col:
    if st.button(f"{T['icon']}  {T['label']}", key="theme_toggle"):
        st.session_state["theme"] = "light" if is_dark else "dark"
        safe_rerun()   # ✅ Fixed: works on both old and new Streamlit versions

# ─────────────────────────────────────────────
#  HERO
# ─────────────────────────────────────────────

st.markdown("""
<div class="hero-wrap">
    <div class="hero-badge">✦ Powered by Gemini 2.5 Flash</div>
    <h1 class="hero-title">AI <span>Resume</span> Optimizer</h1>
    <p class="hero-sub">
        Upload your resume, paste a job description, and let AI pinpoint gaps,
        score your fit, and rewrite your resume for ATS success.
    </p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  INPUTS
# ─────────────────────────────────────────────

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<p class="section-label">01 — Upload Resume</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drop your PDF here",
        type=["pdf"],
        label_visibility="collapsed",
    )

with col_right:
    st.markdown('<p class="section-label">02 — Job Description</p>', unsafe_allow_html=True)
    jd = st.text_area(
        "Paste the full job description",
        placeholder="Paste the full job description here…",
        height=180,
        label_visibility="collapsed",
    )

st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ANALYZE BUTTON
# ─────────────────────────────────────────────

if uploaded_file and jd:
    if st.button("✦  Analyze My Resume"):
        resume_text = extract_text_from_pdf(uploaded_file)
        with st.spinner("Running analysis…"):
            analysis = analyze_resume(jd, resume_text)
        st.session_state["analysis"] = analysis
        st.session_state["resume_text"] = resume_text
        st.session_state.pop("optimized", None)

elif not uploaded_file:
    st.markdown('<p class="hint-text">⬆ Upload a PDF resume to get started</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  DISPLAY ANALYSIS
# ─────────────────────────────────────────────

if "analysis" in st.session_state:
    analysis    = st.session_state["analysis"]
    resume_text = st.session_state["resume_text"]

    # Parse each field individually
    score            = extract_score(analysis)
    matching_skills  = extract_field(analysis, "Matching Skills")
    missing_skills   = extract_field(analysis, "Missing Skills")
    suggestions_text = extract_field(analysis, "Suggestions")
    clr              = score_color(score)
    lbl              = score_label(score)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<p class="section-label">03 — Analysis Results</p>', unsafe_allow_html=True)

    # ── Score tiles ──
    st.markdown(f"""
    <div class="metrics-row">
        <div class="metric-tile">
            <div class="metric-value" style="color:{clr}">{score}%</div>
            <div class="metric-label">ATS Match Score</div>
        </div>
        <div class="metric-tile">
            <div class="metric-value" style="font-size:1.35rem">{lbl}</div>
            <div class="metric-label">Overall Assessment</div>
        </div>
        <div class="metric-tile">
            <div class="metric-value" style="color:#a78bfa">{'✓' if score >= 75 else '!'}</div>
            <div class="metric-label">{'Ready to Apply' if score >= 75 else 'Optimization Recommended'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Progress bar ──
    st.markdown(f"""
    <div class="progress-wrap">
        <div class="progress-track">
            <div class="progress-fill" style="width:{score}%"></div>
        </div>
        <div class="progress-legend"><span>0%</span><span>50%</span><span>100%</span></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Matching skills chips ──
    if matching_skills:
        st.markdown(f"""
        <div class="chips-section">
            <div class="chips-title" style="color:#34d399">✓ Matching Skills</div>
            {render_chips(matching_skills, "chip-match")}
        </div>
        """, unsafe_allow_html=True)

    # ── Missing skills chips ──
    if missing_skills:
        st.markdown(f"""
        <div class="chips-section">
            <div class="chips-title" style="color:#f87171">✗ Missing Skills</div>
            {render_chips(missing_skills, "chip-miss")}
        </div>
        """, unsafe_allow_html=True)

    # ── Suggestions only (no duplicate score/skills) ──
    if suggestions_text:
        suggestions_html = md_lib.markdown(suggestions_text)
        st.markdown(f"""
        <div class="suggestions-box">
            <div style="font-family:'Syne',sans-serif;font-size:0.68rem;font-weight:700;
                        letter-spacing:0.12em;text-transform:uppercase;color:#4f8ef7;
                        margin-bottom:0.7rem">💡 Suggestions</div>
            {suggestions_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    #  OPTIMIZE BUTTON
    # ─────────────────────────────────────────────

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<p class="section-label">04 — Optimized Resume</p>', unsafe_allow_html=True)

    if st.button("✦  Generate Optimized Resume"):
        with st.spinner("Rewriting for ATS…"):
            optimized = optimize_resume(jd, resume_text)
        st.session_state["optimized"] = optimized

    if "optimized" in st.session_state:
        optimized = st.session_state["optimized"]
        st.markdown(f'<div class="preview-box">{optimized}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────

st.markdown("""
<div class="footer">
    AI RESUME OPTIMIZER &nbsp;·&nbsp; GEMINI 2.5 FLASH
</div>
""", unsafe_allow_html=True)