import os
import hmac
import streamlit as st
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:8080/v1/"),
    api_key=os.getenv("OPENAI_API_KEY", "-"))

st.set_page_config(
    page_title="LLM Platform Chat"
)

def check_password():
    password = os.getenv("PASSWORD")

    if not password:
        return True

    def password_entered():
        if hmac.compare_digest(st.session_state["password"], password):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )

    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")

    return False

if not check_password():
    st.stop()

@st.cache_resource
def get_models():
    return [m for m in sorted(client.models.list(), key=lambda m: m.id)
        if all(x not in m.id for x in ["embed", "tts", "whisper", "dall-e"])]

with st.sidebar:
    st.title("LLM Platform Chat")
    
    st.selectbox("Model", get_models(), key="model", format_func=lambda m: m.id)
    st.text_area("System Prompt", "", key="system")
    st.slider(label="Temperature", key="temperature", min_value=0.0, max_value=2.0, value=1.0, step=.1)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        messages = []

        if st.session_state.system:
            messages.append({"role": "system", "content": st.session_state.system})
        
        for m in st.session_state.messages:
            messages.append({"role": m["role"], "content": m["content"]})

        stream = client.chat.completions.create(
            model=st.session_state.model.id,
            messages=messages,
            temperature=st.session_state.temperature,
            stream=True,
        )

        response = st.write_stream(stream)
    
    st.session_state.messages.append({"role": "assistant", "content": response})