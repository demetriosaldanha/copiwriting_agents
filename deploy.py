import json
import os
from uuid import uuid4

import requests
import streamlit as st

AGENT_ID = "copywriter"
AGENT_OS_URL = os.getenv("AGENT_OS_URL", "http://127.0.0.1:7777").rstrip("/")
RUNS_ENDPOINT = f"{AGENT_OS_URL}/agents/{AGENT_ID}/runs"
SESSIONS_ENDPOINT = f"{AGENT_OS_URL}/sessions"
# 2 - Conexão com o Agno (SERVER) =========================================


def conversation_title(text: str, max_length: int = 54) -> str:
    """Cria um título curto, sem partir palavras, a partir da primeira mensagem."""
    title = " ".join(text.split())
    if len(title) <= max_length:
        return title

    shortened = title[: max_length + 1].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{shortened}…"


def get_response_stream(message: str, session_id: str, user_id: str):
    response = requests.post(
        url=RUNS_ENDPOINT,
        data={
            "message": message,
            "stream": "true",
            "session_id": session_id,
            "user_id": user_id,
        },
        stream=True,
        timeout=180,
    )
    response.raise_for_status()
    
    # 2.1 - Streaming (processamento) ====================================
    for line in response.iter_lines():
        if line:
            # Parse Server-Sent Events
            if line.startswith(b'data: '):
                data = line[6:] # Remove 'data: ' prefix
                try:
                    event = json.loads(data)
                    yield event
                except json.JSONDecodeError:
                    continue


def get_sessions(user_id: str) -> list[dict]:
    response = requests.get(
        SESSIONS_ENDPOINT,
        params={
            "type": "agent",
            "component_id": AGENT_ID,
            "user_id": user_id,
            "limit": 50,
            "sort_by": "updated_at",
            "sort_order": "desc",
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json().get("data", [])


def get_session_messages(session_id: str, user_id: str) -> list[dict]:
    response = requests.get(
        f"{SESSIONS_ENDPOINT}/{session_id}",
        params={"user_id": user_id},
        timeout=15,
    )
    response.raise_for_status()

    messages = []
    for message in response.json().get("chat_history", []):
        role = message.get("role")
        content = message.get("content")
        if role in {"user", "assistant"} and isinstance(content, str):
            messages.append({"role": role, "content": content})
    return messages


def rename_session(session_id: str, user_id: str, title: str) -> None:
    response = requests.post(
        f"{SESSIONS_ENDPOINT}/{session_id}/rename",
        params={"user_id": user_id},
        json={"session_name": title},
        timeout=15,
    )
    response.raise_for_status()


def start_new_conversation() -> None:
    st.session_state.agent_session_id = str(uuid4())
    st.session_state.messages = []
    st.session_state.loaded_session_id = st.session_state.agent_session_id
    st.query_params["session_id"] = st.session_state.agent_session_id


# 3 - Streamlit ==========================================================

st.set_page_config(page_title="Copy Master")
st.title("Copy Master")

# 3.1 - Histórico ==========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_id" not in st.session_state:
    st.session_state.user_id = st.query_params.get("user_id", str(uuid4()))
    st.query_params["user_id"] = st.session_state.user_id

if "agent_session_id" not in st.session_state:
    st.session_state.agent_session_id = st.query_params.get("session_id", str(uuid4()))
    st.query_params["session_id"] = st.session_state.agent_session_id

if st.session_state.get("loaded_session_id") != st.session_state.agent_session_id:
    try:
        st.session_state.messages = get_session_messages(
            st.session_state.agent_session_id,
            st.session_state.user_id,
        )
    except requests.HTTPError as error:
        if error.response.status_code != 404:
            st.error("Não foi possível carregar esta conversa.")
        st.session_state.messages = []
    except requests.RequestException:
        st.error("Não foi possível conectar ao AgentOS.")
        st.session_state.messages = []
    st.session_state.loaded_session_id = st.session_state.agent_session_id

with st.sidebar:
    st.header("Conversas")
    if st.button("+ Nova conversa", use_container_width=True):
        start_new_conversation()
        st.rerun()

    try:
        sessions = get_sessions(st.session_state.user_id)
    except requests.RequestException:
        sessions = []
        st.warning("A lista de conversas ficará disponível quando o AgentOS estiver acessível.")

    for session in sessions:
        session_id = session["session_id"]
        label = conversation_title(session.get("session_name") or "Conversa sem título")
        if st.button(label, key=f"session-{session_id}", use_container_width=True):
            st.session_state.agent_session_id = session_id
            st.session_state.loaded_session_id = None
            st.query_params["session_id"] = session_id
            st.rerun()

# 3.2 - Mostrar histórico ==================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("process"):
            with st.expander(label="Process", expanded=False):
                st.json(msg["process"])
        st.markdown(msg["content"])

# 3.3 - Input do usuário ==================================================
if prompt := st.chat_input("Digite sua mensagem..."):
    is_first_message = not st.session_state.messages

    # Adicionar mensagem do usuário (memoria do streamlit)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
    
    # processamento streaming
    try:
        for event in get_response_stream(
            prompt,
            st.session_state.agent_session_id,
            st.session_state.user_id,
        ):
            event_type = event.get("event", "")

            # Tool call iniciado
            if event_type == "ToolCallStarted":
                tool_name = event.get("tool", {}).get("tool_name")
                with st.status(f"Executando {tool_name}...", expanded=True):
                    st.json(event.get("tool", {}).get("tool_args", {}))

            # Conteúdo da resposta
            elif event_type == "RunContent":
                content = event.get("content", "")
                if content:
                    full_response += content
                    response_placeholder.markdown(full_response + "▌")
    except requests.RequestException as error:
        st.error(f"Não foi possível consultar o agente: {error}")
    
    response_placeholder.markdown(full_response)

    if is_first_message:
        try:
            rename_session(
                st.session_state.agent_session_id,
                st.session_state.user_id,
                conversation_title(prompt),
            )
        except requests.RequestException:
            # O agente já respondeu; uma falha ao renomear não deve interromper o chat.
            pass

    # salvar a resposta e histórico na session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
    })
