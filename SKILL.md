---
name: social-context
description: Fetch the real content behind a TikTok, X/Twitter, or Instagram link, the caption text, the image(s), the author, and the canonical URL, and view the image inline. Use whenever the user pastes or mentions a tiktok.com, x.com, twitter.com, or instagram.com post URL and wants its context, image, or text.
---

# Social context

Given a TikTok, X/Twitter or Instagram post URL, pull the text, image(s), author and canonical URL, and actually look at the image.

## Quick start

```bash
uv run --with yt-dlp python "$HOME/.claude/skills/social-context/scripts/fetch_social.py" "<url>" "$HOME/.claude/social-cache"
```

`uv run --with yt-dlp` provisions the Instagram dependency on the fly (cached after the first run). For X/Twitter and TikTok plain `python <script> <url> <out>` also works (stdlib only, no uv needed).

It prints JSON with `platform, text, author, image_urls, video_url, canonical_url, local_images` and downloads the image(s) to the output dir. Then **Read the local image file** to see it.

## Workflow

1. Run the script on the URL, with an output dir (prefer `~/.claude/social-cache`).
2. Read the JSON: surface `text`, `author`, `canonical_url`, and the video URL if any.
3. Read each path in `local_images` with the Read tool to view the image, then describe what is in it together with the caption.

## Platforms

- **X / Twitter** and **TikTok** work out of the box: public endpoints (fxtwitter, tikwm), no key, no login, stdlib only.
- **Instagram** uses `yt-dlp` (free, open source), provisioned via `uv run --with yt-dlp`. Anonymous Instagram is blocked in 2026, so it needs a burner-account cookie: log in to a burner IG, export cookies with a "Get cookies.txt" browser extension, and save them as `ig_cookies.txt` in this skill folder. Burner account only, never your real one.

## Notes

- These are unofficial public services. If one breaks, the script prints `{"error": ...}` and the other platforms keep working.
- Credits: fxtwitter/FxEmbed (X), tikwm.com (TikTok), instaloader (Instagram).
