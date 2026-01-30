from modules.translator_module import translate_text, NLLB_LANGS, detect_language
import pdfplumber
from docx import Document

def read_txt(file_path):
    with open(file_path,"r",encoding="utf-8") as f:
        return f.read()

def read_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def read_docx(file_path):
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def file_translate(file_path, file_type, target_lang="en"):
    if file_type=="txt":
        text = read_txt(file_path)
    elif file_type=="pdf":
        text = read_pdf(file_path)
    elif file_type=="docx":
        text = read_docx(file_path)
    else:
        raise ValueError("Format non supporté")
    
    detected_lang, _ = detect_language(text)
    translated = translate_text(text, NLLB_LANGS[detected_lang], NLLB_LANGS[target_lang])
    return {"original_text": text, "translated_text": translated}
