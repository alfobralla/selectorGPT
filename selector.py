from openai import OpenAI
import openai
import os
import time
import streamlit as st

import streamlit as st
from openai import OpenAI

st.title("SELECTOR GPT (Assistant API con Streaming)")

client = OpenAI(organization="org-ioUF8oxXusHuVpI1h6sThy6h")
ASSISTANT_ID = "asst_jZIEzyCNpy0JpGII6h57gSls"

# --- Inicialización de sesión ---
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Mostrar historial ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Entrada del usuario ---
if prompt := st.chat_input("¿Qué quieres gestionar en tu tablero?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Añadir el mensaje al hilo
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt,
    )

    # --- Ejecutar el asistente con streaming ---
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        with client.beta.threads.runs.stream(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID,
        ) as stream:
            for event in stream:
                # Algunos eventos no tienen type
                if not hasattr(event, "type"):
                    continue

                # Mostrar texto parcial en tiempo real
                if event.type == "thread.message.delta":
                    if hasattr(event, "delta") and hasattr(event.delta, "content"):
                        for block in event.delta.content:
                            if (
                                hasattr(block, "text")
                                and hasattr(block.text, "value")
                            ):
                                full_response += block.text.value
                                placeholder.markdown(full_response)

            # Esperamos a que termine
            stream.until_done()

        # ✅ Recuperar la respuesta final completa del asistente
        messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        last_msg = None
        for m in messages.data:
            if m.role == "assistant":
                if len(m.content) > 0 and hasattr(m.content[0], "text"):
                    last_msg = m.content[0].text.value
                    break

        if last_msg:
            full_response = last_msg
            placeholder.markdown(full_response)
        else:
            placeholder.markdown("_(El asistente no devolvió texto)_")

        st.session_state.messages.append({"role": "assistant", "content": full_response})
