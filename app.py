import os
import re
import streamlit as st

from openai import OpenAI

title=os.getenv("TITLE", "LLM Platform Chat")

st.set_page_config(
    page_icon=":robot_face:",
    page_title=title,
    layout="centered",
    initial_sidebar_state="collapsed"
)

client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:8080/v1/"),
    api_key=os.getenv("OPENAI_API_KEY", "-"))

@st.cache_resource
def get_models():
    models = [m for m in sorted(client.models.list(), key=lambda m: m.id)
        if all(x not in m.id for x in ["embed", "tts", "whisper", "dall-e", "flux"])]
    
    default = os.environ.get('MODEL')
    
    if default:
        list = [m.id for m in models]
        
        if default in list:
            index = list.index(default)
            models.insert(0, models.pop(index))
    
    return models

def reset_chat():
    st.session_state.messages = []

with st.sidebar:
    st.title(title)
    
    st.selectbox("Model", get_models(), key="model", placeholder="Select model", format_func=lambda m: m.id, index=0)
    st.text_area("System Prompt", "", key="system")
    
    st.button('Clear chat history', on_click=reset_chat)

if "messages" not in st.session_state:
    reset_chat()
    
def decorate_message(content):
    for url, format in re.findall(r'\[.*?\]\((https?://[^\s\)]+?\.(wav|mp3|ogg))\)', content):
        st.audio(url, format="audio/" + format, autoplay=True)
    
    for url, format in  re.findall(r'\[.*?\]\((https?://[^\s\)]+?\.(mp4|webm))\)', content):
        st.video(url, format="video/" + format, autoplay=True)

for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    
    with st.chat_message(role):
        st.write(content)
        decorate_message(content)

if prompt := st.chat_input("Message " + title):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        messages = []

        if st.session_state.system:
            messages.append({"role": "system", "content": st.session_state.system})
        
        for m in st.session_state.messages:
            messages.append({"role": m["role"], "content": m["content"]})

        stream = client.chat.completions.create(
            model=st.session_state.model.id,
            messages=messages,
            stream=True,
        )
        
        response = st.write_stream(stream)
        decorate_message(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

if len(st.session_state.messages) == 0:
    col1, col2, col3 = st.columns(3, vertical_alignment="center")
    
    with col2:
        st.image("assets/logo.png")