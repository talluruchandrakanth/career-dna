import requests
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import PyPDF2
import os
import sqlite3
import time
from datetime import datetime
from collections import Counter
import google.generativeai as genai

# ==========================================
# 1️⃣ CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="DevDNA Enterprise", layout="wide", page_icon="🧬")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    div.css-1r6slb0, div.stMetric {
        background-color: #1E2329;
        border: 1px solid #30363D;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stButton>button {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF914D 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
    }
    div[data-testid="stTable"] {
        background-color: #1E2329;
        border-radius: 10px;
        padding: 10px;
    }
    iframe { border-radius: 10px; border: 1px solid #30363D; }
    .badge {
        display: inline-block;
        padding: 8px 12px;
        margin: 4px;
        border-radius: 6px;
        font-weight: 500;
        font-size: 13px;
        border: 1px solid;
    }
    .badge-found {
        background-color: rgba(34, 197, 94, 0.2);
        color: #22C55E;
        border-color: #22C55E;
    }
    .badge-missing {
        background-color: rgba(239, 68, 68, 0.2);
        color: #EF4444;
        border-color: #EF4444;
    }
    .rec-card {
        background: linear-gradient(135deg, #1E2329 0%, #252D36 100%);
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 24px;
        margin: 12px 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        position: relative;
        overflow: hidden;
    }
    .rec-card:hover {
        border-color: #58A6FF;
        box-shadow: 0 8px 24px rgba(88, 166, 255, 0.15);
        transform: translateY(-2px);
    }
    .rec-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #58A6FF 0%, #79C0FF 100%);
    }
    .rec-role-name {
        font-size: 18px;
        font-weight: 700;
        color: #79C0FF;
        margin-bottom: 12px;
    }
    .rec-match-score {
        font-size: 28px;
        font-weight: 800;
        color: #22C55E;
        margin-bottom: 8px;
    }
    .rec-progress-bar {
        width: 100%;
        height: 6px;
        background-color: #0E1117;
        border-radius: 3px;
        overflow: hidden;
        margin-bottom: 16px;
    }
    .rec-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #22C55E 0%, #84E1BC 100%);
        border-radius: 3px;
    }
    .rec-description {
        font-size: 14px;
        color: #C9D1D9;
        line-height: 1.6;
        margin-top: 12px;
    }
