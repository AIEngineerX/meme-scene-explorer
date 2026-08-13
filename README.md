# Meme Scene Explorer

Turn one meme still into a 15-second cinematic film.

The still is the only evidence. The subject stays frozen. Only the camera moves.

This repo packages [Alex Patrascu (@maxescu)'s method](https://x.com/maxescu/status/2087592524940452149) for [Higgsfield](https://higgsfield.ai) **Seedance 2.5**. Humans run a Python script. Any coding agent that can read a file and run a shell command can run the same script. No vendor-specific APIs.

Seedance has no seed. The same image and prompt will not produce identical pixels. What this repo locks is the **method**: model, flags, prompt shape, and the rule that the original still is never redrawn by another image model.

## Requirements

- A [Higgsfield](https://higgsfield.ai) account with credits (Seedance 2.5 is paid)
- The [Higgsfield CLI](https://github.com/higgsfield-ai/cli)
- Python 3.9+ (standard library only)
- One meme image (`.jpg`, `.png`, or `.webp`)

```bash
curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh
higgsfield auth login
```

## Run

```bash
git clone https://github.com/AIEngineerX/meme-scene-explorer.git
cd meme-scene-explorer

python scripts/explore.py path/to/meme.jpg --out ~/Videos
```

That sends a generic 15-stage skeleton. Seedance reads the still and fills the beats.

For a better film, write stages from the actual details in the still (see `examples/filled-prompt.puppy.txt` for the shape), then:

```bash
python scripts/explore.py path/to/meme.jpg \
  --prompt-file path/to/your-stages.txt \
  --out ~/Videos
```

| Flag | Default | Meaning |
|---|---|---|
| `--prompt-file` | `examples/skeleton.txt` | Your filled 15-stage prompt |
| `--world` | a matching real place | Setting used by the skeleton |
| `--out` | current directory | Where the `.mp4` is saved |
| `--aspect` | `21:9` | Closest Higgsfield value to Alexa 2.39:1 |
| `--resolution` | `720p` | `480p` or `720p` |
| `--no-download` | off | Print the result URL only |

## Use with a coding agent

```bash
python scripts/install.py
```

That links this folder into every skills directory already on the machine (`~/.agents/skills`, `~/.claude/skills`, `~/.codex/skills`, `~/.cursor/skills`, `~/.gemini/skills`, `~/.grok/skills`, and others if present).

To vendor it into another project:

```bash
python scripts/install.py --project /path/to/your/app
```

Then attach a still and say **explore this meme**. Agents should follow `AGENTS.md` and generate only through `scripts/explore.py`.

## How it works

1. The meme still is the only image reference (`omni_reference`).
2. The prompt restages that same subject in one real place.
3. Fifteen one-second stages: close-up of the defining detail → the subject → the world → snap back to the original framing.
4. Diegetic sound only. No music. No original JPEG, captions, or UI.

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

## What's in this repo

```text
AGENTS.md                         instructions for any coding agent
SKILL.md                          skill entry (name + when to load)
LICENSE                           MIT
scripts/explore.py                generate a video
scripts/install.py                install the skill for local agents
references/prompt-contract.md     locked flags and prompt rules
examples/skeleton.txt             default prompt (used when you pass no --prompt-file)
examples/filled-prompt.puppy.txt  one worked 15-stage prompt (shape only)
agents/openai.yaml                Codex discovery stub
```

## What not to do

- Do not redraw the subject in another image or video model, then animate those stills.
- Do not pass the original JPEG as `--start-image`. That keeps the upload, captions, and compression.
- Do not send a generic list of camera moves. Name details that exist on *this* still.
- If Higgsfield is unavailable, stop. Do not fake the film.

## Credit

Method: [Alex Patrascu (@maxescu)](https://x.com/maxescu/status/2087592524940452149). Runtime: Higgsfield Seedance 2.5.

## License

MIT. See [LICENSE](LICENSE).
