

# 🧬 CareerDNA: AI-Driven Talent Intelligence & Behavioral Analytics

**CareerDNA** is a sophisticated recruitment engine that replaces subjective hiring with objective, real-time data. By synthesizing **GitHub Behavioral Heuristics** with **Large Language Models (LLM)**, the platform generates a high-fidelity "Engineering DNA" for any candidate.



## 🛠️ Key Technical Pillars

### 1. DevDNA | Behavioral Intelligence Engine
DevDNA moves beyond the resume by performing deep-packet analysis of a candidate's GitHub footprint via the **REST API**.
* **Commit Velocity & Discipline:** Algorithmic calculation of contribution consistency over time.
* **Chronological Work-Style Mapping:** Analysis of UTC-normalized commit timestamps to identify peak productivity windows (e.g., *Early Riser* vs. *Night Owl*).
* **Repository Maturity Index:** Automated scanning for professional standards including `LICENSE` documentation and `README` coverage.
* **Predictive Hireability Scoring:** A weighted mathematical model that aggregates documentation quality, community engagement, and technical discipline.

### 2. GrowHub | Integrated Career Ecosystem
A high-performance **React/Vite** bridge that synchronizes traditional professional profiles with real-time technical metrics, providing a 360-degree candidate evaluation.

### 3. AI Interviewer | Context-Aware Screening
A "Zero-Mock" interview generator powered by **Google Gemini 1.5 Flash**.
* **Automated PDF Text Extraction:** Utilizes `PyPDF2` for raw data ingestion from uploaded resumes, ensuring 100% data authenticity.
* **Dynamic Prompt Engineering:** Generates non-linear, role-specific technical questions.
* **Taxonomy-Based Categorization:** Questions are programmatically sorted into four tiers: **Fundamental**, **Applied**, **Architectural**, and **Systemic (Advanced)**.

---

## 🏗️ System Architecture & Stack

| Layer | Technology Stack |
| :--- | :--- |
| **Orchestration** | Python 3.14 / Streamlit |
| **Intelligence** | Google Generative AI (Gemini Pro) |
| **Data Extraction** | PyPDF2 (Binary-to-Text Parsing) |
| **Analytics** | Pandas, NumPy (Statistical Processing) |
| **Integration** | GitHub REST API v3 |
| **Frontend** | React.js / Vite (GrowHub Module) |



---

## 🛡️ The "Zero-Mimic" Protocol
**CareerDNA** is built on a foundation of **Data Veracity**.
* **No Static Databases:** All candidate metrics are fetched asynchronously from live production servers.
* **No Pre-Written Questions:** LLM responses are generated based specifically on the **unique text** extracted from the candidate's PDF.
* **Live Handshakes:** If the GitHub API or Gemini API is unreachable, the system will not "fake" data; it requires active network connectivity to function.

---

## 🚀 Deployment Guide

### Prerequisites
* Python 3.10+ 
* Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/CareerDNA.git

# Install core dependencies
pip install streamlit pandas numpy requests google-generativeai PyPDF2
```

### Execution
```bash
python -m streamlit run app.py
```

---

### 👤 Contact & Contribution
Talluru Chandrakanth

