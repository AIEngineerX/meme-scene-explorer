# Meme Scene Explorer

Turn one meme still into a 15-second cinematic restage.

The still is the only evidence. The subject stays frozen. Only the camera moves.

This package makes **[Alex Patrascu’s (@maxescu) method](https://x.com/maxescu/status/2087592524940452149)** repeatable on [Higgsfield](https://higgsfield.ai) **Seedance 2.5**.

It is **agent-agnostic**. Humans run a Python script. Any coding agent that can read `SKILL.md` / `AGENTS.md` and execute a shell command can run the same path. No Grok, Claude, or Codex APIs are required.

It does **not** make Seedance output the same pixels twice. There is no seed. What is locked: model, flags, prompt contract, and the rule that the original still is never redrawn by a stills model.

## What you need

1. A Higgsfield account with credits (Seedance 2.5 is a paid generate)
2. The [Higgsfield CLI](https://github.com/higgsfield-ai/cli)
3. One meme image (jpg / png / webp)
4. Python 3.9+ (stdlib only)

```bash
curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh
higgsfield auth login
higgsfield account status
```

## Quick start (no agent)

```bash
git clone https://github.com/AIEngineerX/meme-scene-explorer.git
cd meme-scene-explorer

python scripts/explore.py path/to/meme.jpg --out ~/Videos
```

Better — fill 15 stages from the still, then:

```bash
python scripts/explore.py path/to/meme.jpg \
  --prompt-file examples/filled-prompt.puppy.txt \
  --out ~/Videos
```

`examples/filled-prompt.puppy.txt` is a worked example. Use it as the *shape*, not as the prompt for a different meme.

### Flags

| Flag | Default | Meaning |
|---|---|---|
| `--prompt-file` | skeleton | Your filled 15-stage prompt |
| `--world` | auto | Setting injected into the skeleton |
| `--out` | `.` | Where to save the mp4 |
| `--aspect` | `21:9` | Closest Higgsfield value to Alexa 2.39:1 |
| `--resolution` | `720p` | `480p` or `720p` |
| `--no-download` | off | Print the URL only |

## Install for any coding agent

From the repo:

```bash
python scripts/install.py
```

That links this folder into every skills directory that already exists on the machine:

| Path | Typical host |
|---|---|
| `~/.agents/skills/` | Cross-runtime (Claude, Codex, Gemini, Copilot) |
| `~/.claude/skills/` | Claude Code |
| `~/.codex/skills/` | Codex CLI |
| `~/.cursor/skills/` | Cursor |
| `~/.gemini/skills/` | Gemini CLI |
| `~/.grok/skills/` | Grok |
| `~/.github/skills/` | Copilot CLI |
| `~/.config/opencode/skills/` | OpenCode |
| `~/.windsurf/skills/` | Windsurf |

To vendor it into a project so any agent opened on that repo sees it:

```bash
python scripts/install.py --project /path/to/your/app
```

That writes `.agents/skills/meme-scene-explorer`. Opening the folder is enough — `AGENTS.md` at the repo root tells the agent what to do.

Then: attach a still and say **explore this meme**.

## How it works

1. The meme still is passed as the only image reference (`omni_reference`).
2. The prompt restages that **same** subject in one real place.
3. 15 one-second stages: ECU of the defining detail → subject details → world → snap back to the original framing.
4. Diegetic sound only. No music. No original JPEG, captions, or UI.

Locked generate (also what `scripts/explore.py` runs):

```text
higgsfield generate create seedance_2_5
  --mode omni_reference
  --image-references <meme.jpg>
  --duration 15
  --aspect_ratio 21:9
  --resolution 720p
  --generate_audio true
```

Full contract: [`references/prompt-contract.md`](references/prompt-contract.md).

## Agent contract

If you are an agent, read [`AGENTS.md`](AGENTS.md) and [`SKILL.md`](SKILL.md).

- Generate only via `python scripts/explore.py`
- Do not call the host image/video tools
- Stop if there is no still or Higgsfield is not logged in

## Why the first naive version fails

Regenerating the face with an image model, then Ken-burning 15 stills, produces a prettier *different* character. That is not this method. If Higgsfield is down, stop. Do not fake the film.

## Credit

- Method: [Alex Patrascu (@maxescu) — Meme Scene Explorer](https://x.com/maxescu/status/2087592524940452149)
- Runtime: Higgsfield Seedance 2.5

## License

MIT. See [LICENSE](LICENSE).
