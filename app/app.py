import os
import re
import requests
import streamlit as st

from openai import OpenAI
from urllib.parse import urljoin

title=os.getenv("TITLE", "LLM Platform Chat")

st.set_page_config(
    page_icon=":robot_face:",
    page_title=title,
    layout="centered",
    initial_sidebar_state="collapsed"
)

client_url = os.getenv("OPENAI_BASE_URL", "http://localhost:8080/v1/")
client_token = os.getenv("OPENAI_API_KEY", "-")

client = OpenAI(base_url=client_url, api_key=client_token)

@st.cache_resource
def get_models():
    models = [m for m in sorted(client.models.list(), key=lambda m: m.id)
        if all(x not in m.id for x in ["embed", "tts", "whisper", "dall-e", "flux"])]
    
    model_filter = os.environ.get('MODELS')
    
    if model_filter:
        models = [m for m in models if m.id in model_filter.split(',')]
    
    default_model = os.environ.get('MODEL')
    
    if default_model:
        list = [m.id for m in models]
        
        if default_model in list:
            index = list.index(default_model)
            models.insert(0, models.pop(index))
    
    return models

def reset_chat():
    st.session_state.messages = []

def extract_text(file):
    headers = {
        'Authorization': "Bearer " + client_token,
    }

    data = {
        'chunking_strategy': 'by_title',
        'max_characters': '2000',
        'overlap': '0'
    }

    files = {
        'files': (file.name, file.getvalue())
    }
    
    response = requests.post(urljoin(client_url, "partition"), headers=headers, data=data, files=files)

    result = response.json()
    texts = [item['text'] for item in result]

    return texts

def process_files():
    if "segments" not in st.session_state:
        st.session_state.segments = {}
    
    current_files = [file.name for file in st.session_state.files] if st.session_state.files else []
    
    for file in list(st.session_state.segments.keys()):
        if file not in current_files:
            del st.session_state.segments[file]

    for file in st.session_state.files:
        if file.name not in st.session_state.segments:
            segments = extract_text(file)
            st.session_state.segments[file.name] = segments

with st.sidebar:
    st.title(title)
    
    st.selectbox("Model", get_models(), key="model", placeholder="Select model", format_func=lambda m: m.id, index=0)
    st.text_area("System Prompt", "", key="system")
    
    st.file_uploader("Upload files", key="files", type=("txt", "md", "pdf", "docx", "pptx"), accept_multiple_files=True, on_change=process_files)

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
    if prompt.startswith("/"):
        match prompt:
            case "/reset":
                reset_chat()
    
        st.rerun()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        system = []
        messages = []

        if st.session_state.system:
            system.append(st.session_state.system)
        
        if "segments" in st.session_state:
            content = "Use these uploaded documents if helpful:"

            for segments in st.session_state.segments.values():
                for segment in segments:
                    content += "\n" + segment
            
            system.append(content)
        
        if system:
            messages.append({"role": "system", "content": "\n\n".join(system)})
        
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
    st.html("""
            <div style="display: flex; justify-content: center; align-items: center; height: 50vh">
                <img src="/app/static/logo.png" style="max-height: 100%; width: auto;">
            </div>
            """)