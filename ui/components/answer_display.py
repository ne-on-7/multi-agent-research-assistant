import streamlit as st


def render_answer(answer: str, sources: list[dict]):
    st.divider()
    st.subheader("Final Answer")
    st.markdown(answer)

    if sources:
        st.subheader("Sources")
        for i, source in enumerate(sources, 1):
            title = source.get("title", "Unknown")
            url = source.get("url", "")
            page = source.get("page")

            if url:
                st.markdown(f"**[{i}]** [{title}]({url})")
            elif page:
                st.markdown(f"**[{i}]** {title} — Page {page}")
            else:
                st.markdown(f"**[{i}]** {title}")

            snippet = source.get("snippet", "")
            if snippet:
                st.caption(snippet[:150] + "..." if len(snippet) > 150 else snippet)