</style>
""", unsafe_allow_html=True)

ADMIN_PASSWORD = "chandu2005@admin"


# ==========================================
# 2️⃣ DATABASE ENGINE
# ==========================================
def init_db():
    conn = sqlite3.connect('dna_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY, timestamp TEXT, tool_used TEXT, user_id TEXT, details TEXT)''')
    conn.commit()
    conn.close()

def save_log(tool, user, details=""):
    conn = sqlite3.connect('dna_database.db')
    c = conn.cursor()
    c.execute("INSERT INTO history (timestamp, tool_used, user_id, details) VALUES (?, ?, ?, ?)",
              (datetime.now(), tool, user, details))
    conn.commit()
    conn.close()

def get_logs():
    conn = sqlite3.connect('dna_database.db')
    df = pd.read_sql_query("SELECT * FROM history ORDER BY id DESC", conn)
    conn.close()
    return df

init_db()

# ==========================================
# 3️⃣ GITHUB API FETCHING (DevDNA)
# ==========================================
def fetch_detailed_github_data(username):
    try:
        user_url = f"https://api.github.com/users/{username}"
        user_resp = requests.get(user_url)
        user_info = user_resp.json() if user_resp.status_code == 200 else {}

        repo_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
        repo_resp = requests.get(repo_url)
        
        if repo_resp.status_code == 200:
            repos = repo_resp.json()
            
            update_dates = [datetime.strptime(r['updated_at'], "%Y-%m-%dT%H:%M:%SZ") for r in repos]
            hours = [d.hour for d in update_dates]
            
            if hours:
                avg_hour = np.mean(hours)
                if 9 <= avg_hour <= 18:
                    work_style = "🏢 9-to-5 Developer"
                elif 19 <= avg_hour <= 23 or 0 <= avg_hour <= 4:
                    work_style = "🦉 Night Owl / Hacker"
                else:
                    work_style = "🌅 Early Riser"
            else:
                work_style = "Unknown"

            if update_dates:
                days_since_update = [(datetime.now() - d).days for d in update_dates]
                avg_gap = np.mean(days_since_update)
                consistency_score = max(0, min(100, 100 - int(avg_gap)))
                burnout_risk = "High (Inactive > 2mo)" if min(days_since_update) > 60 else "Low (Active)"
            else:
                consistency_score = 0
                burnout_risk = "N/A"

            followers = user_info.get('followers', 0)
            if followers > 500:
                network_score = "⭐ Industry Leader"
            elif followers > 50:
                network_score = "🔗 Well Connected"
            else:
                network_score = "👤 Independent Coder"

            readme_count = sum([1 for r in repos if r['description']]) 
            has_license = sum([1 for r in repos if r['license']])
            quality_score = int(((readme_count + has_license) / (max(1, len(repos)) * 2)) * 100)

            languages = [r['language'] for r in repos if r['language']]
            lang_counts = Counter(languages)
            top_lang = lang_counts.most_common(1)[0][0] if languages else "Unknown"
            
            if top_lang in ['Python', 'Jupyter Notebook', 'R']:
                identity = "AI/Data Science Engineer"
            elif top_lang in ['JavaScript', 'TypeScript', 'HTML', 'CSS', 'React']:
                identity = "Frontend/Full Stack Dev"
            elif top_lang in ['Java', 'C++', 'Go', 'Rust', 'C#']:
                identity = "Backend/Systems Engineer"
            else:
                identity = "Generalist Developer"

            hire_prob = (consistency_score * 0.4) + (quality_score * 0.3) + (min(100, followers + sum([r.get('stargazers_count', 0) for r in repos])) * 0.3)
            hire_prob = int(min(98, hire_prob))

            return {
                "username": username,
                "avatar": user_info.get('avatar_url', ''),
                "total_repos": len(repos),
                "stars": sum([repo.get('stargazers_count', 0) for repo in repos]),
                "followers": followers,
                "languages": lang_counts,
                "consistency": int(consistency_score),
                "quality": quality_score,
                "burnout": burnout_risk,
                "identity": identity,
                "top_lang": top_lang,
                "work_style": work_style,
                "network_score": network_score,
                "hire_prob": hire_prob,
                "activity_dates": update_dates
            }
        else:
            return None
    except Exception as e:
        return None

# ==========================================
# 4️⃣ TOOL 1: DevDNA (Recruiter Logic)
# ==========================================
def run_devdna():
    st.header("🧬 DevDNA: Recruiter Simulation System")
    st.caption("Advanced Behavioral Analysis & Comparison Engine (No Mocks)")
    
    tab1, tab2 = st.tabs(["👤 Single Candidate Scan", "🆚 Head-to-Head Comparison"])

    with tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            gh_user = st.text_input("GitHub Username", key="single_user")
            analyze_btn = st.button("🚀 Run Recruiter Scan")

        if analyze_btn and gh_user:
            with st.spinner(f"🔍 Analyzing behavioral patterns for {gh_user}..."):
                data = fetch_detailed_github_data(gh_user)
                
                if data:
                    save_log("DevDNA", gh_user, f"Identity: {data['identity']}")
                    
                    c1, c2 = st.columns([1, 5])
                    with c1:
                        if data['avatar']:
                            st.image(data['avatar'], width=100)
                    with c2:
                        st.subheader(f"{data['identity']}")
                        st.caption(f"Top Language: {data['top_lang']} | {data['network_score']}")

                    st.markdown("---")

                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Consistency", f"{data['consistency']}%", "Discipline")
                    k2.metric("Code Quality", f"{data['quality']}/100", "Documentation")
                    k3.metric("Hireability", f"{data['hire_prob']}%", "AI Prediction")
                    k4.metric("Work Style", data['work_style'])

                    st.success(f"💡 **Insight:** This candidate is a **{data['work_style']}** who is **{data['network_score']}**. Their burnout risk is **{data['burnout']}**.")
                    
                    st.subheader("📅 Activity Timeline")
                    if data['activity_dates']:
                        dates_df = pd.DataFrame(data['activity_dates'], columns=['date'])
                        dates_df['date'] = dates_df['date'].dt.date
                        chart_data = dates_df['date'].value_counts().sort_index()
                        st.bar_chart(chart_data)
                    else:
                        st.info("No activity data available for visualization.")
                else:
                    st.error(f"⚠️ User '{gh_user}' not found.")

    with tab2:
        st.markdown("### ⚔️ Compare Two Candidates")
        st.caption("See who fits the job description better.")
        
        cc1, cc2 = st.columns(2)
        with cc1:
            user_a = st.text_input("Candidate A", placeholder="e.g. torvalds")
        with cc2:
            user_b = st.text_input("Candidate B", placeholder="e.g. facebook")
            
        compare_btn = st.button("⚔️ Fight!")

        if compare_btn and user_a and user_b:
            with st.spinner("⚔️ Calculating matchup stats..."):
                data_a = fetch_detailed_github_data(user_a)
                data_b = fetch_detailed_github_data(user_b)
                
                if data_a and data_b:
                    winner = user_a if data_a['hire_prob'] > data_b['hire_prob'] else user_b
                    st.success(f"🏆 **Winner:** {winner} has a stronger technical profile.")
                    
                    comp_data = {
                        "Metric": ["Hireability Score", "Consistency", "Docs Quality", "Followers", "Work Style", "Identity"],
                        f"{user_a}": [f"{data_a['hire_prob']}%", f"{data_a['consistency']}%", data_a['quality'], data_a['followers'], data_a['work_style'], data_a['identity']],
                        f"{user_b}": [f"{data_b['hire_prob']}%", f"{data_b['consistency']}%", data_b['quality'], data_b['followers'], data_b['work_style'], data_b['identity']]
                    }
                    st.table(pd.DataFrame(comp_data).set_index("Metric"))
                else:
                    st.error("One or both users not found.")

# ==========================================
# 5️⃣ TOOL 2: GrowHub (React Integration)
# ==========================================

# --- 1. AI KNOWLEDGE BASE (REAL INDUSTRY DATA) ---
JOB_ROLES = {
    "Frontend Developer": {
        "skills": ["html", "css", "javascript", "react", "vue", "typescript", "figma", "sass", "nextjs", "tailwind"],
        "desc": "Focuses on user-facing interface and design implementation.",
        "courses": ["Meta Front-End Developer Certificate (Coursera)", "FreeCodeCamp Responsive Web Design", "Frontend Masters - React Path"],
        "certs": ["Meta Front-End Certificate", "Google UX Design Certificate"]
    },
    "Backend Developer": {
        "skills": ["python", "nodejs", "sql", "api", "express", "django", "docker", "aws", "mongodb", "redis", "microservices"],
        "desc": "Handles server-side logic, databases, and API architecture.",
        "courses": ["Node.js Developer Roadmap (roadmap.sh)", "Python for Everybody (UMich)", "Back-End Engineer Path (Codecademy)"],
        "certs": ["AWS Certified Developer", "Oracle Certified Professional: Java"]
    },
    "Fullstack Developer": {
        "skills": ["react", "nodejs", "sql", "javascript", "html", "css", "docker", "aws", "typescript", "git", "api"],
        "desc": "Manages both client-side and server-side development.",
        "courses": ["Full Stack Open (University of Helsinki)", "The Web Developer Bootcamp (Udemy)"],
        "certs": ["AWS Certified Solutions Architect", "IBM Full Stack Developer"]
    },
    "Data Scientist": {
        "skills": ["python", "machine learning", "statistics", "sql", "pandas", "deep learning", "tensorflow", "pytorch", "tableau"],
        "desc": "Uses advanced analytics and AI to interpret complex data.",
        "courses": ["Machine Learning Specialization (Andrew Ng)", "Kaggle Micro-courses", "Data Science MicroMasters (edX)"],
        "certs": ["Google Data Analytics Professional", "IBM Data Science Professional"]
    },
    "Civil Engineer": {
        "skills": ["autocad", "staad pro", "surveying", "concrete", "structural analysis", "revit", "estimation", "construction"],
        "desc": "Designs and manages physical infrastructure projects.",
        "courses": ["Autodesk Revit Architecture (LinkedIn)", "Staad.Pro Structural Analysis (Udemy)"],
        "certs": ["EIT (Engineer In Training)", "PMP (Project Management)"]
    },
    "UI/UX Designer": {
        "skills": ["figma", "adobe xd", "wireframing", "prototyping", "user research", "photoshop", "illustrator"],
        "desc": "Designs intuitive and aesthetic digital user journeys.",
        "courses": ["Google UX Design Professional Certificate", "Interaction Design Foundation"],
        "certs": ["Adobe Certified Professional", "Google UX Design Certificate"]
    },
    "DevOps Engineer": {
        "skills": ["docker", "kubernetes", "linux", "jenkins", "aws", "terraform", "ansible", "ci/cd", "bash"],
        "desc": "Specializes in automation and deployment infrastructure.",
        "courses": ["Cloud Dev Ops Nanodegree (Udacity)", "Docker and Kubernetes Guide"],
        "certs": ["CKA (Certified Kubernetes Admin)", "AWS DevOps Engineer Pro"]
    },
    "Mechanical Engineer": {
        "skills": ["solidworks", "cad", "thermodynamics", "manufacturing", "mechanical design", "ansys", "matlab", "robotics"],
        "desc": "Designs, develops, and tests mechanical devices.",
        "courses": ["SolidWorks Mastery (Udemy)", "Mechanical Engineering Design (MIT)"],
        "certs": ["CSWP (Certified SOLIDWORKS Pro)", "PE License"]
    },
    "Software Tester": {
        "skills": ["selenium", "manual testing", "automation", "unit testing", "bug tracking", "quality assurance", "cypress"],
        "desc": "Ensures software quality through rigorous testing.",
        "courses": ["Selenium WebDriver with Java", "Complete Guide to Manual Testing"],
        "certs": ["ISTQB Certified Tester", "LambdaTest Selenium Cert"]
    }
}
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text.lower()


def get_role_similarity(resume_text):
    results = []
    for role, data in JOB_ROLES.items():
        match_count = sum(1 for skill in data['skills'] if skill in resume_text)
        percentage = (match_count / len(data['skills'])) * 100
        results.append({
            "role": role,
            "score": percentage,
            "desc": data['desc'],
            "skills": data['skills']
        })
    return sorted(results, key=lambda x: x['score'], reverse=True)
def run_growhub():
    st.title("💼 Pro AI Resume Analyzer")
    st.caption("Building your personal data-driven career path.")

    col_input1, col_input2 = st.columns([2, 1])
    with col_input1:
        uploaded_file = st.file_uploader("📤 Upload Resume (PDF format)", type="pdf")
    with col_input2:
        target_role = st.selectbox("🎯 Select Applied Role", ["-- Select a Role --"] + list(JOB_ROLES.keys()))

    if uploaded_file and target_role != "-- Select a Role --":

        resume_text = extract_text_from_pdf(uploaded_file)

        all_role_matches = get_role_similarity(resume_text)
        current_role_data = next(item for item in all_role_matches if item["role"] == target_role)
        detected_role_data = all_role_matches[0]

        # MATCH SCORE
        st.markdown(f"""
            <div class="match-score-container">
                <h1 style="color:white;">{round(current_role_data['score'])}% Compatibility</h1>
                <p>Analyzing qualifications for {target_role}</p>
            </div>
        """, unsafe_allow_html=True)

        # WARNING
        if detected_role_data['role'] != target_role:
            st.markdown(f"""
                <div class="warning-box">
                    ⚠️ Better match: <b>{detected_role_data['role']}</b>
                </div>
            """, unsafe_allow_html=True)

        # ✅ COLUMNS (FIXED POSITION)
        c1, c2 = st.columns(2)

        # LEFT COLUMN
        with c1:
            st.markdown(f'<div class="card"><h3>📋 Required Skills</h3>', unsafe_allow_html=True)

            req_badges = " ".join([
                f'<span class="badge badge-found">{s.upper()}</span>'
                if s in resume_text
                else f'<span class="badge badge-missing">{s.upper()}</span>'
                for s in JOB_ROLES[target_role]['skills']
            ])

            st.markdown(
                f'<div style="display:flex; flex-wrap:wrap; gap:8px;">{req_badges}</div></div>',
                unsafe_allow_html=True
            )

        # RIGHT COLUMN
        with c2:
            found = [s for s in JOB_ROLES[target_role]['skills'] if s in resume_text]
            missing = [s for s in JOB_ROLES[target_role]['skills'] if s not in resume_text]

            st.markdown('<div class="card"><h3>📊 Skills Gap Analysis</h3>', unsafe_allow_html=True)

            st.markdown(f"<b>✅ Found ({len(found)})</b>", unsafe_allow_html=True)
            found_badges = " ".join([f'<span class="badge badge-found">{s.upper()}</span>' for s in found])
            st.markdown(f'<div style="display:flex; flex-wrap:wrap; gap:8px;">{found_badges}</div>', unsafe_allow_html=True)

            st.markdown(f"<b>➕ Missing ({len(missing)})</b>", unsafe_allow_html=True)
            missing_badges = " ".join([f'<span class="badge badge-missing">{s.upper()}</span>' for s in missing])
            st.markdown(f'<div style="display:flex; flex-wrap:wrap; gap:8px;">{missing_badges}</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # RECOMMENDATIONS
        st.markdown("<div style='margin-top: 40px;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: #79C0FF; font-size: 24px; margin-bottom: 20px;'>💡 Best Suited Alternative Roles</h2>", unsafe_allow_html=True)

        rec_cols = st.columns(3)
        recommendations = [r for r in all_role_matches if r['role'] != target_role][:3]

        for idx, rec in enumerate(recommendations):
            with rec_cols[idx]:
                match_percentage = round(rec['score'])
                st.markdown(f"""
                <div class="rec-card">
                    <div class="rec-role-name">{rec['role']}</div>
                    <div class="rec-match-score">{match_percentage}% Match</div>
                    <div class="rec-progress-bar">
                        <div class="rec-progress-fill" style="width: {match_percentage}%;"></div>
                    </div>
                    <div class="rec-description">{rec['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ROADMAP
        st.divider()
        st.markdown("## 📖 Career Growth Roadmap")

        s_col1, s_col2 = st.columns([2, 1])

        with s_col1:
            st.markdown('<div class="card"><h4>🚀 Priority Learning Plan</h4>', unsafe_allow_html=True)
            for m in missing[:3]:
                st.write(f"🔹 Master {m.upper()}")
            st.markdown('</div>', unsafe_allow_html=True)

        with s_col2:
            st.markdown('<div class="card"><h4>🏅 Certifications</h4>', unsafe_allow_html=True)
            for cert in JOB_ROLES[target_role]['certs']:
                st.info(cert)
            st.markdown('</div>', unsafe_allow_html=True)

        # SAVE DATASET
        df_db = pd.DataFrame([[target_role, resume_text]], columns=['role', 'resume_text'])
        df_db.to_csv("user_resume_dataset.csv", mode='a', header=not os.path.exists("user_resume_dataset.csv"), index=False)

    else:
        st.info("👋 Upload resume & select role to start.")

# ==========================================
# 6️⃣ TOOL 3: AI Interview Generator
# ==========================================
# Hardcoded Gemini API Key
GEMINI_API_KEY = "AIzaSyCZ1ggd9L8mdS2ehNDeFp_SxBh_8JwNfLk"

def run_interview_generator():
    st.header("🎙️ AI Interview Simulator")
    st.caption("Generates real, role-specific interview questions using the Gemini AI API.")
    
    st.markdown("### 📄 Step 1: Input Your Profile")
    resume_skills = st.text_area(
        "Paste your core skills or resume summary here:", 
        placeholder="e.g., Spring Boot, React, REST APIs, Java, SQL..."
    )
    
    target_role = st.text_input("Target Job Title", placeholder="e.g., Backend Developer")

    if st.button("🧠 Generate Interview Questions"):
        if resume_skills and target_role:
            with st.spinner("Analyzing skills and generating technical questions..."):
                genai.configure(api_key=GEMINI_API_KEY)
                
                system_prompt = f"""
                You are a Senior Technical Recruiter hiring for a {target_role}.
                The candidate has the following skills: {resume_skills}.
                
                Generate a technical interview categorized EXACTLY into these 4 levels:
                1. Beginner / Basic Concepts
                2. Intermediate / Application
                3. Professional / Architecture & Best Practices
                4. Advanced / System Design & Troubleshooting
                
                Provide 2 highly specific, realistic questions for each level based ONLY on their skills.
                Format the output cleanly using Markdown headers, and make the questions bold. Do not include answers.
                """
                
                try:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    response = model.generate_content(system_prompt)
                    
                    st.success("✅ Interview Generated Successfully!")
                    st.markdown("---")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"❌ API Error: {e}")
        else:
            st.error("⚠️ Please enter both your skills and a target role.")
# ==========================================
# 6️⃣ TOOL 4: AI Interview Generator (Either/Or)
# ==========================================
def run_interview_generator():
    st.header("🎙️ AI Interview Simulator")
    st.caption("Generate real, role-specific interview questions based on your profile.")
    target_role = st.text_input("Target Job Title", placeholder="e.g., Spring Boot Backend Developer")
    
    st.markdown("### 📄 Step 1: Provide Your Background")
    
    # 🌟 NEW: The Either/Or Toggle Switch
    input_method = st.radio("How would you like to provide your experience?", 
                            ("📄 Upload Resume (PDF)", "✍️ Paste Skills Manually"))
    
    candidate_context = "" # This will hold the text regardless of how they input it
    
    # Logic for Option 1: PDF Upload
    if input_method == "📄 Upload Resume (PDF)":
        uploaded_file = st.file_uploader("Upload your resume", type=["pdf"])
        if uploaded_file:
            with st.spinner("📄 Extracting text from your resume..."):
                try:
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    for page in pdf_reader.pages:
                        candidate_context += page.extract_text()
                except Exception as e:
                    st.error(f"❌ Could not read the PDF. Error: {e}")
                    
    # Logic for Option 2: Manual Text Entry
    else:
        candidate_context = st.text_area(
            "Paste your core skills or resume summary here:", 
            placeholder="e.g., Spring Boot, React, REST APIs, Java, SQL..."
        )

    if st.button("🧠 Generate Interview Questions"):
        if candidate_context and target_role:
            with st.spinner("🤖 AI is analyzing your profile and writing questions..."):
                genai.configure(api_key=GEMINI_API_KEY)
                
                # The prompt now flexibly accepts whatever text 'candidate_context' holds
                system_prompt = f"""
                You are a Senior Technical Recruiter hiring for a {target_role}.
                Here is the candidate's background/skills: 
                {candidate_context}
                
                Analyze this profile, identify their core technical skills, 
                and generate a technical interview categorized EXACTLY into these 4 levels:
                1. Beginner / Basic Concepts
                2. Intermediate / Application
                3. Professional / Architecture & Best Practices
                4. Advanced / System Design & Troubleshooting
                
                Provide 2 highly specific, realistic questions for each level based ONLY on the actual technologies and experience mentioned.
                Format the output cleanly using Markdown headers, and make the questions bold. Do not include answers.
                """
                
                try:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    response = model.generate_content(system_prompt)
                    
                    st.success("✅ Interview Generated Successfully!")
                    st.markdown("---")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"❌ API Error: {e}")
        else:
            st.error("⚠️ Please provide your skills/resume and enter a target role.")

# ==========================================
# 7️⃣ MAIN NAVIGATION
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9311/9311388.png", width=60)
    st.title("DevDNA Enterprise")
    page = st.radio("Select Tool", ["🧬 DevDNA (Recruiter)", "🚀 GrowHub (Resume)", "🎙️ AI Interviewer"])
    st.markdown("---")
    
if page == "🧬 DevDNA (Recruiter)":
    run_devdna()
elif page == "🚀 GrowHub (Resume)":
    run_growhub()
elif page == "🎙️ AI Interviewer":
    run_interview_generator()