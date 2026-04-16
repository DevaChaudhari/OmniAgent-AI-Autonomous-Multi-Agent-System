import streamlit as st
import requests

st.title("🔥 OmniAgent Dashboard")

query = st.text_input("Enter your task")

if st.button("Run Agent"):
    response = requests.post(
        "http://127.0.0.1:8000/run",
        json={"query": query}
    )

    if response.status_code == 200:
        data = response.json()

        # DEBUG
        st.write("Full Response:", data)

        st.subheader("⚡ Final Result")
        st.success(data.get("final", "No result"))

        st.subheader("🛠 Tool Output")
        st.code(data.get("tool", "No tool output"), language="text")

    else:
        st.error("Error connecting to backend")