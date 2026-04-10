Project: IP Mining tool

# Overview
The NJII Patent-Based Candidate Matching System is a web-based application designed to help the NJII Venture Studio identify the right people to engage based on their patented technologies. 
The system searches a MySQL database of patents and inventors, evaluates how well each patent aligns with NJII’s venture criteria, and ranks inventors based on their suitability for venture creation and company building.
This tool reduces manual screening and enables faster, data-driven decision making.

---

## Purpose
- Identify inventors and researchers using patent data
- Evaluate patent strength and commercialization potential
- Match inventors to NJII Venture Studio criteria
- Rank candidates for outreach and venture development

---

# Key Features
- *Patent Search*
  - Search by patent title, inventor name, keywords, or technology area
- **Inventor Matching**
  - Associate patents with individual inventors
- **Rule-Based Filtering**
  - Exclude patents that do not meet minimum NJII requirements
- **Weighted Scoring System**
  - Scores inventors based on:
    - Technical strength of patents
    - Early-stage readiness
    - Capital efficiency
    - Strategic fit with NJII/NJIT
    - 18-month commercialization feasibility
- **Ranked Results**
  - Displays inventors ordered by fit score
- **Web Dashboard**
  - Simple interface for NJII staff to review candidates

---

#Technology Stack

### **Frontend (Website)**
- HTML
- CSS
- JavaScript
- React (recommended)

### **Backend**
- Python (FastAPI or Flask)
  *or*
- Node.js (Express)

### **Database**
- **MySQL**
  - Stores patent records
  - Stores inventor profiles
  - Stores scoring results

### **APIs / Data Sources**
- USPTO patent data (bulk data or API)
- Manual patent entry (initial MVP)

---

#Scoring Logic (High-Level)
Each inventor is evaluated based on their patents using a weighted scoring model:

- Patent defensibility and novelty
- Relevance to NJII focus areas (AI/ML, Human Health, Advanced Manufacturing)
- Commercial viability within 18 months
- Estimated funding required
- Strategic alignment with NJIT research strengths

Each category contributes to a final **Fit Score (0–10)**.
