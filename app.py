import streamlit as st
import pandas as pd
import re

# -----------------------------
# Load Initial Issues
# -----------------------------
# Excel file must be in the same repo
df = pd.read_excel("All Events for Keywords.xlsx")



# Normalize column names
df.columns = df.columns.str.strip().str.lower()

# -----------------------------
# Helper functions
# -----------------------------
def normalize(text):
    text = str(text).lower()
    text = re.sub(r"[()/\-#,]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# Generic / noisy terms to ignore
GENERIC_TERMS = {
    "engine", "system", "unit", "module", "assembly",
    "case", "indicating", "control", "pressure",
    "mount", "data", "number"
}

def extract_issue_terms(issue):
    words = normalize(issue).split()

    stop_words = {
        "issue", "assembly", "module",
        "case", "unit", "valve", "sensor",
        "actuator", "stage"
    }

    return {
        w for w in words
        if len(w) >= 3
        and w not in stop_words
        and w not in GENERIC_TERMS
    }

# -----------------------------
# Build Initial Issue → keywords map
# IMPORTANT: column name is "initial issues"
# -----------------------------
issue_terms = {
    issue: extract_issue_terms(issue)
    for issue in df["initial issues"].dropna()
}

# -----------------------------
# Core logic: match + rank
# -----------------------------
def match_and_rank_narrative(narrative):
    narrative = normalize(narrative)
    results = []

    for issue, terms in issue_terms.items():
        matched = [
            term for term in terms
            if re.search(rf"\b{re.escape(term)}\b", narrative)
        ]

        if matched:
            results.append({
                "Initial Issue": issue,
                "Matched Keywords": ", ".join(matched),
                "Score": len(matched)
            })

    return sorted(results, key=lambda x: x["Score"], reverse=True)

def extract_narrative_keywords(narrative):
    narrative_words = set(normalize(narrative).split())
    valid_terms = set().union(*issue_terms.values())

    return sorted(
        word for word in narrative_words
        if word in valid_terms and word not in GENERIC_TERMS
    )

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Initial Issue Identifier", layout="wide")

st.title("Initial Issue Auto-Identification (Prototype)")
st.write("Paste an engine event narrative below and click **Analyze**.")

narrative = st.text_area(
    "Engine Event Narrative",
    height=150,
    placeholder="Engine start fault ECAM on engine start plus engine #1 EGT overlimit"
)

if st.button("Analyze"):
    if narrative.strip():
        narrative_keywords = extract_narrative_keywords(narrative)
        ranked_results = match_and_rank_narrative(narrative)

        st.subheader("🔑 Extracted Narrative Keywords")
        st.write(", ".join(narrative_keywords) if narrative_keywords else "No keywords detected")

        st.subheader("📋 Ranked Initial Issues")
        if ranked_results:
            st.dataframe(pd.DataFrame(ranked_results))
        else:
            st.warning("No relevant Initial Issues found.")
    else:
        st.warning("Please enter a narrative.")

