import streamlit as st
import groq
from PyPDF2 import PdfReader
import re
import pandas as pd
from fpdf import FPDF

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="ResumeAI", layout="wide")

# --- 2. CUSTOM CSS STYLES ---
st.markdown("""
<style>
    .report-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #374151;
        margin-bottom: 15px;
    }
    .header-text { color: #00d4ff; font-weight: bold; }
    .stButton>button {
        background: linear-gradient(90deg, #00d4ff, #0072ff);
        color: white;
        border: none;
        padding: 12px 30px;
        font-weight: bold;
        border-radius: 10px;
        width: 100%;
        transition: 0.4s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.6);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---
client = groq.Groq(api_key="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")

def extract_text_from_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def generate_pdf_report(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="ResumeAI - Analysis Report", ln=1, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    clean_text = text_content.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. UI LAYOUT ---
st.title("🛡️ ResumeAI")
st.markdown("<p style='font-size: 20px; color: #9ca3af;'>Impact First | AI-Driven Career Analysis</p>", unsafe_allow_html=True)
st.write("---")

tab1, tab2 = st.tabs(["🎓 Student / Job Seeker", "🏢 Company Screening"])

# --- TAB 1: STUDENT / JOB SEEKER ---
with tab1:
    col_input, col_output = st.columns([1, 1.5], gap="large")
    
    with col_input:
        st.markdown("<h3 class='header-text'>Upload Resume</h3>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Drop your resume (PDF) here", type=['pdf'])
        btn = st.button("Analyze Resume")

    if uploaded_file and btn:
        resume_text = extract_text_from_pdf(uploaded_file)
        
        prompt = f"""
        Act as an expert ATS (Applicant Tracking System) and Career Coach.
        Analyze the following resume and return the output ONLY in this structured format:
        SCORE: [0-100]
        STRENGTHS: [List 3 points]
        WEAKNESSES: [List 3 points]
        ADVICE: [3 lines of career growth advice]
        
        Resume: {resume_text}
        """
        
        with st.spinner("AI is analyzing your resume..."):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            raw_res = response.choices[0].message.content
            score = int(re.search(r"SCORE:\s*(\d+)", raw_res).group(1))

        with col_output:
            st.markdown("<h3 class='header-text'>Analysis Report</h3>", unsafe_allow_html=True)
            st.write(f"**ATS Compatibility Score: {score}%**")
            st.progress(score / 100)
            
            st.markdown(f"""
            <div class="report-card" style="border-left: 6px solid #10b981;">
                <h4 style="color: #10b981;">✅ Key Strengths</h4>
                <p>{raw_res.split('STRENGTHS:')[1].split('WEAKNESSES:')[0].strip()}</p>
            </div>
            <div class="report-card" style="border-left: 6px solid #ef4444;">
                <h4 style="color: #ef4444;">⚠️ Missing Skills / Gaps</h4>
                <p>{raw_res.split('WEAKNESSES:')[1].split('ADVICE:')[0].strip()}</p>
            </div>
            <div class="report-card" style="border-left: 6px solid #f59e0b;">
                <h4 style="color: #f59e0b;">💡 Career Growth Advice</h4>
                <p>{raw_res.split('ADVICE:')[1].strip()}</p>
            </div>
            """, unsafe_allow_html=True)

            # PDF Download Button
            try:
                pdf_bytes = generate_pdf_report(raw_res)
                st.download_button(
                    label="📥 Download Analysis Report (PDF)",
                    data=pdf_bytes,
                    file_name="Resume_Analysis.pdf",
                    mime="application/pdf"
                )
            except:
                st.warning("PDF generation failed, but you can see the report above.")

# --- TAB 2: COMPANY SCREENING ---
with tab2:
    st.markdown("<h3 class='header-text'>For Companies: Bulk Candidate Screening</h3>", unsafe_allow_html=True)
    
    jd_text = st.text_area("Paste the Job Description (JD) here:", height=150, placeholder="e.g. Looking for a Python Developer...")
    bulk_files = st.file_uploader("Upload resumes of all candidates", type=['pdf'], accept_multiple_files=True)
    
    if st.button("🚀 Rank All Candidates") and bulk_files and jd_text:
        results = []
        with st.spinner("AI is ranking all candidates..."):
            for file in bulk_files:
                text = extract_text_from_pdf(file)
                bulk_prompt = f"Compare Resume with JD. Give score/100 and 10-word reason. JD: {jd_text} Resume: {text}. Format: Score | Reason"
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": bulk_prompt}]
                )
                res_text = response.choices[0].message.content
                try:
                    parts = res_text.split('|')
                    results.append({"Candidate": file.name, "Score": parts[0].strip(), "Verdict": parts[1].strip()})
                except: continue
        
        if results:
            st.success("Analysis Complete! Ranking Table:")
            st.table(pd.DataFrame(results))
