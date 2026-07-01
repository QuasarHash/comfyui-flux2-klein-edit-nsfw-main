#!/usr/bin/env python3
"""Emit Klein edit API workflows with mopMix refiner + NSFW anatomy detailers."""

from __future__ import annotations

import json
import random
from copy import deepcopy
from pathlib import Path

UNET_MODEL = "gonzalomoKlein_v10.safetensors"
REFINER_CHECKPOINT = "mopMix_omnia.safetensors"
OUTPUT_WIDTH = 1536
OUTPUT_HEIGHT = 1920
KLEIN_STEPS = 5
REFINER_STEPS = 12
REFINER_DENOISE = 0.15
SNOFS_STRENGTH = 0.4
DEFAULT_NEGATIVE = (
    "low quality, tanlines, tan lines, cartoon, illustration, sketch, drawing"
)


def _klein_lora_stack(unet_node: str, clip_node: str) -> dict:
    return {
        "438": {
            "class_type": "Power Lora Loader (rgthree)",
            "inputs": {
                "model": [unet_node, 0],
                "clip": [clip_node, 0],
                "lora_1": {
                    "on": True,
                    "lora": "Yarely_Rae_Lora_Klein_v1_epoch_8.safetensors",
                    "strength": 1.25,
                },
                "lora_2": {
                    "on": True,
                    "lora": "InstaPic.safetensors",
                    "strength": 0.4,
                },
                "lora_3": {
                    "on": True,
                    "lora": "lenovo_flux_klein9b.safetensors",
                    "strength": 0.4,
                },
                "lora_4": {
                    "on": True,
                    "lora": "klein_snofs_v1_4.safetensors",
                    "strength": SNOFS_STRENGTH,
                },
            },
        },
    }


def _refiner_chain(decode_node: str, refiner_seed: int | None = None) -> dict:
    if refiner_seed is None:
        refiner_seed = random.randint(0, 2**53 - 1)
    return {
        "444": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": REFINER_CHECKPOINT},
        },
        "17": {
            "class_type": "Power Lora Loader (rgthree)",
            "inputs": {"model": ["444", 0]},
        },
        "18": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": [decode_node, 0], "vae": ["444", 2]},
        },
        "19": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["444", 1], "text": DEFAULT_NEGATIVE},
        },
        "20": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["444", 1], "text": ""},
        },
        "22": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["17", 0],
                "positive": ["20", 0],
                "negative": ["19", 0],
                "latent_image": ["18", 0],
                "seed": refiner_seed,
                "steps": REFINER_STEPS,
                "cfg": 1,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": REFINER_DENOISE,
            },
        },
        "442": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["22", 0], "vae": ["444", 2]},
        },
    }


def _nsfw_detailer_tail(
    pussy_seed: int | None = None,
    nipples_seed: int | None = None,
) -> dict:
    """Pussy → Nipples FaceDetailer chain after mopMix decode (node 442)."""
    if pussy_seed is None:
        pussy_seed = random.randint(0, 2**31 - 1)
    if nipples_seed is None:
        nipples_seed = random.randint(0, 2**31 - 1)
    return {
        "427": {
            "class_type": "easy cleanGpuUsed",
            "inputs": {"anything": ["442", 0]},
        },
        "428": {
            "class_type": "easy clearCacheAll",
            "inputs": {"anything": ["427", 0]},
        },
        "520": {
            "class_type": "SAMLoader",
            "inputs": {
                "model_name": "sam_vit_b_01ec64.pth",
                "device_mode": "Prefer GPU",
            },
        },
        "521": {
            "class_type": "UltralyticsDetectorProvider",
            "inputs": {"model_name": "bbox/Pussy.pt"},
        },
        "522": {
            "class_type": "FaceDetailer",
            "inputs": {
                "image": ["428", 0],
                "model": ["444", 0],
                "clip": ["444", 1],
                "vae": ["444", 2],
                "positive": ["20", 0],
                "negative": ["19", 0],
                "bbox_detector": ["521", 0],
                "sam_model_opt": ["520", 0],
                "seed": pussy_seed,
                "guide_size": 512,
                "guide_size_for": True,
                "max_size": 1024,
                "steps": 6,
                "cfg": 1,
                "sampler_name": "lcm",
                "scheduler": "karras",
                "denoise": 0.45,
                "feather": 5,
                "noise_mask": True,
                "force_inpaint": True,
                "bbox_threshold": 0.5,
                "bbox_dilation": 10,
                "bbox_crop_factor": 3,
                "sam_detection_hint": "center-1",
                "sam_dilation": 0,
                "sam_threshold": 0.93,
                "sam_bbox_expansion": 0,
                "sam_mask_hint_threshold": 0.7,
                "sam_mask_hint_use_negative": "False",
                "drop_size": 10,
                "wildcard": "",
                "cycle": 1,
                "inpaint_model": False,
                "noise_mask_feather": 20,
                "tiled_encode": False,
                "tiled_decode": False,
            },
        },
        "510": {
            "class_type": "SAMLoader",
            "inputs": {
                "model_name": "sam_vit_b_01ec64.pth",
                "device_mode": "Prefer GPU",
            },
        },
        "511": {
            "class_type": "UltralyticsDetectorProvider",
            "inputs": {"model_name": "bbox/Nipples.pt"},
        },
        "512": {
            "class_type": "FaceDetailer",
            "inputs": {
                "image": ["522", 0],
                "model": ["17", 0],
                "clip": ["444", 1],
                "vae": ["444", 2],
                "positive": ["20", 0],
                "negative": ["19", 0],
                "bbox_detector": ["511", 0],
                "sam_model_opt": ["510", 0],
                "seed": nipples_seed,
                "guide_size": 512,
                "guide_size_for": True,
                "max_size": 1024,
                "steps": 6,
                "cfg": 1,
                "sampler_name": "lcm",
                "scheduler": "karras",
                "denoise": 0.45,
                "feather": 5,
                "noise_mask": True,
                "force_inpaint": True,
                "bbox_threshold": 0.5,
                "bbox_dilation": 10,
                "bbox_crop_factor": 3,
                "sam_detection_hint": "center-1",
                "sam_dilation": 0,
                "sam_threshold": 0.93,
                "sam_bbox_expansion": 0,
                "sam_mask_hint_threshold": 0.7,
                "sam_mask_hint_use_negative": "False",
                "drop_size": 10,
                "wildcard": "",
                "cycle": 1,
                "inpaint_model": False,
                "noise_mask_feather": 20,
                "tiled_encode": False,
                "tiled_decode": False,
            },
        },
    }


