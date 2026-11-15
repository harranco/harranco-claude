import sys, json, os, re, pathlib, datetime as dt
from .config import TZ
from . import llm, tts, render, publish, buffer

STATE = pathlib.Path("state/topics.json")

def load():
    return json.loads(STATE.read_text("utf-8")) if STATE.exists() else []

def save(s):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1), "utf-8")

def main():
    lang = sys.argv[1]
    dry, force = "--dry" in sys.argv, "--force" in sys.argv
    today = dt.datetime.now(TZ).strftime("%Y-%m-%d")
    st = load()
    if not force and any(x["date"] == today and x["lang"] == lang for x in st):
        print("تم إنتاج فيديو اليوم مسبقاً لهذي اللغة، تخطي."); return

    avoid = [x["topic"] for x in st if x["lang"] == lang][-40:]
    if not dry and os.getenv("BUFFER_TOKEN"):
        try:
            avoid += buffer.history_texts()[:15]
        except Exception as e:
            print("buffer history skipped:", str(e)[:120])

    script = llm.make_script(lang, avoid)
    wd = pathlib.Path("work") / lang
    wd.mkdir(parents=True, exist_ok=True)
    wavs, engine = [], ""
    for i, sc in enumerate(script["scenes"]):
        p = str(wd / ("s%d.wav" % i))
        engine = tts.synth(lang, sc["narration"], p)
        wavs.append(p)

    slug = re.sub(r"[^a-z0-9]+", "-", script["topic"].lower())[:20].strip("-") or "reel"
    name = "%s-%s-%s.mp4" % (today.replace("-", ""), lang, slug if slug.isascii() else "reel")
    out = str(wd / name)
    secs = render.render(lang, script["title"], script["scenes"], wavs, out, str(wd / "audio.wav"))
    print("rendered %.1fs voice=%s -> %s" % (secs, engine, out))
    if dry:
        return

    url = publish.publish_video(out)
    due, res = buffer.schedule_all(lang, script, url)
    for k, v in res.items():
        print(k, v)
    if not any(v.startswith("ok") for v in res.values()):
        raise SystemExit("كل القنوات فشلت، الحالة ما انحفظت عشان يعاد التشغيل.")
    st.append({"date": today, "lang": lang, "topic": script["topic"], "title": script["title"],
               "video": url, "due": due.isoformat(), "results": res})
    save(st)
    print("تم: %s | النشر %s | %s" % (script["title"], due.strftime("%H:%M"),
          "، ".join("%s %s" % (k, "✓" if v.startswith("ok") else "✗") for k, v in res.items())))

if __name__ == "__main__":
    main()
