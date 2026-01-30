import streamlit as st
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Chargement du modèle DialoGPT-medium
@st.cache_resource  # pour cacher le modèle et ne pas le recharger à chaque run
def load_model():
    tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
    model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
    return tokenizer, model

tokenizer, model = load_model()

# Initialisation de l'historique
def init_chat_session():
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

# Fonction qui génère la réponse
def chatbot_response(prompt):
    # Encodage
    input_ids = tokenizer.encode(prompt + tokenizer.eos_token, return_tensors="pt")
    
    # Historique du chat
    chat_history_ids = model.generate(
        input_ids,
        max_length=1000,
        pad_token_id=tokenizer.eos_token_id,
        do_sample=True,
        top_k=50,
        top_p=0.95,
        temperature=0.7
    )
    # Décodage
    response = tokenizer.decode(chat_history_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
    return response

# Interface Streamlit
def chat_interface():
    init_chat_session()

    # Affichage de l'historique
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input utilisateur
    if prompt := st.chat_input("Posez votre question :"):
        # Ajouter la question
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Générer réponse
        answer = chatbot_response(prompt)

        # Ajouter la réponse à l'historique
        st.session_state["chat_history"].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)