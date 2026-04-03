import streamlit as st
import fitz  # PyMuPDF
from google import genai
from docx import Document
from docx.shared import Pt
from docx2pdf import convert
import re

# ===============================
# 🎨 CUSTOM UI (SaaS STYLE)
# ===============================
st.markdown("""
<style>
.main {
    background-color: #0f172a;
}
h1, h2, h3 {
    color: #e2e8f0;
}
.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}
.stButton>button:hover {
    background-color: #1d4ed8;
}
.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 🔑 GEMINI CLIENT
# ===============================
client = genai.Client(api_key="AIzaSyBBbSYW53z72L7KdMdTxc0fmF0G-dj80kY")
MODEL = "gemini-2.5-flash"

# ===============================
# 📄 Extract PDF
# ===============================
def extract_text_from_pdf(uploaded_file):
    text = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# ===============================
# 🤖 ANALYZE
# ===============================
def analyze_resume(jd, resume):
    prompt = f"""
Return in markdown format:

**Match Score:** <number>%
**Matching Skills:** <comma separated>
**Missing Skills:** <comma separated>
**Suggestions:** <short paragraph>

Job Description:
{jd}

Resume:
{resume}
"""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    return response.text

# ===============================
# ✨ OPTIMIZE
# ===============================
def optimize_resume(jd, resume):
    prompt = f"""
Rewrite the resume keeping structure same.

- Use bullet points
- ATS friendly
- Add missing keywords

Return only formatted resume.

JD:
{jd}

Resume:
{resume}
"""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    return response.text

# ===============================
# 📄 DOCX FORMAT
# ===============================
def create_docx(content):
    doc = Document()

    for i, line in enumerate(content.split("\n")):
        line = line.strip()
        if not line:
            continue

        if i == 0:
            run = doc.add_paragraph().add_run(line)
            run.bold = True
            run.font.size = Pt(16)

        elif line.upper() in ["SUMMARY", "SKILLS", "EXPERIENCE", "PROJECTS", "EDUCATION"]:
            run = doc.add_paragraph().add_run(line.upper())
            run.bold = True

        elif line.startswith(("•", "-", "*")):
            doc.add_paragraph(line[1:].strip(), style='List Bullet')

        else:
            doc.add_paragraph(line)

    doc.save("optimized_resume.docx")

# ===============================
# 🔁 PDF
# ===============================
def convert_to_pdf():
    try:
        convert("optimized_resume.docx", "optimized_resume.pdf")
        return True
    except:
        return False

# ===============================
# 🎯 SCORE EXTRACT
# ===============================
def extract_score(text):
    match = re.search(r"(\d+)%", text)
    return int(match.group(1)) if match else 0

# ===============================
# 🌐 UI
# ===============================
st.markdown("""
# 🚀 AI Resume Optimizer  
### Optimize your resume with AI for better job matching
""")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
jd = st.text_area("Paste Job Description")

# ===============================
# 🔍 ANALYZE BUTTON
# ===============================
if uploaded_file and jd:
    if st.button("🔍 Analyze Resume"):

        resume_text = extract_text_from_pdf(uploaded_file)

        with st.spinner("Analyzing..."):
            analysis = analyze_resume(jd, resume_text)

        st.session_state["analysis"] = analysis
        st.session_state["resume_text"] = resume_text

# ===============================
# 📊 SHOW ANALYSIS
# ===============================
if "analysis" in st.session_state:

    analysis = st.session_state["analysis"]
    resume_text = st.session_state["resume_text"]

    score = extract_score(analysis)

    st.markdown("## 📊 Resume Analysis")

    col1, col2, col3 = st.columns(3)
    col1.metric("🎯 Match Score", f"{score}%")
    col2.metric("📈 Level", "Strong" if score >= 70 else "Moderate")
    col3.metric("⚠️ Improve", "Yes" if score < 70 else "Low")

    st.progress(score / 100)

    st.markdown("### 📋 Details")
    st.markdown(f"""
    <div style="background:#1e293b;padding:15px;border-radius:10px">
    {analysis}
    </div>
    """, unsafe_allow_html=True)

    # ===============================
    # 🚀 OPTIMIZE
    # ===============================
    if st.button("🚀 Generate Optimized Resume"):

        with st.spinner("Optimizing..."):
            optimized = optimize_resume(jd, resume_text)

        st.markdown("### ✨ Optimized Resume")
        st.text_area("Preview", optimized, height=400, label_visibility="collapsed")

        create_docx(optimized)

        if convert_to_pdf():
            with open("optimized_resume.pdf", "rb") as f:
                st.download_button("📥 Download PDF", f)
        else:
            with open("optimized_resume.docx", "rb") as f:
                st.download_button("📥 Download DOCX", f)
