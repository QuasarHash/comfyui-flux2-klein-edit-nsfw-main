# Flux2 Klein Edit NSFW (reference edit + full refiner)

RunPod serverless worker for **Klein reference edit → mopMix refiner → Pussy FaceDetailer → Nipples FaceDetailer → save**.

SFW edit (`comfyui-flux2-klein-edit-main`) stops after mopMix. This repo adds `klein_snofs_v1_4` (lora_4) and the anatomy detailer chain from the generate NSFW worker.

**UI:** [klein-studio-ui](https://github.com/korotoshi/klein-studio-ui) — **Edit NSFW** mode.

## Pipeline

```
Reference image(s) → Klein edit (LoRAs incl. snofs)
  → mopMix KSampler refiner
  → Pussy.pt + SAM FaceDetailer
  → Nipples.pt + SAM FaceDetailer
  → save
```

Supports **1 ref** (scene/subject) and **2 refs** (scene + face/outfit), same as SFW edit.

## Models

Same network volume as generate NSFW — see `models-manifest.json`. No extra downloads if generate NSFW is already set up.

## Regenerate API workflows

```bash
python3 scripts/strip_and_flatten.py
```

Writes `api-workflow-single.json`, `api-workflow-multi.json`, test inputs, and syncs `klein-studio-ui/ui/edit-nsfw-workflow-*.json` when that folder exists.

## Deploy (RunPod)

1. Push this repo to GitHub (`korotoshi/comfyui-flux2-klein-edit-nsfw-main`).
2. RunPod → Serverless → **Deploy from GitHub** → this repo.
3. Attach the Klein network volume (EU-RO-1).
4. Set execution timeout **≥ 1800s**.
5. Copy endpoint ID into Vercel `RUNPOD_EDIT_NSFW_ENDPOINT`.

## Test

```bash
RUNPOD_API_KEY=rpa_… ./scripts/test-endpoint.sh <your-endpoint-id>
```