import streamlit as st

st.set_page_config(
    page_title="Bio Paper Summarizer",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 Bio Paper Summarizer")

st.write(
    """
    Bio Paper Summarizer is a prototype AI tool designed to help users understand
    biomedical research papers more efficiently.
    
    This app summarizes a biomedical abstract into structured sections such as
    background, purpose, methods, results, limitations, and future research ideas.
    """
)

st.divider()

abstract = st.text_area(
    "Paste a biomedical paper abstract here:",
    height=250,
    placeholder="Enter biomedical abstract text..."
)

if st.button("Generate Summary"):
    if abstract.strip() == "":
        st.warning("Please enter a biomedical abstract first.")
    else:
        st.subheader("Structured Summary")

        st.markdown("### 1. One-sentence Summary")
        st.write("This section will provide a concise one-sentence summary of the paper.")

        st.markdown("### 2. Research Background")
        st.write("This section will explain the scientific background of the study.")

        st.markdown("### 3. Research Purpose")
        st.write("This section will describe the main objective of the research.")

        st.markdown("### 4. Experimental Methods")
        st.write("This section will summarize the major methods used in the study.")

        st.markdown("### 5. Key Results")
        st.write("This section will summarize the key findings of the paper.")

        st.markdown("### 6. Limitations")
        st.write("This section will identify possible limitations of the study.")

        st.markdown("### 7. Future Research Ideas")
        st.write("This section will suggest possible future research directions.")

        st.markdown("### 8. Beginner-friendly Explanation")
        st.write("This section will explain the paper in a beginner-friendly way.")

st.divider()

st.caption(
    "Current status: Prototype UI. Generative AI API integration will be added in the next step."
)
