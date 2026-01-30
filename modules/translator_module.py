from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# Détecteur de langue
lang_detector = pipeline(
    "text-classification",
    model="papluca/xlm-roberta-base-language-detection",
    device=-1
)

NLLB_LANGS = {
    "fr": "fra_Latn",
    "en": "eng_Latn",
    "es": "spa_Latn",
    "de": "deu_Latn",
    "ar": "arb_Arab"
}

def detect_language(text):
    result = lang_detector(text[:512])[0]
    return result["label"], round(result["score"],4)

# NLLB modèle
model_nllb_name = "facebook/nllb-200-distilled-600M"
tokenizer_nllb = AutoTokenizer.from_pretrained(model_nllb_name)
model_nllb = AutoModelForSeq2SeqLM.from_pretrained(model_nllb_name)

# Traduction
def translate_text(text, src_lang, tgt_lang, max_length=512):
    tokenizer_nllb.src_lang = src_lang
    inputs = tokenizer_nllb(text, return_tensors="pt", max_length=max_length, truncation=True)
    
    # Attention: certaines versions transformers n'ont pas lang_code_to_id
    forced_bos_token_id = tokenizer_nllb.lang_code_to_id[tgt_lang]  # Si erreur ici, il faut une autre version de transformers
    generated_tokens = model_nllb.generate(
        **inputs,
        forced_bos_token_id=forced_bos_token_id,
        max_length=max_length
    )
    return tokenizer_nllb.batch_decode(generated_tokens, skip_special_tokens=True)[0]
