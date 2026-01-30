import streamlit as st
import os
import json
import tempfile
import numpy as np
from datetime import datetime
from PIL import Image

# --- Imports Modules ---
from modules.translator_module import translate_text, NLLB_LANGS, detect_language
from modules.tts_module import text_to_speech
from modules.file_module import file_translate
from modules.download_module import save_translation

from modules.chatbot_module import chat_interface


# Imports IA
import easyocr
import whisper

# ==========================================
# 1. CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(
    page_title="NeuroTranslate AI", 
    layout="wide", 
    page_icon="🧠",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. STYLE CSS PROFESSIONNEL (Mise à jour)
# ==========================================
st.markdown("""
    <style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    /* Background Global */
    .stApp {
        background-color: #f4f6f9; /* Gris très doux */
        font-family: 'Inter', sans-serif;
    }

    /* --- CORRECTION DES ONGLETS (TAILLE UNIFORME) --- */
    /* Cela cible le contenu à l'intérieur des onglets pour qu'ils fassent tous la même taille */
    div[data-baseweb="tab-panel"] {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 30px;
        min-height: 400px; /* HAUTEUR FIXE POUR TOUS LES ONGLETS */
        display: flex;
        flex-direction: column;
        justify-content: flex-start; /* Aligner le contenu en haut */
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    /* Style des boutons d'onglets (Texte, Doc, Photo...) */
    div[data-baseweb="tab-list"] {
        gap: 8px;
        margin-bottom: -1px; /* Pour coller au panneau */
    }
    
    button[data-baseweb="tab"] {
        background-color: #eef2f6;
        border-radius: 8px 8px 0 0; /* Arrondi seulement en haut */
        border: none;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: white;
        color: #3182ce;
        border-top: 2px solid #3182ce;
        box-shadow: 0 -2px 5px rgba(0,0,0,0.05);
    }

  
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }

    /* Zones de texte (TextArea) */
    .stTextArea textarea {
        background-color: #f8fafc;
        border: 1px solid #cbd5e0;
        border-radius: 8px;
        font-size: 16px;
    }
    .stTextArea textarea:focus {
        border-color: #3182ce;
        background-color: #ffffff;
    }

    /* Boutons d'action */
    .stButton>button {
        background-color: #3182ce;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #2b6cb0;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(49, 130, 206, 0.3);
    }

    /* Uploaders de fichiers plus jolis */
    [data-testid="stFileUploader"] {
        padding: 20px;
        border: 2px dashed #cbd5e0;
        border-radius: 10px;
        text-align: center;
        margin-top: 20px;
    }
    
    /* Card Containers génériques */
    .css-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)


# ==========================================
# 3. FONCTIONS UTILITAIRES
# ==========================================
def image_to_text_easyocr(image, target_lang):
    image_array = np.array(image)
    reader_europe = easyocr.Reader(['fr', 'en', 'es', 'de'], gpu=False)
    reader_arabic = easyocr.Reader(['ar', 'fa', 'ur', 'ug', 'en'], gpu=False)
    reader = reader_arabic if target_lang in ['ar', 'fa', 'ur', 'ug'] else reader_europe
    results = reader.readtext(image_array, detail=0)
    return " ".join(results)

# Initialisation Session State pour garder le texte traduit
if 'input_text' not in st.session_state:
    st.session_state['input_text'] = ""
if 'translated_text' not in st.session_state:
    st.session_state['translated_text'] = ""

# ==========================================
# 4. INTERFACE UTILISATEUR
# ==========================================

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🧠 NeuroTranslate")
    st.markdown("---")
    menu = st.radio("Navigation", ["Traducteur", "Historique", "Assistant IA", "Infos"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("© 2026 AI Solutions")

# --- Page : TRADUCTEUR ---
if menu == "Traducteur":
    
    # En-tête propre
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown("## 👋 Bonjour, que voulez-vous traduire ?")
    
    # --- Barre de Contrôle (Langues) ---
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([2, 0.5, 2, 1])
    with c1:
        st.caption("Langue source")
        st.markdown("**Détection Automatique** 🌐") # Fixe pour simplifier, ou ajouter un selectbox
    with c2:
        st.markdown("<h3 style='text-align: center; color: #cbd5e0;'>➝</h3>", unsafe_allow_html=True)
    with c3:
        st.caption("Langue cible")
        target_lang = st.selectbox("", ["fr", "en", "es", "de", "ar"], index=1, label_visibility="collapsed")
    with c4:
        st.caption("Action")
        translate_btn = st.button("Traduire 🚀")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Zone de Saisie (Onglets Modernes) ---
    tab_txt, tab_doc, tab_img, tab_voc = st.tabs(["📝 Texte", "📄 Document", "📷 Photo", "🎙️ Vocal"])

    # Contenu des onglets
    new_input = ""
    
    with tab_txt:
        # On utilise session_state pour que le texte reste affiché
        text_val = st.text_area("Saisissez votre texte", height=200, placeholder="Tapez ou collez votre texte ici...", label_visibility="collapsed")
        if text_val: new_input = text_val

    with tab_doc:
        uploaded_file = st.file_uploader("Upload PDF/Word/TXT", type=["txt", "pdf", "docx"], label_visibility="collapsed")
        if uploaded_file:
            st.info(f"Fichier chargé : {uploaded_file.name}")
            if translate_btn: # Si on clique sur traduire
                with st.spinner("Lecture du fichier..."):
                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        tmp.write(uploaded_file.read())
                        tmp.write(uploaded_file.read()) # Bug fix, read twice safe
                        path = tmp.name
                    res = file_translate(path, uploaded_file.name.split(".")[-1], "en")
                    new_input = res["original_text"]

    with tab_img:
        up_img = st.file_uploader("Upload Image", type=["png", "jpg"], label_visibility="collapsed")
        if up_img:
            img = Image.open(up_img)
            st.image(img, width=300)
            if translate_btn:
                with st.spinner("OCR en cours..."):
                    new_input = image_to_text_easyocr(img, target_lang)

    with tab_voc:
        up_audio = st.file_uploader("Upload Audio", type=["mp3", "wav"], label_visibility="collapsed")
        if up_audio:
            if translate_btn:
                with st.spinner("Transcription Whisper..."):
                    model = whisper.load_model("base")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                        tmp.write(up_audio.read())
                        path = tmp.name
                    res = model.transcribe(path)
                    new_input = res["text"]

    # --- Logique de Traduction ---
    if translate_btn and (new_input or text_val):
        # Utiliser new_input s'il vient d'un fichier/img, sinon text_val
        final_input = new_input if new_input else text_val
        st.session_state['input_text'] = final_input
        
        with st.spinner("L'IA travaille..."):
            # 1. Detect & Translate
            d_lang, conf = detect_language(final_input)
            t_text = translate_text(final_input, NLLB_LANGS.get(d_lang, 'en'), NLLB_LANGS[target_lang])
            st.session_state['translated_text'] = t_text
            st.session_state['detected_lang'] = d_lang

            # 2. Generate Audio
            text_to_speech(final_input, lang=d_lang, filename="source.mp3")
            text_to_speech(t_text, lang=target_lang, filename="target.mp3")
            
            # 3. Save History
            hist = {
                "original": final_input, "translated": t_text,
                "source_lang": d_lang, "target_lang": target_lang,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            mode = "r+" if os.path.exists("history.json") else "w"
            try:
                with open("history.json", mode, encoding="utf-8") as f:
                    lines = f.readlines() if mode == "r+" else []
                    lines.append(json.dumps(hist) + "\n")
                    if mode == "r+": f.seek(0); f.writelines(lines)
            except: pass

    # --- AFFICHAGE DES RÉSULTATS (Style Split Screen) ---
    if st.session_state['translated_text']:
        st.markdown("---")
        
        col_res1, col_res2 = st.columns(2)
        
        # Bloc Source
        with col_res1:
            st.markdown(f"**Original ({st.session_state.get('detected_lang', 'auto')})**")
            st.text_area("Source", value=st.session_state['input_text'], height=250, disabled=True, label_visibility="collapsed")
            # Audio Player minimaliste
            if os.path.exists("source.mp3"):
                with open("source.mp3", "rb") as f:
                    st.audio(f.read(), format="audio/mp3")

        # Bloc Traduction
        with col_res2:
            st.markdown(f"**Traduction ({target_lang})**")
            st.text_area("Cible", value=st.session_state['translated_text'], height=250, label_visibility="collapsed")
            # Audio Player minimaliste
            if os.path.exists("target.mp3"):
                with open("target.mp3", "rb") as f:
                    st.audio(f.read(), format="audio/mp3")

        # Boutons d'export
        # Boutons d'export
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📥 Télécharger les résultats"):
            
            # On vérifie que les informations nécessaires existent bien dans la session
            if 'input_text' in st.session_state and st.session_state['input_text']:
                
                c1, c2, c3 = st.columns(3)
                
                # Création du dictionnaire d'arguments pour la fonction de sauvegarde
                save_args = {
                    "original_text": st.session_state.get('input_text', ''),
                    "translated_text": st.session_state.get('translated_text', ''),
                    "source_lang": st.session_state.get('detected_lang', 'auto'),
                    "target_lang": target_lang  # Cette variable vient du selectbox en haut de la page
                }

                # On génère les fichiers UNIQUEMENT quand on clique sur le bouton de téléchargement
                # C'est plus efficace que de les générer à chaque rechargement
                
                # --- Bouton TXT ---
                with c1:
                    # On crée le fichier .txt en mémoire
                    save_translation(**save_args, format="txt", filename="t.txt")
                    # On le lit et on le propose au téléchargement
                    with open("t.txt", "rb") as file:
                        st.download_button(
                            label="⬇️ TXT",
                            data=file,
                            file_name="traduction.txt",
                            mime="text/plain"
                        )
                
                # --- Bouton DOCX ---
                with c2:
                    save_translation(**save_args, format="docx", filename="t.docx")
                    with open("t.docx", "rb") as file:
                        st.download_button(
                            label="⬇️ Word",
                            data=file,
                            file_name="traduction.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

                # --- Bouton PDF ---
                with c3:
                    save_translation(**save_args, format="pdf", filename="t.pdf")
                    with open("t.pdf", "rb") as file:
                        st.download_button(
                            label="⬇️ PDF",
                            data=file,
                            file_name="traduction.pdf",
                            mime="application/pdf"
                        )
            else:
                st.caption("Faites une traduction pour pouvoir télécharger les résultats.")



# --- Page : HISTORIQUE ---
elif menu == "Historique":
    st.title("📜 Archives")
    if os.path.exists("history.json"):
        with open("history.json", "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[::-1]:
            d = json.loads(line)
            with st.container():
                st.markdown(f"""
                <div style="background: white; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #3182ce;">
                    <small style="color: grey;">{d['timestamp']} | {d['source_lang']} ➝ {d['target_lang']}</small><br>
                    <b>{d['original'][:60]}...</b>
                </div>
                """, unsafe_allow_html=True)
                with st.expander("Voir détails"):
                    st.write(f"**Traduction :** {d['translated']}")
    else:
        st.info("Historique vide.")

# --- Page : CHATBOT ---
elif menu == "Assistant IA":
    st.title("🤖 Assistant Virtuel")
    if chat_interface:
        chat_interface()
    else:
        st.warning("Module Chatbot non disponible.")

# --- Page : INFOS ---
elif menu == "Infos":

    # ===== HEADER EN COLONNES =====
    col_text, col_img = st.columns([2, 1])

    with col_text:
        st.markdown("""
        <h1 style="color:#2C3E50;">ℹ️ AI Translator Pro</h1>
        <h4 style="color:#16A085;">
        Une application intelligente de traduction multilingue
        </h4>
        <p style="font-size:16px;">
        AI Translator Pro est une application avancée combinant plusieurs 
        technologies d’<b>Intelligence Artificielle</b> pour la traduction,
        la reconnaissance vocale, l’OCR et la synthèse vocale.
        </p>
        """, unsafe_allow_html=True)

    with col_img:
        st.image(
            "https://miro.medium.com/v2/resize:fit:1400/1*c_fiB-YgbnMl6nntYGBMHQ.jpeg",
             width=None
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ===== SECTION TECHNOLOGIES =====
    st.markdown("## 🧠 Technologies utilisées")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="
            background-color:#ECF0F1;
            padding:15px;
            border-radius:10px;
        ">
        <h4>🌍 Traduction</h4>
        <ul>
            <li><b>NLLB / Transformers</b></li>
            <li>Traduction neuronale multilingue</li>
            <li>Détection automatique de langue</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="
            background-color:#ECF0F1;
            padding:15px;
            border-radius:10px;
            margin-top:15px;
        ">
        <h4>📸 OCR</h4>
        <ul>
            <li><b>EasyOCR</b></li>
            <li>Extraction texte depuis images</li>
            <li>Support arabe & langues européennes</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="
            background-color:#E8F8F5;
            padding:15px;
            border-radius:10px;
        ">
        <h4>🎙️ Audio</h4>
        <ul>
            <li><b>Whisper</b> – Speech to Text</li>
            <li><b>gTTS</b> – Text to Speech</li>
            <li>Lecture du texte original & traduit</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="
            background-color:#E8F8F5;
            padding:15px;
            border-radius:10px;
            margin-top:15px;
        ">
        <h4>💻 Interface</h4>
        <ul>
            <li><b>Streamlit</b></li>
            <li>Application multi-pages</li>
            <li>Design moderne & interactif</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ===== FOOTER =====
    st.markdown("""
    <div style="text-align:center;">
        <h4>🎓 Projet académique</h4>
        <p>
        Développé dans le cadre du module 
        <b>Intelligence Artificielle</b><br>
        Traduction • OCR • Audio • Chatbot
        </p>
    </div>
    """, unsafe_allow_html=True)
