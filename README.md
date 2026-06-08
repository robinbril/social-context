# social-context

Pull the real content behind a TikTok, X/Twitter, or Instagram link: the caption text, the image(s), the author, and the canonical URL, and view the image inline. Free and open source, no API keys.

Built as a skill for Claude Code and Codex, but the script runs standalone too.

## Platforms

| Platform | Source | Login needed |
|---|---|---|
| X / Twitter | fxtwitter / FxEmbed | No |
| TikTok | tikwm.com | No |
| Instagram | yt-dlp | Yes, a burner-account cookie (anonymous IG is blocked in 2026) |

## Usage

```bash
# X / Twitter and TikTok: stdlib only, no install
python scripts/fetch_social.py "<url>" ./out

# Instagram: needs yt-dlp, provisioned on the fly with uv
uv run --with yt-dlp python scripts/fetch_social.py "<url>" ./out
```

It prints JSON with `platform, text, author, image_urls, video_url, canonical_url, local_images` and downloads the image(s) into the output dir. Open the files in `local_images` to see the image.

## Install as a Claude Code / Codex skill

```bash
git clone https://github.com/robinbril/social-context.git
mkdir -p ~/.claude/skills/social-context
cp -r social-context/SKILL.md social-context/scripts ~/.claude/skills/social-context/
```

Then it triggers automatically when you paste a tiktok.com, x.com, twitter.com, or instagram.com link.

## Instagram

Anonymous Instagram no longer works (verified against instaloader, yt-dlp, and gallery-dl: all hit a login wall). To enable it, give yt-dlp a burner-account cookie:

1. Log in to a **burner** Instagram account in your browser (never your real one).
2. Export cookies with a free "Get cookies.txt" browser extension on instagram.com.
3. Save the file as `ig_cookies.txt` in the project root (next to `SKILL.md`).

That file is gitignored and must never be committed. X and TikTok need none of this.

## Credits

fxtwitter / [FxEmbed](https://github.com/FxEmbed/FxEmbed) for X, [tikwm.com](https://www.tikwm.com) for TikTok, [yt-dlp](https://github.com/yt-dlp/yt-dlp) for Instagram. These are unofficial public services; if one changes, the script returns a clean error and the others keep working.

## License

MIT. See [LICENSE](LICENSE).
