import os, shutil, subprocess, time, glob, requests

def _git(d, *a, check=True):
    return subprocess.run(["git", "-c", "user.name=harranco-bot", "-c", "user.email=bot@users.noreply.github.com",
                           "-C", d, *a], check=check, capture_output=True, text=True)

def publish_video(path):
    """Push the mp4 to an orphan 'media' branch (keeps only newest 4) and return a public URL."""
    repo, tok = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"]
    remote = "https://x-access-token:%s@github.com/%s.git" % (tok, repo)
    d = "/tmp/media_wt"
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    _git(d, "init", "-b", "fresh")
    _git(d, "remote", "add", "origin", remote)
    if _git(d, "fetch", "--depth", "1", "origin", "media", check=False).returncode == 0:
        _git(d, "checkout", "FETCH_HEAD", "--", ".")
    name = os.path.basename(path)
    shutil.copy(path, os.path.join(d, name))
    files = sorted(glob.glob(d + "/*.mp4"))
    for old in files[:-4]:
        os.remove(old)
    _git(d, "add", "-A")
    _git(d, "commit", "-m", "media " + name)
    _git(d, "push", "-f", "origin", "fresh:media")
    base = os.getenv("MEDIA_BASE", "https://raw.githubusercontent.com/%s/media" % repo)
    url = "%s/%s" % (base, name)
    for _ in range(18):
        try:
            if requests.head(url, allow_redirects=True, timeout=20).status_code == 200:
                return url
        except Exception:
            pass
        time.sleep(10)
    raise RuntimeError("video URL never became reachable: " + url)
