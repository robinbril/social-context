#!/usr/bin/env python3
"""Fetch public post context from X/Twitter, TikTok, or Instagram.

Usage:
    fetch_social.py <url> [output_dir]

Prints JSON to stdout: platform, text, author, image_urls, video_url,
canonical_url, local_images. Downloads the primary image(s) into output_dir.

X and TikTok use public endpoints (fxtwitter, tikwm) and need no extra deps.
Instagram uses yt-dlp (free, open source) with a burner cookies.txt; anonymous
Instagram is blocked in 2026, so a burner login cookie is required.
"""
import sys
import os
import re
import json
import hashlib
import urllib.request
import urllib.parse

UA = "Mozilla/5.0 (social-context/1.0)"


def _get(url, data=None, timeout=25):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _get_json(url, data=None, timeout=25):
    return json.loads(_get(url, data=data, timeout=timeout).decode("utf-8", "replace"))


def fetch_twitter(url):
    m = re.search(r"(?:twitter\.com|x\.com)/([^/?#]+)/status/(\d+)", url)
    if m:
        user, sid = m.group(1), m.group(2)
    else:
        m2 = re.search(r"status/(\d+)", url)
        if not m2:
            raise ValueError("no status id in url")
        user, sid = "i", m2.group(1)
    d = _get_json("https://api.fxtwitter.com/%s/status/%s" % (user, sid))
    t = d.get("tweet") or d.get("status") or {}
    if not t:
        raise ValueError("fxtwitter: %s" % d.get("message", "no tweet"))
    media = t.get("media") or {}
    photos = [p.get("url") for p in (media.get("photos") or []) if p.get("url")]
    videos = [v.get("url") for v in (media.get("videos") or []) if v.get("url")]
    auth = t.get("author") or {}
    return {
        "platform": "twitter",
        "text": t.get("text", ""),
        "author": auth.get("screen_name", ""),
        "image_urls": photos,
        "video_url": videos[0] if videos else None,
        "canonical_url": t.get("url", url),
    }


def fetch_tiktok(url):
    body = urllib.parse.urlencode({"url": url, "hd": "1"}).encode()
    d = _get_json("https://www.tikwm.com/api/", data=body)
    data = d.get("data") or {}
    if not data:
        raise ValueError("tikwm: %s" % d.get("msg", "no data"))
    images = [u for u in (data.get("images") or []) if u]
    cover = data.get("cover")
    author = (data.get("author") or {}).get("unique_id", "")
    vid = data.get("id", "")
    canonical = url
    if author and vid:
        canonical = "https://www.tiktok.com/@%s/video/%s" % (author, vid)
    return {
        "platform": "tiktok",
        "text": data.get("title", ""),
        "author": author,
        "image_urls": images if images else ([cover] if cover else []),
        "video_url": data.get("hdplay") or data.get("play"),
        "canonical_url": canonical,
    }


def fetch_instagram(url):
    import subprocess
    m = re.search(r"instagram\.com/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)", url)
    if not m:
        raise ValueError("no shortcode in url")
    sc = m.group(1)
    clean = "https://www.instagram.com/p/%s/" % sc
    here = os.path.dirname(os.path.abspath(__file__))
    cookies = os.path.normpath(os.path.join(here, "..", "ig_cookies.txt"))
    cmd = [sys.executable, "-m", "yt_dlp", "--dump-single-json", "--no-warnings"]
    if os.path.exists(cookies):
        cmd += ["--cookies", cookies]
    cmd.append(clean)
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=90)
    except FileNotFoundError:
        raise RuntimeError(
            "yt-dlp not available; run via: uv run --with yt-dlp python <script>"
        )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip()
        low = err.lower()
        if any(k in low for k in ("cookies", "registered users", "login", "rate-limit")):
            raise RuntimeError(
                "Instagram needs a login. Drop a burner-account cookies.txt at %s "
                "(log in to a burner IG, export cookies with a 'Get cookies.txt' "
                "browser extension). Then it works, free and open source via yt-dlp. "
                "Use a burner account only, never your real one." % cookies
            )
        raise RuntimeError("yt-dlp failed: %s" % err[-300:])
    info = json.loads(proc.stdout.decode("utf-8", "replace"))
    entries = info.get("entries") or [info]
    imgs, vids = [], []
    for e in entries:
        is_video = bool(e.get("duration")) or (e.get("vcodec") not in (None, "none"))
        if is_video:
            if e.get("url"):
                vids.append(e["url"])
            if e.get("thumbnail"):
                imgs.append(e["thumbnail"])
        else:
            u = e.get("url") or e.get("display_url") or e.get("thumbnail")
            if u:
                imgs.append(u)
    return {
        "platform": "instagram",
        "text": info.get("description") or "",
        "author": info.get("uploader") or info.get("uploader_id") or "",
        "image_urls": [u for u in imgs if u],
        "video_url": vids[0] if vids else None,
        "canonical_url": info.get("webpage_url") or clean,
    }


def fetch(url):
    u = url.lower()
    if "tiktok.com" in u:
        return fetch_tiktok(url)
    if "instagram.com" in u:
        return fetch_instagram(url)
    if "x.com" in u or "twitter.com" in u:
        return fetch_twitter(url)
    raise ValueError("supported hosts: x.com, twitter.com, tiktok.com, instagram.com")


def download(urls, outdir):
    paths = []
    if not urls:
        return paths
    os.makedirs(outdir, exist_ok=True)
    for u in urls[:6]:
        try:
            data = _get(u, timeout=45)
            ext = (u.split("?")[0].rsplit(".", 1)[-1] or "jpg")[:5]
            name = hashlib.md5(u.encode()).hexdigest()[:10] + "." + ext
            path = os.path.join(outdir, name)
            with open(path, "wb") as f:
                f.write(data)
            paths.append(path)
        except Exception as e:  # noqa: BLE001 - report, do not crash the whole fetch
            paths.append("(download failed: %s)" % e)
    return paths


def main():
    if len(sys.argv) < 2:
        print("usage: fetch_social.py <url> [output_dir]", file=sys.stderr)
        sys.exit(2)
    url = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."
    try:
        post = fetch(url)
    except Exception as e:  # noqa: BLE001 - surface a clean error as JSON
        print(json.dumps({"error": str(e), "url": url}, ensure_ascii=False))
        sys.exit(1)
    post["local_images"] = download(post.get("image_urls") or [], outdir)
    print(json.dumps(post, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
