import streamlit as st
from openai import OpenAI
from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import matplotlib.pyplot as plt
import numpy as np

client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

# === Proposal Generation with Optional Prompt Add-ons ===
def generate_proposal(base_prompt, add_honesty=False, add_sources=False, add_confidence=False):
    suffixes = []
    if add_honesty:
        suffixes.append(
            "Please be honest. If no reliable source is available, say that instead of making anything up."
        )
    if add_sources:
        suffixes.append(
            "Please include the links to the sources you used."
        )
    if add_confidence:
        suffixes.append(
            "Please provide a score between 1 and 10 to explain how confident you are in your answer."
        )
    final_prompt = base_prompt + "\n\n" + "\n".join(suffixes) if suffixes else base_prompt

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

# === Explain / Cite / Summarize Section ===
def explain_section(text, mode="explain"):
    mode_prompts = {
        "explain": "Please explain the following section in simpler terms:",
        "cite": "Please provide source citations for this section:",
        "summarize": "Please provide a concise summary of this section:"
    }
    prompt_text = mode_prompts.get(mode, "Please explain the following section:") + "\n\n" + text
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

# === PDF Creation ===
def create_pdf(text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
        title="Final Proposal",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Body", fontSize=12, leading=18))
    story = []

    story.append(Paragraph("<b>Finalized Proposal</b>", styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))

    for paragraph in text.split('\n'):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), styles["Body"]))
            story.append(Spacer(1, 0.2 * inch))

    doc.build(story)
    buffer.seek(0)
    return buffer

# === Mock SAM.gov Bids for Data Ingestion ===
MOCK_BIDS = {
    "Cybersecurity Training Q3 2025": "We are seeking a vendor to provide cybersecurity training for our staff in Q3 2025, including phishing simulation and incident response exercises.",
    "Office Cleaning Services FY 2026": "The agency requires office cleaning services for the fiscal year 2026 across three federal buildings.",
    "Cloud Migration Services": "Looking for qualified vendors to assist with cloud migration of legacy systems by the end of 2025.",
    "Custom Bid (Type your own...)": ""
}

st.set_page_config(page_title="SalesPatriot AI Assistant", layout="wide")
st.title("🧾 SalesPatriot Proposal Draft Review Loop (HITL Demo)")

# === Sidebar for navigation ===
tab = st.sidebar.radio("Choose View", ["Proposal Generator", "Metrics & Evaluation"])

