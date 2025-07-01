import streamlit as st

def generate_fake_draft():
    return (
        "Proposal Section 1:\n"
        "- Delivery within 5 days of signing.\n"
        "- Valid for 90 days.\n"
        "- Cost: $15,000 USD."
    )

def explain_section(text):
    return "This clause could pose risk because of tight delivery timelines."

st.title("Proposal Draft Review Loop")

if "draft" not in st.session_state:
    st.session_state.draft = ""

if st.button("Generate Proposal Draft"):
    st.session_state.draft = generate_fake_draft()

if st.session_state.draft:
    edited = st.text_area("Review and Edit Draft:", st.session_state.draft, height=250)

    if st.button("Explain this section"):
        st.info(explain_section(edited))

    if st.button("Flag this claim"):
        st.warning("Flag submitted!")

    if st.button("Submit Review"):
        st.success("Review submitted.")
