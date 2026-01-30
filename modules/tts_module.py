from gtts import gTTS

def text_to_speech(text, lang="en", filename="output.mp3"):
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    return filename
