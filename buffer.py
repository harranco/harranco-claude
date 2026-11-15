import json, datetime as dt, requests
from .config import ORG, CHANNELS, BUFFER_TOKEN, TZ, POST_AT

API = "https://api.buffer.com"

def gql(query, variables=None):
    r = requests.post(API, json={"query": query, "variables": variables or {}},
                      headers={"Authorization": "Bearer " + BUFFER_TOKEN}, timeout=60)
    r.raise_for_status()
    j = r.json()
    if j.get("errors"):
        raise RuntimeError(json.dumps(j["errors"], ensure_ascii=False)[:800])
    return j["data"]

def history_texts():
    q = ('query{ posts(first:100, input:{organizationId:"%s", filter:{status:[sent,scheduled,sending,error]}}){ '
         'edges{ node{ dueAt status channelService text } } } }') % ORG
    d = gql(q)
    return [(e["node"]["text"] or "").replace("\n", " ")[:80] for e in d["posts"]["edges"]]

MUT = """mutation($input: CreatePostInput!){ createPost(input:$input){
  ... on PostActionSuccess { post { id status dueAt } }
  ... on MutationError { message } } }"""

def due_time(lang):
    now = dt.datetime.now(TZ)
    h, m = POST_AT[lang]
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    floor = now + dt.timedelta(minutes=4)
    return max(target, floor)

def schedule_all(lang, script, video_url):
    tags = " ".join(script["hashtags"][:8])
    text = (script["description"] + "\n\n" + tags).strip()
    title = script["title"]
    due = due_time(lang)
    metas = {
        "instagram": {"type": "reel", "shouldShareToFeed": True},
        "tiktok": {"title": title[:90]},
        "youtube": {"title": (title[:88] + " #Shorts"), "categoryId": "27"},
    }
    results = {}
    for svc, ch in CHANNELS.items():
        inp = {"channelId": ch, "text": text, "schedulingType": "automatic", "mode": "customScheduled",
               "dueAt": due.isoformat(timespec="seconds"),
               "assets": {"videos": [{"url": video_url}]}, "metadata": {svc: metas[svc]}}
        try:
            res = gql(MUT, {"input": inp})["createPost"]
            if res.get("message"):
                raise RuntimeError(res["message"])
            results[svc] = "ok " + str(res.get("post", {}).get("id"))
        except Exception as e:
            results[svc] = "FAIL " + str(e)[:300]
    return due, results
