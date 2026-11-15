import os, zoneinfo

TZ = zoneinfo.ZoneInfo("Asia/Riyadh")

ORG = os.getenv("BUFFER_ORG", "6af9551aa5ae4080b6149177")
CHANNELS = {
    "instagram": "6af955a5ece6dfde5fce5e18",
    "tiktok": "6af95636ece6dfde5fce611b",
    "youtube": "6af955faece6dfde5fce5fd5",
}
BUFFER_TOKEN = os.getenv("BUFFER_TOKEN", "")

GEMINI_KEYS = [k for k in (os.getenv("GEMINI_KEY_1"), os.getenv("GEMINI_KEY_2")) if k]
GEMINI_VOICE = os.getenv("GEMINI_VOICE", "Ludo")
ELEVEN_KEY = os.getenv("ELEVENLABS_KEY", "")
ELEVEN_VOICE = "yXEnnEln9armDCyhkXcA"
EN_VOICE = os.getenv("EN_VOICE", "en-US-AndrewNeural")

# post time (Asia/Riyadh)
POST_AT = {"ar": (13, 0), "en": (21, 0)}
