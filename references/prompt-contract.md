# Prompt contract

Method published by [Alex Patrascu (@maxescu)](https://x.com/maxescu/status/2087592524940452149). This file is the single source of truth for the text sent to Seedance 2.5.

## What is locked

- Model: `seedance_2_5`
- Mode: `omni_reference`
- Media: the meme still as the only `--image-references` item
- Duration: `15`
- Aspect: `21:9` (closest Higgsfield enum to Alexa 2.39:1)
- Resolution: `720p`
- Audio: `--generate_audio true` (diegetic only)

## What is not locked

Seedance has no seed. Same image + same prompt will not render identical pixels. The contract makes the *method* repeatable.

## Rules the prompt must contain

1. `meme_reference` is the attached still. It is the only evidence for identity, pose, expression, clothes/markings, composition, and meaning.
2. Restage those exact elements in one complete physical place that matches the meme's energy. Elevate the world. Do not replace the subject.
3. Do not show the uploaded JPEG, screenshots, borders, captions, watermarks, website UI, typography, or compression artifacts.
4. Technical base: Arri Alexa 65, anamorphic 2.39:1, 35mm Kodak 5219, fine grain, hyper-realistic, no music, diegetic sound only.
5. Subject stays frozen. Only the camera moves.
6. Exactly 15 one-second stages, each continuing from the last.
7. Stage 1 is an extreme close-up of the single most defining detail of the pose or expression.
8. Stages 2–14 are *subject-specific* camera beats (a watch, a dirty paw, a finger on a temple). Not a generic list of "orbit, dolly, crane".
9. Stage 15 snaps back to a centered master that matches the original meme framing.
10. Close with a short diegetic sound bed in `<angle brackets>`.

## CLI skeleton

Used by `scripts/explore.py` when no `--prompt-file` is passed. Seedance can see the still, so this skeleton tells it to derive the 15 beats from the image.

`{{WORLD}}` is replaced by `--world` or by a short default.

```
meme_reference corresponds to the attached reference image. Use it as the sole semantic and visual evidence for the subject(s). Carefully extract appearance, clothing or markings, exact pose, facial expression, composition, and the core meaning of the meme.

Re-stage those exact elements inside a complete, believable physical world: {{WORLD}}. Elevate the meme's energy and tone. The subject(s) in every frame must be the same beings from meme_reference — same face, body, clothes, dirt, and pose. Do not replace them with cleaner or generic lookalikes.

Do not show the original uploaded image, screenshots, borders, captions, watermarks, website UI, typography, or compression artifacts.

Technical base: Arri Alexa 65, anamorphic 2.39:1, 35mm Kodak 5219, fine grain, hyper-realistic, no music, diegetic sound only. Subjects stay almost completely frozen. Only the camera moves.

Write and execute exactly 15 one-second stages derived from THIS still:

[Stage 1] 0-1s. Initial state: the main subject(s) from meme_reference stand perfectly still in the new environment, locked in their iconic pose and expression. Primary event: extreme close-up on the single most defining detail of the pose or expression. End state: hyper-detailed view of that detail.

[Stage 2] through [Stage 14]. Continue from the previous stage. Subjects remain frozen. Each stage introduces a new cinematic camera move aimed at a real detail that exists on THIS subject or in THIS world (skin, fabric, a held object, a mark, a reflection, a texture, then the environment). Progressively reveal the character, then the place, then move around the static subject.

[Stage 15] 14-15s. Continue from the previous stage. Primary event: camera snaps back to a perfectly centered, steady master composition that matches the original framing and feeling of meme_reference. End state: iconic final frame.

Keep character identity, clothing, exact pose, expression, and the chosen environment 100% consistent across all 15 stages.

<quiet diegetic ambience that fits the chosen environment>
```

## Agent path (higher quality)

Do not send the skeleton raw. Read the still first. Write the 15 stages as Maxescu did for the smug-guy meme: name the actual details (finger-on-temple, gold watch, leather collar, shop-window reflection). Then send that filled prompt with the still as `omni_reference`.

A worked filled prompt is in `examples/filled-prompt.puppy.txt`.
