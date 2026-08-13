# Prompt contract

Method published by [Alex Patrascu (@maxescu)](https://x.com/maxescu/status/2087592524940452149). This file is the single source of truth for the text sent to Seedance 2.5.

## What is locked

Not overridable — `scripts/explore.py` always sends these:

- Model: `seedance_2_5`
- Mode: `omni_reference`
- Media: the meme still as the only `--image-references` item
- Audio: `--generate_audio true` (diegetic only)

## Defaults you can override

`explore.py` exposes these as flags. The method assumes the values below; changing one puts you outside this contract:

- Duration: `15` (`--duration`)
- Aspect: `21:9` (`--aspect`) — closest Higgsfield enum to Alexa 2.39:1
- Resolution: `720p` (`--resolution`)

The accepted values come from `higgsfield model get seedance_2_5` and are enforced by the script before anything is submitted.

## What is not locked

Seedance has no seed. Same image + same prompt will not render identical pixels. The contract makes the *method* repeatable. Because a take cannot be reproduced, `explore.py` never overwrites an existing `.mp4`.

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

Used by `scripts/explore.py` when no `--prompt-file` is passed. The live text is `examples/skeleton.txt`. The literal token `{world}` is replaced by `--world`; every other character is sent verbatim, so braces elsewhere in the file are safe.

`--world` fills the skeleton only. Passing it alongside `--prompt-file` is an error, and sending the raw skeleton as a `--prompt-file` is rejected while `{world}` is still in it — otherwise a paid job would be staged in a place literally named `{world}`.

## Agent path (higher quality)

Do not send the skeleton raw. Read the still first. Write the 15 stages as Maxescu did for the smug-guy meme: name the actual details (finger-on-temple, gold watch, leather collar, shop-window reflection). Then send that filled prompt with the still as `omni_reference`.

A worked filled prompt is in `examples/filled-prompt.puppy.txt`.
