from __future__ import annotations

from uuid import uuid4

import streamlit as st

from app.graph import graph

st.set_page_config(page_title="Healthcare Policy RAG", layout="wide")
st.title("Healthcare Policy RAG — Correct, Verify, Escalate")
st.caption("Synthetic demonstration only. Not a coverage or claim determination system.")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid4())

examples = [
    "What billing code and preferred product apply to bendamustine?",
    "What documentation is required for an advanced imaging scan?",
    "What is required for continued CGM coverage?",
    "My member ID is AB-12345. What is the policy for an unknown treatment?",
]
query = st.selectbox("Example", examples)
query = st.text_area("Question", query)

if st.button("Run graph", type="primary"):
    with st.spinner("Running retrieval and verification graph..."):
        result = graph.invoke(
            {"query": query, "trace": []},
            config={"configurable": {"thread_id": st.session_state.thread_id}},
        )
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Answer")
        st.write(result["answer"])
        st.subheader("Citations")
        st.dataframe(result.get("citations", []), use_container_width=True)
    with right:
        st.metric("Verified", "Yes" if result.get("verified") else "No")
        st.metric("Evidence coverage", f"{result.get('verification_coverage', 0):.0%}")
        st.metric("Corrections", result.get("correction_count", 0))
        if result.get("needs_human_review"):
            st.error("Human review required")
    st.subheader("LangGraph execution trace")
    st.dataframe(result.get("trace", []), use_container_width=True)
