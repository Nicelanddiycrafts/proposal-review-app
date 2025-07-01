import streamlit as st
from openai import OpenAI
from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import fonts
from reportlab.lib.styles import ParagraphStyle
from io import BytesIO

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
    with st.spinner("Generating proposal..."):
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

    st.subheader("📝 Highlight & Comment Section")

    highlighted_text = st.text_area(
        "Paste or type the exact text you want to highlight from the proposal:",
        height=100,
    )

    comment = st.text_area(
        "Write your comment or feedback about the highlighted section:",
        height=100,
    )

    if st.button("✅ Submit Review & Feedback"):
        if highlighted_text.strip() and comment.strip():
            st.success("Feedback submitted. Thank you! (Simulated feedback loop)")
        else:
            st.warning("Please provide both highlighted text and comment.")

    st.subheader("Add Missing Data or Corrections")
    corrections = st.text_area("Enter corrections or missing data to add:", height=150)

    if st.button("➕ Add Corrections"):
        if corrections.strip():
            st.session_state.draft += "\n\n" + corrections.strip()
            st.success("Corrections added to the proposal draft.")
        else:
            st.warning("Please enter corrections before adding.")

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
