import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

def generate_proposal(prompt="Generate a short contract proposal for a service bid."):
    try:
        response = client.chat.completions.create(
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
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": text}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

st.set_page_config(page_title="Proposal Draft Review Loop", layout="wide")
st.title("🧾 Proposal Draft Review Loop (HITL Demo)")
st.markdown("""
<style>
a.no-underline {
    text-decoration: none;
    color: inherit;
    cursor: pointer;
}
</style>
Simulated RFP or Bid Prompt <a href="https://docs.google.com/document/d/1YDpjFDkG7LU-2nt6yfOI1TNqWpaTlRJc9zgDiM-Nsas/edit?usp=sharing" class="no-underline" target="_blank">🔗</a>
""", unsafe_allow_html=True)

bid_prompt = st.text_area(
    "Enter a fake request or bid prompt for the AI to respond to:",
    "We are seeking a vendor to provide cybersecurity training for our staff in Q3 2025..."
)

if "draft" not in st.session_state:
    st.session_state.draft = ""

if st.button("✨ Generate Proposal with GPT-4o"):
    st.session_state.draft = generate_proposal(prompt=bid_prompt)

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
