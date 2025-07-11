import streamlit as st
import requests
import json
import time

# streamlit run interface.py
# D:\venvs\venv1\Scripts\streamlit.exe run interface.py


# === CONFIG ===
API_KEY = "tpsg-tMLXhjGxa2E18Pw6vCRINcgtD3PblTI"
BOT_ID = "a50a21f2-a191-4f4a-bd17-bcfee112a847"
BASE_URL = "https://api.metisai.ir/api/v1/chat"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


# === API UTILITIES ===
def get_sessions():
    res = requests.get(f"{BASE_URL}/session?botId={BOT_ID}", headers=HEADERS)
    return res.json() if res.ok else []

def load_session_messages(session_id):
    res = requests.get(f"{BASE_URL}/session/{session_id}", headers=HEADERS)
    if res.ok:
        return sorted(res.json().get("messages", []), key=lambda m: m["timestamp"])
    return []

def create_new_session(first_message):
    payload = {
        "botId": BOT_ID,
        "user": None,
        "initialMessages": [{"type": "USER", "content": first_message}]
    }
    res = requests.post(f"{BASE_URL}/session", headers=HEADERS, json=payload)
    if res.ok:
        session_data = res.json()
        return session_data["id"], session_data.get("messages", [])
    else:
        st.error("❌ Could not start new session.")
        return None, []

def send_message(session_id, user_input):
    url = f"{BASE_URL}/session/{session_id}/message"
    payload = {
        "message": {
            "content": user_input,
            "type": "USER"
        }
    }
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.ok:
        return res.json()
    else:
        st.error("❌ Failed to send message.")
        return None

# === SESSION STATE INIT ===
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = get_sessions()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "new_chat_requested" not in st.session_state:
    st.session_state.new_chat_requested = False

# === SIDEBAR ===
st.sidebar.title("💬 Chat History")

# Start new chat button
if st.sidebar.button("➕ New Chat"):
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.new_chat_requested = True

# Track which session is being confirmed for deletion
if "delete_confirm_id" not in st.session_state:
    st.session_state.delete_confirm_id = None

# List chat sessions
for session in st.session_state.all_sessions:
    session_id = session["id"]
    session_label = session.get("title") or f"🗂 {session_id[:8]}"
    col1, col2 = st.sidebar.columns([4, 1])

    # Select session
    if col1.button(session_label, key=f"session-{session_id}"):
        st.session_state.session_id = session_id
        st.session_state.messages = load_session_messages(session_id)
        st.session_state.new_chat_requested = False
        st.rerun()

    # Delete button
    if col2.button("🗑", key=f"del-{session_id}"):
        st.session_state.delete_confirm_id = session_id

    # Show confirmation
    if st.session_state.delete_confirm_id == session_id:
        with st.sidebar.expander(f"❓ Delete chat {session_id[:8]}?", expanded=True):
            st.write("Are you sure you want to delete this chat?")
            confirm_col1, confirm_col2 = st.columns([1, 1])
            if confirm_col1.button("✅ Yes", key=f"yes-{session_id}"):
                delete_url = f"{BASE_URL}/session/{session_id}"
                requests.delete(delete_url, headers=HEADERS)

                # Reset if deleted current session
                if st.session_state.session_id == session_id:
                    st.session_state.session_id = None
                    st.session_state.messages = []

                # Refresh session list
                st.session_state.all_sessions = get_sessions()
                st.session_state.delete_confirm_id = None
                st.rerun()

            if confirm_col2.button("❌ No", key=f"no-{session_id}"):
                st.session_state.delete_confirm_id = None


# === MAIN UI ===
st.title("🤖 Metis Chat UI")

if st.session_state.session_id:
    st.caption(f"🧾 Session ID: `{st.session_state.session_id}`")

# === Show chat history ===
for msg in st.session_state.messages:
    role = "user" if msg["type"] == "USER" else "assistant"
    with st.chat_message(role):
        st.markdown(msg["content"])

# === Chat Input ===
user_input = st.chat_input("Type your message...")

if user_input:
    # Show user message immediately
    st.session_state.messages.append({"type": "USER", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # If new chat, create it
    if not st.session_state.session_id:
        sid, msgs = create_new_session(user_input)
        if sid:
            st.session_state.session_id = sid
            st.session_state.messages = sorted(msgs, key=lambda m: m["timestamp"])
            st.rerun()
    else:
        # Send user message and get AI reply
        ai_response = send_message(st.session_state.session_id, user_input)
        if ai_response:
            ai_msg = {
                "type": ai_response["type"],
                "content": ai_response["content"]
            }
        st.session_state.messages.append(ai_msg)
        with st.chat_message("assistant"):
            st.markdown(ai_msg["content"])

