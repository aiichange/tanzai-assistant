import streamlit as st
import requests
import os
API_URL_CHAT = os.getenv("API_URL_CHAT", "http://127.0.0.1:8000/chat")


st.set_page_config(page_title="AI Platform Playground", layout="wide")

# ---------------- Session State ----------------
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "system_message" not in st.session_state:
    st.session_state["system_message"] = "You are a helpful assistant."
if "initialized" not in st.session_state:
    st.session_state["initialized"] = False  # Track if prompt has been run once

# ---------------- Sidebar ----------------
st.sidebar.header("⚙️ Options")
uploaded_file = st.sidebar.file_uploader("📎 Upload File (any type)", type=None)
web_query = st.sidebar.text_input("🌐 Web Search Query")
use_web = st.sidebar.checkbox("Enable Web Search", value=False)

if st.sidebar.button("🧹 Clear Session"):
    st.session_state["messages"] = []
    st.session_state["initialized"] = False
    st.rerun()

# ---------------- Layout ----------------
col1, col2 = st.columns([1, 2])

# ----- Left Column (Prompt Builder) -----
with col1:
    st.subheader("📝 Prompt Builder")

    st.markdown("**System Message**")
    system_input = st.text_area(
        "System",
        value=st.session_state["system_message"],
        height=120,
        label_visibility="collapsed"
    )

    st.markdown("**User Message**")
    user_input = st.text_area(
        "User",
        placeholder="Enter your first task or question...",
        height=100,
        label_visibility="collapsed"
    )

    # Run button to initialize context
    if st.button("▶️ Run Prompt"):
        st.session_state["system_message"] = system_input
        st.session_state["messages"] = []

        if user_input.strip():
            st.session_state["messages"].append(("user", user_input.strip()))

        payload = {
            "messages": [{"role": "system", "content": st.session_state["system_message"]}]
                        + [{"role": r, "content": c} for r, c in st.session_state["messages"]],
            "use_rag": uploaded_file is not None,
            "use_web": use_web,
        }
        if use_web and web_query:
            payload["messages"].append({"role": "user", "content": web_query})

        try:
            response = requests.post(API_URL_CHAT, json=payload)
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "⚠️ No response")
                backend = data.get("backend", "unknown")

                st.session_state["messages"].append(("assistant", answer))
                st.session_state["initialized"] = True
                st.success(f"Prompt run complete (Backend: {backend.upper()})")
            else:
                st.error(f"❌ Prompt failed: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ----- Right Column (Conversation Panel) -----
with col2:
    st.subheader("💬 Conversation")

    for role, content in st.session_state["messages"]:
        with st.chat_message(role):
            st.markdown(content)

    # Only allow chat if prompt has been initialized
    if st.session_state["initialized"]:
        if prompt := st.chat_input("Type your next message..."):
            st.session_state["messages"].append(("user", prompt))

            payload = {
                "messages": [{"role": "system", "content": st.session_state["system_message"]}]
                            + [{"role": r, "content": c} for r, c in st.session_state["messages"]],
                "use_rag": uploaded_file is not None,
                "use_web": use_web,
            }

            try:
                response = requests.post(API_URL_CHAT, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "⚠️ No response")
                    backend = data.get("backend", "unknown")

                    st.session_state["messages"].append(("assistant", answer))
                    with st.chat_message("assistant"):
                        st.markdown(answer)
                        st.caption(f"🤖 Backend: {backend.upper()}")
                else:
                    st.error(f"❌ Chat failed: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    else:
        st.info("⚠️ Please run the initial prompt first using ▶️ Run Prompt.")
