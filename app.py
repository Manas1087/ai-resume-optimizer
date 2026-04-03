import streamlit as st
import fitz  # PyMuPDF
from google import genai
from docx import Document
from docx.shared import Pt
from docx2pdf import convert

# ===============================
# 🔑 GEMINI CLIENT SETUP
# ===============================
client = genai.Client(api_key="AIzaSyBBbSYW53z72L7KdMdTxc0fmF0G-dj80kY")
MODEL = "gemini-2.5-flash"

# ===============================
# 📄 Extract text from PDF
# ===============================
def extract_text_from_pdf(uploaded_file):
    text = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# ===============================
# 🤖 Analyze Resume
# ===============================
def analyze_resume(jd, resume):
    prompt = f"""
    Compare the Job Description and Resume.

    Return strictly:
    Match Score: <number>%
    Matching Skills: <comma separated>
    Missing Skills: <comma separated>
    Suggestions: <short paragraph>

    Job Description:
    {jd}

    Resume:
    {resume}
    """

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error: {e}"

# ===============================
# ✨ Optimize Resume
# ===============================
def optimize_resume(jd, resume):
    prompt = f"""
    Rewrite the resume BUT KEEP STRUCTURE SIMILAR TO ORIGINAL.

    IMPORTANT:
    - Keep sections like EDUCATION, EXPERIENCE, PROJECTS
    - Use bullet points (• or -)
    - Do NOT make long paragraphs
    - Maintain clean professional resume format
    - Add missing keywords naturally

    Return ONLY formatted resume text (no explanation)

    Job Description:
    {jd}

    Resume:
    {resume}
    """

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error: {e}"

# ===============================
# 📄 Create DOCX (Formatted)
# ===============================
def create_docx(content):
    doc = Document()

    lines = content.split("\n")

    for i, line in enumerate(lines):
        line = line.strip()

        if not line:
            continue

        # NAME (first line)
        if i == 0:
            p = doc.add_paragraph()
            run = p.add_run(line)
            run.bold = True
            run.font.size = Pt(16)

        # SECTION HEADINGS
        elif line.upper() in ["SUMMARY", "SKILLS", "EXPERIENCE", "PROJECTS", "EDUCATION", "CERTIFICATIONS"]:
            p = doc.add_paragraph()
            run = p.add_run(line.upper())
            run.bold = True

        # BULLET POINTS
        elif line.startswith("•") or line.startswith("-") or line.startswith("*"):
            doc.add_paragraph(line[1:].strip(), style='List Bullet')

        else:
            doc.add_paragraph(line)

    doc.save("optimized_resume.docx")

# ===============================
# 🔁 Convert to PDF
# ===============================
def convert_to_pdf():
    try:
        convert("optimized_resume.docx", "optimized_resume.pdf")
        return True
    except:
        return False

# ===============================
# 🌐 STREAMLIT UI
# ===============================

st.set_page_config(page_title="AI Resume Optimizer", layout="wide")
st.title("🚀 AI Resume Optimizer (Gemini + ATS Friendly)")

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

    st.subheader("📊 Resume Analysis")
    st.text(analysis)

    # Extract score
    try:
        score_line = analysis.split("\n")[0]
        score = int(score_line.split(":")[1].replace("%", "").strip())
    except:
        score = 0

    # Match indicator
    if score >= 70:
        st.success(f"✅ Strong Match: {score}%")
    elif score >= 50:
        st.warning(f"⚠️ Moderate Match: {score}%")
    else:
        st.error(f"❌ Low Match: {score}%")

    # ===============================
    # 👉 OPTIMIZE BUTTON
    # ===============================
    if st.button("👉 Optimize Resume"):

        with st.spinner("Optimizing..."):
            optimized_content = optimize_resume(jd, resume_text)

        st.subheader("✨ Optimized Resume")
        st.text_area("", optimized_content, height=400)

        # Create DOCX
        create_docx(optimized_content)

        # Convert to PDF
        pdf_created = convert_to_pdf()

        # Download
        if pdf_created:
            with open("optimized_resume.pdf", "rb") as f:
                st.download_button(
                    "📥 Download PDF",
                    f,
                    file_name="optimized_resume.pdf"
                )
        else:
            with open("optimized_resume.docx", "rb") as f:
                st.download_button(
                    "📥 Download DOCX",
                    f,
                    file_name="optimized_resume.docx"
                )