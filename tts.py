import base64, subprocess, time, wave, requests
from .config import GEMINI_KEYS, GEMINI_VOICE, ELEVEN_KEY, ELEVEN_VOICE, EN_VOICE
from .llm import clean

RATE = 24000

def write_wav(pcm, path):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(pcm)

def gemini_tts(text, path):
    prompt = ("Read this naturally in a warm, energetic Saudi white dialect (Khaleeji), "
              "like a friendly science presenter: " + text)
    err = "no keys"
    for k in GEMINI_KEYS:
        for voice in (GEMINI_VOICE, "Charon"):
            try:
                r = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key=" + k,
                    json={"contents": [{"parts": [{"text": prompt}]}],
                          "generationConfig": {"responseModalities": ["AUDIO"],
                                               "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}},
                    timeout=120)
                if r.status_code == 429:
                    err = "429 on key"; time.sleep(5); break      # next key
                if r.status_code == 400:
                    err = "400 voice %s" % voice; continue          # next voice
                r.raise_for_status()
                b64 = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                write_wav(base64.b64decode(b64), path)
                return
            except Exception as e:
                err = clean(e, k)
    raise RuntimeError("gemini tts failed: " + err)

def eleven_tts(text, path):
    if not ELEVEN_KEY:
        raise RuntimeError("no elevenlabs key")
    r = requests.post(
        "https://api.elevenlabs.io/v1/text-to-speech/%s?output_format=pcm_24000" % ELEVEN_VOICE,
        headers={"xi-api-key": ELEVEN_KEY},
        json={"text": text, "model_id": "eleven_v3"}, timeout=120)
    r.raise_for_status()
    write_wav(r.content, path)

def edge_tts(text, path):
    mp3 = path + ".mp3"
    subprocess.run(["edge-tts", "--voice", EN_VOICE, "--text", text, "--write-media", mp3],
                   check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-i", mp3, "-ar", str(RATE), "-ac", "1", path],
                   check=True, capture_output=True)

def synth(lang, text, path):
    if lang == "en":
        edge_tts(text, path); return "edge-tts"
    try:
        gemini_tts(text, path); return "gemini"
    except Exception as e:
        print("gemini failed, trying elevenlabs:", e)
        eleven_tts(text, path); return "elevenlabs"