def _scale_ref(node_id: str, image_ref: list) -> dict:
    return {
        node_id: {
            "class_type": "ImageScale",
            "inputs": {
                "image": image_ref,
                "upscale_method": "lanczos",
                "width": OUTPUT_WIDTH,
                "height": OUTPUT_HEIGHT,
                "crop": "disabled",
            },
        },
    }


def _node_widget(workflow: dict, sg_id: str, node_id: int, field: str):
    definitions = {sg["id"]: sg for sg in workflow["definitions"]["subgraphs"]}
    for n in definitions[sg_id]["nodes"]:
        if n["id"] == node_id:
            wv = n.get("widgets_values") or []
            if field == "text":
                return wv[0] if wv else ""
            if field == "noise_seed":
                return wv[0] if wv else random.randint(0, 2**53 - 1)
    return None


def build_single_api(workflow: dict, prompt: str | None = None) -> dict:
    sg = "7b34ab90-36f9-45ba-a665-71d418f0df18"
    if prompt is None:
        prompt = _node_widget(workflow, sg, 74, "text")
    seed = _node_widget(workflow, sg, 73, "noise_seed")

    wf = {
        "76": {
            "class_type": "LoadImage",
            "inputs": {"image": "input_ref1.png", "upload": "image"},
        },
        "70": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": UNET_MODEL, "weight_dtype": "default"},
        },
        "71": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen_3_8b_fp8mixed.safetensors",
                "type": "flux2",
                "device": "default",
            },
        },
        "72": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "flux2-vae.safetensors"},
        },
        "61": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"},
        },
        "73": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed, "control_after_generate": "randomize"},
        },
        "62": {
            "class_type": "Flux2Scheduler",
            "inputs": {
                "steps": KLEIN_STEPS,
                "width": OUTPUT_WIDTH,
                "height": OUTPUT_HEIGHT,
            },
        },
        "66": {
            "class_type": "EmptyFlux2LatentImage",
            "inputs": {
                "width": OUTPUT_WIDTH,
                "height": OUTPUT_HEIGHT,
                "batch_size": 1,
            },
        },
        "74": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["71", 0], "text": prompt},
        },
        "82": {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["74", 0]},
        },
        "78": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["80", 0], "vae": ["72", 0]},
        },
        "77": {
            "class_type": "ReferenceLatent",
            "inputs": {"conditioning": ["74", 0], "latent": ["78", 0]},
        },
        "100": {
            "class_type": "ReferenceLatent",
            "inputs": {"conditioning": ["82", 0], "latent": ["78", 0]},
        },
        "63": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["438", 0],
                "positive": ["77", 0],
                "negative": ["100", 0],
                "cfg": 1,
            },
        },
        "64": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["73", 0],
                "guider": ["63", 0],
                "sampler": ["61", 0],
                "sigmas": ["62", 0],
                "latent_image": ["66", 0],
            },
        },
        "65": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["64", 0], "vae": ["72", 0]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "klein-edit-nsfw", "images": ["512", 0]},
        },
    }
    wf.update(_scale_ref("80", ["76", 0]))
    wf.update(_klein_lora_stack("70", "71"))
    wf.update(_refiner_chain("65"))
    wf.update(_nsfw_detailer_tail())
    return wf


