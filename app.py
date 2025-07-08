import streamlit as st
from openai import OpenAI
from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import matplotlib.pyplot as plt
import numpy as np
import re
from st_click_detector import click_detector

if "highlight_color" not in st.session_state:
    st.session_state.highlight_color = "#d1f6f4"  # default color

for key in ["draft", "highlights", "edit_log"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "log" in key or "highlights" in key else ""

client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

def generate_proposal(base_prompt, add_honesty=False, add_sources=False, add_confidence=False):
    suffixes = []
    if add_honesty:
        suffixes.append("Please be honest. If no reliable source is available, say that instead of making anything up.")
    if add_sources:
        suffixes.append("Please include the links to the sources you used.")
    if add_confidence:
        suffixes.append("Please provide a score between 1 and 10 to explain how confident you are in your answer.")
    final_prompt = base_prompt + "\n\n" + "\n".join(suffixes) if suffixes else base_prompt

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "You are a professional federal proposal writer tasked with drafting compelling, complete, "
                    "and compliant responses to RFPs from government agencies and institutions. "
                    "Your writing should be clear, factual, concise, and persuasive."
                )},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

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
    story = [Paragraph("<b>Finalized Proposal</b>", styles["Title"]), Spacer(1, 0.3 * inch)]

    clean_text = re.sub(r'<.*?>', '', text)
    for paragraph in clean_text.split('\n'):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), styles["Body"]))
            story.append(Spacer(1, 0.2 * inch))

    doc.build(story)
    buffer.seek(0)
    return buffer

# Sample Bids
MOCK_BIDS = {
    "Law Firm Website Redesign": "We are a mid-sized law firm seeking a qualified vendor to redesign our website to enhance client engagement and optimize mobile responsiveness. The new site must comply with WCAG 2.1 AA accessibility standards and integrate seamlessly with our existing WordPress CMS. Proposals should include project timelines, team qualifications, examples of similar work, and total cost estimates.",
    "City of Riverside Office Supplies": "The City of Riverside invites qualified vendors to submit bids for the supply and delivery of office supplies for various municipal departments. Vendors must provide bulk pricing on items including paper, toner cartridges, pens, folders, and filing systems. Proposals should detail delivery lead times, eco-friendly certifications, and any volume discounts offered.",
    "AI Legal Document Summarization Tool": "We are seeking a technology partner to develop an AI-powered application capable of summarizing lengthy legal documents such as contracts, NDAs, and terms of service into concise bullet-point summaries for internal compliance teams. The tool must support English and Spanish languages with a minimum of 90% summarization accuracy. Please include technical specifications, data training considerations, licensing fees, and maintenance plans.",
    "Fintech Cybersecurity Audit": "Our fintech startup requires a thorough third-party cybersecurity audit to achieve SOC 2 Type II compliance. The audit must encompass penetration testing, AWS cloud infrastructure review, employee access controls, and policy evaluation. Submissions should include audit methodology, team certifications (e.g., CISSP), past client references, and detailed pricing.",
    "HVAC Systems Replacement for Schools": "We are requesting bids for the removal and replacement of HVAC systems across three elementary schools in the district. Scope includes equipment removal, installation of energy-efficient systems, ductwork modifications, and post-install testing. Bidders must be licensed contractors with public school experience.",
    "Custom Bid (Type your own...)": ""
}

st.set_page_config(page_title="SalesPatriot AI Assistant", layout="wide")
tab = st.sidebar.radio("Choose View", ["Proposal Generator", "Proposal Preview", "Metrics & Evaluation"])

def render_highlighted_text(draft, highlights):
    # Clean extra newlines and strip trailing spaces
    clean_draft = re.sub(r'\n{3,}', '\n\n', draft).strip()
    
    # Sort highlights by length to avoid substring conflicts
    highlights_sorted = sorted(highlights, key=lambda h: len(h['text']), reverse=True)

    for h in highlights_sorted:
        safe_text = re.escape(h['text'])
        replacement = f'<span style="background-color: {h["color"]}; padding: 2px 4px; border-radius: 4px;">{h["text"]}</span>'
        clean_draft = re.sub(safe_text, replacement, clean_draft, flags=re.IGNORECASE)

    # Replace newlines with paragraph breaks
    html_output = clean_draft.replace('\n\n', '</p><p>').replace('\n', '<br>')

    return f"""
    <div style="white-space: pre-wrap; line-height: 1.6; font-size: 16px;">
        <p>{html_output}</p>
    </div>
    """


