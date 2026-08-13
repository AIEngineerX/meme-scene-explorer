# Meme Scene Explorer

Instructions for any coding agent (Claude Code, Codex, Cursor, Gemini CLI, Grok, Copilot, Windsurf, or a generic shell agent).

This repo is a skill + a CLI. The generate path is `python scripts/explore.py`. Do not use the host agent's image or video tools.

## When this applies

The user attached or named a meme still and wants a cinematic 15-second restage, "Meme Scene Explorer", or a frozen-subject camera-only film.

## Do this

1. Read `SKILL.md` and `references/prompt-contract.md`.
2. Look at the meme still. Extract identity, pose, expression, and meaning.
3. Write a filled 15-stage prompt (shape: `examples/filled-prompt.puppy.txt`).
4. Run:

```bash
python scripts/explore.py /path/to/meme.jpg --prompt-file /path/to/filled.txt --out ~/Videos
```

5. Return the URL and the local `.mp4` path.

## Do not

- Redraw the subject in another model
- Animate the original JPEG as `--start-image`
- Ken Burns / ffmpeg a stills slideshow
- Invent a meme if no still was given

## Install the skill for this agent

```bash
python scripts/install.py
```

That links the folder into every skills directory present on the machine (`~/.agents/skills`, `~/.claude/skills`, `~/.codex/skills`, `~/.cursor/skills`, `~/.gemini/skills`, `~/.grok/skills`, …).