def build_multi_api(workflow: dict, prompt: str | None = None) -> dict:
    sg = "65c22b29-59aa-496b-89c6-55a603658670"
    if prompt is None:
        prompt = _node_widget(workflow, sg, 109, "text")
    seed = _node_widget(workflow, sg, 106, "noise_seed")

    wf = {
        "76": {
            "class_type": "LoadImage",
            "inputs": {"image": "input_ref1.png", "upload": "image"},
        },
        "121": {
            "class_type": "LoadImage",
            "inputs": {"image": "input_ref2.png", "upload": "image"},
        },
        "107": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": UNET_MODEL, "weight_dtype": "default"},
        },
        "108": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen_3_8b_fp8mixed.safetensors",
                "type": "flux2",
                "device": "default",
            },
        },
        "110": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "flux2-vae.safetensors"},
        },
        "101": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"},
        },
        "106": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed, "control_after_generate": "randomize"},
        },
        "102": {
            "class_type": "Flux2Scheduler",
            "inputs": {
                "steps": KLEIN_STEPS,
                "width": OUTPUT_WIDTH,
                "height": OUTPUT_HEIGHT,
            },
        },
        "113": {
            "class_type": "EmptyFlux2LatentImage",
            "inputs": {
                "width": OUTPUT_WIDTH,
                "height": OUTPUT_HEIGHT,
                "batch_size": 1,
            },
        },
        "109": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["108", 0], "text": prompt},
        },
        "86": {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["109", 0]},
        },
        "116": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["111", 0], "vae": ["110", 0]},
        },
        "117": {
            "class_type": "ReferenceLatent",
            "inputs": {"conditioning": ["109", 0], "latent": ["116", 0]},
        },
        "115": {
            "class_type": "ReferenceLatent",
            "inputs": {"conditioning": ["86", 0], "latent": ["116", 0]},
        },
        "119": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["85", 0], "vae": ["110", 0]},
        },
        "120": {
            "class_type": "ReferenceLatent",
            "inputs": {"conditioning": ["117", 0], "latent": ["119", 0]},
        },
        "118": {
            "class_type": "ReferenceLatent",
            "inputs": {"conditioning": ["115", 0], "latent": ["119", 0]},
        },
        "103": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["438", 0],
                "positive": ["120", 0],
                "negative": ["118", 0],
                "cfg": 1,
            },
        },
        "104": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["106", 0],
                "guider": ["103", 0],
                "sampler": ["101", 0],
                "sigmas": ["102", 0],
                "latent_image": ["113", 0],
            },
        },
        "105": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["104", 0], "vae": ["110", 0]},
        },
        "122": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "klein-edit-nsfw-multi",
                "images": ["512", 0],
            },
        },
    }
    wf.update(_scale_ref("111", ["76", 0]))
    wf.update(_scale_ref("85", ["121", 0]))
    wf.update(_klein_lora_stack("107", "108"))
    wf.update(_refiner_chain("105"))
    wf.update(_nsfw_detailer_tail())
    return wf


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1]
    distilled = out_dir / "workflow.json"
    if not distilled.exists():
        sibling = out_dir.parent / "comfyui-flux2-klein-edit-main" / "workflow.json"
        if sibling.exists():
            distilled = sibling
        else:
            raise SystemExit(f"Missing workflow.json in {out_dir}")

    with open(distilled) as f:
        source = json.load(f)

    api_single = build_single_api(source)
    api_multi = build_multi_api(source)

    with open(out_dir / "api-workflow-single.json", "w") as f:
        json.dump(api_single, f, indent=2)
    with open(out_dir / "api-workflow-multi.json", "w") as f:
        json.dump(api_multi, f, indent=2)

    test_single = {
        "input": {
            "workflow": api_single,
            "images": [
                {"name": "input_ref1.png", "image": "data:image/png;base64,REPLACE_ME"},
            ],
        }
    }
    test_multi = {
        "input": {
            "workflow": api_multi,
            "images": [
                {"name": "input_ref1.png", "image": "data:image/png;base64,REPLACE_ME"},
                {"name": "input_ref2.png", "image": "data:image/png;base64,REPLACE_ME"},
            ],
        }
    }

    with open(out_dir / "test-input-single.json", "w") as f:
        json.dump(test_single, f, indent=2)
    with open(out_dir / "test-input-multi.json", "w") as f:
        json.dump(test_multi, f, indent=2)

    ui_dir = out_dir.parent / "klein-studio-ui" / "ui"
    if ui_dir.is_dir():
        with open(ui_dir / "edit-nsfw-workflow-single.json", "w") as f:
            json.dump(api_single, f, indent=2)
        with open(ui_dir / "edit-nsfw-workflow-multi.json", "w") as f:
            json.dump(api_multi, f, indent=2)
        print("wrote klein-studio-ui/ui/edit-nsfw-workflow-*.json")

    print("wrote api-workflow-single.json", len(api_single), "nodes")
    print("wrote api-workflow-multi.json", len(api_multi), "nodes")


if __name__ == "__main__":
    main()