# Session state init
for key in ["draft", "highlights", "edit_log"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "log" in key or "highlights" in key else ""

if tab == "Proposal Generator":
    st.title("🧾 SalesPatriot Proposal Draft Review Loop (HITL Demo)")

    st.markdown("#### Step 1: Select or Enter a Federal Opportunity / RFP")
    bid_choice = st.selectbox("Choose a sample bid:", list(MOCK_BIDS.keys()))
    bid_prompt = st.text_area(
        "Enter your custom bid prompt:" if bid_choice == "Custom Bid (Type your own...)" else "Sample RFP / Bid Prompt:",
        value=MOCK_BIDS[bid_choice],
        height=150,
        disabled=bid_choice != "Custom Bid (Type your own...)",
    )

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
                st.session_state.draft = generate_proposal(
                    bid_prompt,
                    add_honesty=add_honesty,
                    add_sources=add_sources,
                    add_confidence=add_confidence,
                )
                st.session_state.highlights = []
                st.session_state.edit_log = []

    st.markdown("#### Step 3: Review & Edit Proposal Draft")
    st.session_state.draft = st.text_area(
        "🔍 Review and edit proposal draft:",
        value=st.session_state.draft,
        height=400,
        key="proposal_edit_area",
    )

    st.markdown("#### Step 4: Section Analysis & Source-grounding")
    section_to_analyze = st.text_area("Paste a section you'd like to analyze:", height=100, key="section_input")
    col_exp, col_cit, col_sum = st.columns(3)
    with col_exp:
        if st.button("💬 Explain Section") and section_to_analyze.strip():
            st.info(explain_section(section_to_analyze, mode="explain"))
    with col_cit:
        if st.button("📚 Cite Section") and section_to_analyze.strip():
            st.info(explain_section(section_to_analyze, mode="cite"))
    with col_sum:
        if st.button("📝 Summarize Section") and section_to_analyze.strip():
            st.info(explain_section(section_to_analyze, mode="summarize"))

    st.markdown("#### Step 5: Human-in-the-Loop Review")
    colors = ["#d1f6f4", "#c5f2cd", "#f9caca", "#eadbf6", "#fff2c8"]

    selected_color = st.session_state.highlight_color 
    color_squares_html = "".join(
        f"<a href='#' id='{c}' style='"
        f"background-color: {c}; "
        f"width: 40px; height: 40px; display: inline-block; "
        f"border-radius: 8px; margin-right: 8px; cursor: pointer; "
        f"border: 4px solid {'#333' if c == selected_color else '#ccc'}; "
        f"box-sizing: border-box;"
        f"'></a>"
        for c in colors
    )

    clicked = click_detector(
    f"<div style='display:flex; align-items:center; gap:12px;'>{color_squares_html}</div>", 
    key="color_picker_row"
    )

    if clicked and clicked != st.session_state.highlight_color:
        st.session_state.highlight_color = clicked
        st.rerun()  # rerun here is okay since it's a click

    custom_picker = st.color_picker("🎨 Or choose a custom color :", st.session_state.highlight_color, key="custom_color_picker")

    if custom_picker != st.session_state.highlight_color:
        st.session_state.highlight_color = custom_picker

    st.write(f"Selected highlight color: {st.session_state.highlight_color}")

    with st.form("review_form"):
        highlighted_text = st.text_area("Paste or type exact text to highlight:", height=100, key="highlighted_text")
        comment = st.text_area(
            "Write your comment or feedback about the highlighted section:",
            height=100,
            key="comment_text",
        )
        submit = st.form_submit_button("✅ Submit Review & Feedback")

        if submit:
            if highlighted_text.strip() and comment.strip():
                highlight_color = st.session_state.highlight_color
                st.session_state.highlights.append({"text": highlighted_text.strip(), "color": highlight_color})
                st.session_state.edit_log.append({"highlighted": highlighted_text.strip(), "comment": comment.strip()})
                st.session_state.draft += f"\n\n[Reviewer Comment on highlighted text: {comment.strip()}]"
                st.success("Feedback and highlight submitted. Thank you! (Simulated feedback loop)")
                st.rerun()
            else:
                st.warning("Please provide both highlighted text and comment.")

    if st.session_state.edit_log:
        st.markdown("##### 📜 Edit History")
        for i, entry in enumerate(st.session_state.edit_log, 1):
            st.markdown(f"**{i}.** _{entry['highlighted']}_ — 💬 {entry['comment']}")

    st.markdown("#### Step 6: Add Missing Data or Corrections")
    corrections = st.text_area("Enter corrections or missing data to add:", height=150, key="corrections_text")
    if st.button("➕ Add Corrections"):
        if corrections.strip():
            st.session_state.draft += "\n\n" + corrections.strip()
            st.success("Corrections added to the proposal draft.")
        else:
            st.warning("Please enter corrections before adding.")

    st.markdown("#### Step 7: Remove Unwanted Text from Proposal")
    remove_text = st.text_area("Enter exact text to remove from the proposal draft:", height=100, key="remove_text_area")
    if st.button("❌ Remove Text"):
        if remove_text.strip() in st.session_state.draft:
            st.session_state.draft = st.session_state.draft.replace(remove_text.strip(), "")
            st.success("Text removed from the proposal draft.")
        else:
            st.warning("The specified text was not found in the proposal draft.")

    if st.button("✅ Finalize Proposal as PDF"):
        if st.session_state.draft.strip():
            pdf_file = create_pdf(st.session_state.draft)
            st.download_button(
                "Download Final Proposal (.pdf)",
                data=pdf_file,
                file_name="final_proposal.pdf",
                mime="application/pdf",
            )
        else:
            st.warning("Proposal draft is empty.")

    st.markdown("---\n_Prototype by SalesPatriot AI Assistant – July 2025 Demo_")

elif tab == "Proposal Preview":
    st.title("✏️ Proposal Draft Preview with Highlights")

    if st.session_state.draft.strip():
        st.markdown(
            render_highlighted_text(st.session_state.draft, st.session_state.highlights),
            unsafe_allow_html=True
        )
    else:
        st.info("No proposal draft to display. Generate one first.")


elif tab == "Metrics & Evaluation":
    st.title("📊 Model Evaluation Dashboard (Demo Images)")

    st.markdown("### 🧠 Average Hallucination Rate per Method (ChatGPT 3.5 vs. Gemini 2.5)")
    st.image("1.png", use_container_width=True)

    st.markdown("### 📋 Comparison of Evaluation Scores: Gemini vs. ChatGPT 3.5")
    st.image("2.png", use_container_width=True)

    st.markdown("### ⏱️ Comparison of Average Latency and Token Cost: Gemini vs. ChatGPT 3.5")
    st.image("3.png", use_container_width=True)

    st.markdown("---\n_Prototype by SalesPatriot AI Assistant – July 2025 Demo_")

