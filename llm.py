import json, time, requests
from .config import GEMINI_KEYS

BASE = "https://generativelanguage.googleapis.com/v1beta"

def clean(e, k):
    return str(e).replace(k, "***")

def get_working_models(k):
    try:
        r = requests.get(f"{BASE}/models?key={k}", timeout=20)
        r.raise_for_status()
        names = [
            m["name"].replace("models/", "")
            for m in r.json().get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
            and "gemini" in m["name"]
            and "embedding" not in m["name"]
            and "vision" not in m["name"]
        ]
        # ترتيب النماذج الأسرع أولاً
        flash = [n for n in names if "flash" in n]
        others = [n for n in names if "flash" not in n]
        return (flash + others) or ["gemini-2.5-flash"]
    except Exception:
        return ["gemini-2.5-flash", "gemini-2.5-pro"]

def gemini_json(prompt):
    last = None
    for k in GEMINI_KEYS:
        models = get_working_models(k)
        for m in models[:4]:
            try:
                r = requests.post(
                    f"{BASE}/models/{m}:generateContent?key={k}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "responseMimeType": "application/json",
                            "temperature": 0.85
                        }
                    },
                    timeout=60)
                if r.status_code == 404:
                    continue
                r.raise_for_status()
                txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(txt)
            except Exception as e:
                last = f"[{m}] {clean(e, k)}"
    raise RuntimeError("gemini text failed: %s" % last)

PROMPTS = {
"ar": """أنت كاتب محتوى علمي لريلز. اكتب سكربت ريل (35 إلى 40 ثانية) عن موضوع علمي عام مدهش، بلهجة سعودية بيضاء بسيطة وقريبة من الناس (مو فصحى ثقيلة).
- الموضوع جديد وما يشبه هذي المواضيع السابقة: {avoid}
- 5 مشاهد بالضبط. الأول هوك يشد الانتباه، والأخير خاتمة ودعوة للمتابعة.
- كل narration من 12 إلى 20 كلمة. كل caption من 2 إلى 5 كلمات (عنوان كبير على الشاشة).
- المعلومات العلمية لازم تكون صحيحة 100% وما فيها مبالغة.
أرجع JSON فقط بهذا الشكل:
{{"topic":"اسم الموضوع","title":"عنوان قصير","scenes":[{{"narration":"...","caption":"..."}}],"description":"وصف المنشور جملتين","hashtags":["#علوم","..."]}}""",
"en": """You write scripts for viral science reels. Write a 35-40 second script about a surprising general-science topic, in simple energetic spoken English.
- The topic must be new and not similar to these previous ones: {avoid}
- Exactly 5 scenes. Scene 1 is a strong hook, the last scene is a closer with a call to follow.
- Each narration is 12 to 20 words. Each caption is 2 to 5 words (big on-screen headline).
- Facts must be 100% accurate, no exaggeration.
Return JSON only:
{{"topic":"topic name","title":"short title","scenes":[{{"narration":"...","caption":"..."}}],"description":"2-sentence post description","hashtags":["#science","..."]}}""",
}

def make_script(lang, avoid):
    av = "، ".join(avoid[-30:]) if avoid else "none"
    for _ in range(3):
        s = gemini_json(PROMPTS[lang].format(avoid=av))
        sc = s.get("scenes", [])
        if 4 <= len(sc) <= 6 and all(x.get("narration") and x.get("caption") for x in sc) and s.get("title"):
            s["scenes"] = sc[:6]
            s.setdefault("hashtags", [])
            s.setdefault("description", s["title"])
            s.setdefault("topic", s["title"])
            return s
    raise RuntimeError("script invalid after 3 tries")
