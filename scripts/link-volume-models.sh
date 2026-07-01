#!/usr/bin/env bash
# Symlink pod volume layout for Klein NSFW (base + anatomy detectors).
set -euo pipefail

ROOT="${VOLUME_ROOT:-/workspace}"
M="${ROOT}/models"

mkdir -p \
  "${M}/diffusion_models" \
  "${M}/text_encoders" \
  "${M}/vae" \
  "${M}/checkpoints" \
  "${M}/loras" \
  "${M}/sams" \
  "${M}/ultralytics/bbox"

link() {
  local dest_subdir="$1"
  local dest_name="$2"
  local rel_src="$3"
  local dest="${M}/${dest_subdir}/${dest_name}"

  if [[ ! -e "${M}/${rel_src}" ]]; then
    echo "  SKIP  ${dest_subdir}/${dest_name}  (missing: ${rel_src})"
    return 1
  fi

  ln -sfn "../${rel_src}" "$dest"
  echo "  OK    ${dest_subdir}/${dest_name}  ->  ${rel_src}"
}

echo "Linking Klein NSFW models under ${M}"
echo ""
link diffusion_models gonzalomoKlein_v10.safetensors "Stable-diffusion/gonzalomoKlein_v10.safetensors"
link checkpoints mopMix_omnia.safetensors "Stable-diffusion/mopMix_omnia.safetensors"
link text_encoders qwen_3_8b_fp8mixed.safetensors "text_encoder/qwen_3_8b_fp8mixed.safetensors"
link vae flux2-vae.safetensors "VAE/flux2-vae.safetensors"
link loras Yarely_Rae_Lora_Klein_v1_epoch_8.safetensors "Lora/Yarely_Rae_Lora_Klein_v1_epoch_8.safetensors"
link loras InstaPic.safetensors "Lora/InstaPic.safetensors"
link loras lenovo_flux_klein9b.safetensors "Lora/lenovo_flux_klein9b.safetensors"
link loras klein_snofs_v1_4.safetensors "Lora/klein_snofs_v1_4.safetensors"
link sams sam_vit_b_01ec64.pth "sams/sam_vit_b_01ec64.pth" || true

# Anatomy bbox detectors — copy or place real files here (not self-symlinks):
#   models/ultralytics/bbox/Nipples.pt
#   models/ultralytics/bbox/Pussy.pt
# If you only have them under models/Lora/ or elsewhere, run download-nsfw-models.sh
# or: cp /path/to/Nipples.pt models/ultralytics/bbox/
if [[ -f "${M}/ultralytics/bbox/Nipples.pt" ]]; then
  echo "  OK    ultralytics/bbox/Nipples.pt"
else
  echo "  MISS  ultralytics/bbox/Nipples.pt"
fi
if [[ -f "${M}/ultralytics/bbox/Pussy.pt" ]]; then
  echo "  OK    ultralytics/bbox/Pussy.pt"
else
  echo "  MISS  ultralytics/bbox/Pussy.pt"
fi

echo ""
echo "Required anatomy detectors (if SKIP above):"
echo "  models/ultralytics/bbox/Nipples.pt"
echo "  models/ultralytics/bbox/Pussy.pt"
echo "  models/sams/sam_vit_b_01ec64.pth"