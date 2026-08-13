---
name: meme-scene-explorer
description: >
  This skill should be used when the user asks to explore a meme,
  run Meme Scene Explorer, restage a meme as a cinematic 15-second
  video, make a frozen-subject camera-only film from a still, or
  generate a Seedance meme restage. Requires a local meme image
  and the Higgsfield CLI.
license: MIT
compatibility: >
  Any coding agent that can read a still and run a shell command.
  Requires Higgsfield CLI (`higgsfield`) logged in, Python 3.9+
  (`python3` on macOS/Linux, `python` on Windows), and a local meme
  image. Do not call host-specific image/video generators.
metadata:
  version: "1.1.0"
  openclaw:
    requires:
      bins: ["higgsfield"]
---

# Meme Scene Explorer

Turn one meme still into a 15-second cinematic restage. The still is evidence, not a style hint. The subject stays frozen. Only the camera moves.

Why that rule: video models drift, and a face given room to animate is quietly rebuilt more generically every second. Freezing the subject removes the thing that drifts and spends all 15 seconds on camera movement, which cannot alter identity. `omni_reference` does the other half — it tells Seedance the still is evidence of *who this is*, not a first frame to animate away from.

Method from [Alex Patrascu (@maxescu)](https://x.com/maxescu/status/2087592524940452149), run on Higgsfield Seedance 2.5.

This skill is runtime-neutral. Use the bundled script. Do not call the host agent's image or video tools.

**Frames are not bit-identical across runs.** The pipeline, flags, and prompt contract are.

## Bootstrap

1. If `higgsfield` is missing from PATH: ask the user to run `npm install -g @higgsfield/cli` (macOS, Linux, Windows), then `higgsfield auth login`.
2. If `higgsfield account status` fails: ask the user to run `higgsfield auth login` and wait.
3. Stop if there is no local meme still. Do not invent a subject.
4. A 15s 720p run costs ~97.5 credits. `explore.py` prices it and refuses to submit if the balance is short — relay that message rather than retrying.

## Hard rules

- Run `scripts/explore.py`. That is the only supported generate path.
- Use `seedance_2_5` + `--mode omni_reference` + the original still as the only image reference.
- Do not redraw the subject with any stills or video model (Grok Imagine, image_gen, image_edit, Nano Banana, Flux, Midjourney, ffmpeg Ken Burns, frame interpolation).
- Do not pass the JPEG as `--start-image` (that shows the upload).
- Do not send a generic camera list. Write 15 beats from *this* still.
- Do not show the original JPEG, UI, captions, watermarks, or compression.

## Workflow

1. **Read the still** with the host's file/image viewer. Write a short extract: appearance, clothes/markings, exact pose, expression, composition, meaning.
2. **Choose one real place** that heightens that meaning. One world for all 15 seconds.
3. **Write 15 subject-specific stages** to a temp `.txt` file. Stage 1 = ECU of the defining detail. Stages 2–14 = real details on this subject, then the world. Stage 15 = snap back to the original meme framing. Follow `references/prompt-contract.md`. Use `examples/filled-prompt.puppy.txt` as the shape, not the content.
4. **Run the bundled script** (cwd = this skill directory, or pass absolute paths). Use `python3` on macOS/Linux, `python` on Windows:

```bash
python3 scripts/explore.py /absolute/path/to/meme.jpg --prompt-file /absolute/path/to/filled.txt --out ~/Videos
```

   One 15s 720p run costs about **97.5 Higgsfield credits**. Say so before spending the user's balance.

5. **Deliver** the printed URL and the saved `.mp4` path. Open the file only if the user asks.

If `explore.py` cannot run, stop. Do not substitute another generator.

## Common mistakes

| Excuse | Reality |
|---|---|
| "I'll restage the face first for quality" | That replaces the subject. Identity lock is the product. |
| "The host video tool is close enough" | Only Seedance 2.5 `omni_reference` is this method. |
| "Generic orbit / dolly / crane is fine" | Name this still's details. |
| "start_image will preserve identity better" | It also preserves the JPEG, UI, and artifacts. Forbidden. |

## Additional resources

- `references/prompt-contract.md` — locked flags + skeleton
- `examples/filled-prompt.puppy.txt` — one worked 15-stage prompt
- `scripts/explore.py` — the generate runner
- `scripts/install.py` — copy/link this skill into every local agent
- `tests/` — `python3 -m unittest discover -s tests`
