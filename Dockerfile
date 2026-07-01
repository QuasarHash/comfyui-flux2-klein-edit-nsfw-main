# Klein image-edit + mopMix refiner + NSFW anatomy detailers (same volume as generate NSFW).
FROM runpod/worker-comfyui:5.8.4-base

ARG CACHE_BUST=2026-07-01-edit-nsfw-v1

RUN git clone https://github.com/yolain/ComfyUI-Easy-Use /comfyui/custom_nodes/ComfyUI-Easy-Use \
    && cd /comfyui/custom_nodes/ComfyUI-Easy-Use \
    && (git checkout 54614079ca96fa66c8953ff89dc66ca77245f5db 2>/dev/null \
        || git fetch origin 54614079ca96fa66c8953ff89dc66ca77245f5db --depth=1 \
        && git checkout 54614079ca96fa66c8953ff89dc66ca77245f5db \
        || echo "WARN: ComfyUI-Easy-Use pin unreachable, using HEAD")

RUN comfy node install --exit-on-fail rgthree-comfy@1.0.2512112053 --mode remote \
    || comfy node install --exit-on-fail rgthree-comfy --mode remote

RUN comfy node install --exit-on-fail comfyui-impact-pack --mode remote
RUN comfy node install --exit-on-fail comfyui-impact-subpack --mode remote

COPY extra_model_paths.yaml /comfyui/extra_model_paths.yaml
COPY handler.py /handler.py
COPY nodes-manifest.json api-workflow-single.json api-workflow-multi.json scripts/verify_workflow_nodes.py /tmp/workflow-check/
COPY scripts/link-impact-models.sh /link-impact-models.sh
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /link-impact-models.sh /docker-entrypoint.sh \
    && python3 /tmp/workflow-check/verify_workflow_nodes.py

ENTRYPOINT ["/docker-entrypoint.sh"]