import streamlit as st
import openai

openai.api_key = st.secrets["OPENAI_API_KEY"]

def generate_proposal(prompt="Generate a short contract proposal for a service bid."):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

def explain_section(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a contract risk analyst."},
                {"role": "user", "content": f"Explain this contract clause for risk: {text}"}
            ],
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

st.set_page_config(page_title="Proposal Draft Review Loop", layout="wide")
st.title("🧾 Proposal Draft Review Loop (HITL Demo)")

if "draft" not in st.session_state:
    st.session_state.draft = ""

# --- Generate Proposal Button ---
if st.button("✨ Generate Proposal with GPT-4o"):
    st.session_state.draft = generate_proposal()

# --- Editable Draft Viewer ---
if st.session_state.draft:
    edited_text = st.text_area("🔍 Review and Edit Proposal Draft:", value=st.session_state.draft, height=300)

    st.subheader("🧠 Analysis Tools")
    section_to_analyze = st.text_input("Paste a section you'd like explained or flagged:")

    cols = st.columns(2)

    with cols[0]:
        if st.button("💬 Explain this section"):
            if section_to_analyze.strip():
                explanation = explain_section(section_to_analyze)
                st.info(explanation)
            else:
                st.warning("Please enter a section to explain.")

    with cols[1]:
        if st.button("🚩 Flag this claim"):
            if section_to_analyze.strip():
                st.warning(f"Section flagged for review: \"{section_to_analyze}\"")
            else:
                st.warning("Please enter a section to flag.")

    if st.button("✅ Submit Review & Feedback"):
        st.success("Review submitted. (Simulated feedback loop)")