if tab == "Proposal Generator":
    st.markdown("#### Step 1: Select or Enter a Federal Opportunity / RFP")

    bid_choice = st.selectbox("Choose a sample SAM.gov bid:", list(MOCK_BIDS.keys()))
    if bid_choice == "Custom Bid (Type your own...)":
        bid_prompt = st.text_area("Enter your custom fake request or bid prompt:", height=150)
    else:
        bid_prompt = MOCK_BIDS[bid_choice]
        st.text_area("Sample RFP / Bid Prompt:", bid_prompt, height=150, disabled=True)

    st.markdown("#### Step 2: Select AI Generation Options (Hallucination Mitigation)")

    col1, col2, col3 = st.columns(3)
    add_honesty = col1.checkbox("Honesty Response", value=True)
    add_sources = col2.checkbox("Source Request")
    add_confidence = col3.checkbox("Confidence Score")

    if st.button("✨ Generate Proposal with GPT-4o"):
        if not bid_prompt.strip():
            st.warning("Please enter or select a valid bid prompt.")
        else:
            with st.spinner("Generating proposal..."):
                proposal = generate_proposal(
                    bid_prompt,
                    add_honesty=add_honesty,
                    add_sources=add_sources,
                    add_confidence=add_confidence,
                )
                st.session_state.draft = proposal

    if "draft" in st.session_state and st.session_state.draft:
        st.markdown("#### Step 3: Review & Edit Proposal Draft")
        edited_text = st.text_area(
            "🔍 Review and edit proposal draft:",
            value=st.session_state.draft,
            height=300,
            key="proposal_edit_area"
        )

        # Buttons to Explain / Cite / Summarize selected section
        st.markdown("#### Step 4: Section Analysis & Source-grounding")

        section_to_analyze = st.text_area("Paste a section you'd like to analyze:", height=100, key="section_input")

        col_exp, col_cit, col_sum = st.columns(3)
        with col_exp:
            if st.button("💬 Explain Section"):
                if section_to_analyze.strip():
                    explanation = explain_section(section_to_analyze, mode="explain")
                    st.info(explanation)
                else:
                    st.warning("Please enter a section to explain.")
        with col_cit:
            if st.button("📚 Cite Section"):
                if section_to_analyze.strip():
                    citations = explain_section(section_to_analyze, mode="cite")
                    st.info(citations)
                else:
                    st.warning("Please enter a section to cite.")
        with col_sum:
            if st.button("📝 Summarize Section"):
                if section_to_analyze.strip():
                    summary = explain_section(section_to_analyze, mode="summarize")
                    st.info(summary)
                else:
                    st.warning("Please enter a section to summarize.")

        # Human-in-the-loop review
        st.markdown("#### Step 5: Human-in-the-Loop Review")

        highlighted_text = st.text_area(
            "Paste or type exact text to highlight:",
            height=100,
            key="highlighted_text"
        )
        comment = st.text_area(
            "Write your comment or feedback about the highlighted section:",
            height=100,
            key="comment_text"
        )
        if st.button("✅ Submit Review & Feedback"):
            if highlighted_text.strip() and comment.strip():
                if "edit_log" not in st.session_state:
                    st.session_state.edit_log = []
                st.session_state.edit_log.append({
                    "highlighted": highlighted_text,
                    "comment": comment
                })
                st.success("Feedback submitted. Thank you! (Simulated feedback loop)")
                # Clear input areas after submission
                st.session_state.highlighted_text = ""
                st.session_state.comment_text = ""
            else:
                st.warning("Please provide both highlighted text and comment.")

        # Show edit history
        if "edit_log" in st.session_state and st.session_state.edit_log:
            st.markdown("##### 📜 Edit History")
            for i, entry in enumerate(st.session_state.edit_log, 1):
                st.markdown(f"**{i}.** _{entry['highlighted']}_ — 💬 {entry['comment']}")

        # Add corrections or missing data
        st.markdown("#### Step 6: Add Missing Data or Corrections")
        corrections = st.text_area("Enter corrections or missing data to add:", height=150, key="corrections_text")
        if st.button("➕ Add Corrections"):
            if corrections.strip():
                # Append corrections to draft
                st.session_state.draft += "\n\n" + corrections.strip()
                st.success("Corrections added to the proposal draft.")
                # Clear corrections text box
                st.session_state.corrections_text = ""
            else:
                st.warning("Please enter corrections before adding.")

        # Finalize and export PDF
        if st.button("✅ Finalize Proposal as PDF"):
            if st.session_state.draft.strip():
                pdf_file = create_pdf(st.session_state.draft)
                st.download_button(
                    label="Download Final Proposal (.pdf)",
                    data=pdf_file,
                    file_name="final_proposal.pdf",
                    mime="application/pdf",
                )
            else:
                st.warning("Proposal draft is empty.")

    # Footer
    st.markdown("---\n_Prototype by SalesPatriot AI Assistant – July 2025 Demo_")

elif tab == "Metrics & Evaluation":
    st.title("📊 Model Evaluation Dashboard (Demo Data)")

    st.markdown("### Hallucination Rates by Prompting Method")
    methods = ["Original", "Honesty", "Source Request", "Confidence Score"]
    rates = [3.2, 0.8, 0.4, 0.6]  # Placeholder values

    x = np.arange(len(methods))
    fig, ax = plt.subplots()
    ax.bar(x, rates, color=["#AEC6CF", "#FFDAB9", "#B0E0E6", "#F4C2C2"])
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.set_ylabel("Hallucination Rate (%)")
    ax.set_title("Hallucination Rate by Prompting Method")
    st.pyplot(fig)

    st.markdown("### Average ChatGPT Evaluation Scores")
    criteria = [
        "Relevance",
        "Completeness",
        "Factual Accuracy",
        "Terminology Use",
        "Clarity & Conciseness",
        "Contextual Understanding"
    ]
    avg_scores = [4.2, 4.5, 4.6, 4.3, 4.4, 4.1]  # Placeholder values

    x = np.arange(len(criteria))
    fig2, ax2 = plt.subplots()
    ax2.bar(x, avg_scores, color=["#AEC6CF", "#FFDAB9", "#B0E0E6", "#F4C2C2", "#D8BFD8", "#E0FFFF"])
    ax2.set_xticks(x)
    ax2.set_xticklabels(criteria, rotation=30, ha="right")
    ax2.set_ylim(0, 5)
    ax2.set_ylabel("Average Score (1–5)")
    ax2.set_title("Average ChatGPT Evaluation Scores (Gemini Responses)")
    st.pyplot(fig2)

    st.markdown("---\n_Prototype by SalesPatriot AI Assistant – July 2025 Demo_")
