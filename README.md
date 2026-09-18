# RIFE API — Python client

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) [![Hosted on Synexa](https://img.shields.io/badge/hosted%20on-Synexa-6366f1.svg)](https://synexa.ai/explore/bytedance/seedvr2-upscale)

RIFE (Real-Time Intermediate Flow Estimation) is the frame interpolation model behind most open-source slow-motion and frame-rate conversion tools. This package is a Python client for the video enhancement steps that usually surround a RIFE pass: it gives you a RIFE-adjacent API for detail-recovering upscaling and for merging clips to a common frame rate and resolution, with `pip install rife-api` and no GPU of your own. Frame interpolation itself is not hosted; see the note in About.

You get a blocking `run()` that returns when the job is finished, a submit-and-poll path for long videos, webhook delivery for servers that must not block, and a single runtime dependency (`requests`). It is meant for media pipelines, backend services and notebooks that need enhancement as a function call.

> **Try it now:** [https://synexa.ai/explore/bytedance/seedvr2-upscale](https://synexa.ai/explore/bytedance/seedvr2-upscale) — the hosted model behind this client. New accounts get a free trial credit.

## Contents

- [Why this client](#why-this-client)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Hosted models](#hosted-models)
- [Parameters](#parameters)
- [Advanced usage](#advanced-usage)
- [About RIFE](#about-rife)
- [Use cases](#use-cases)
- [FAQ](#faq)
- [License](#license)

## Why this client

- **Upscaling is the expensive step, not interpolation.** RIFE itself runs above 30 fps for 2x 720p on a 2080 Ti, but the super-resolution pass that usually precedes or follows it is a diffusion-class model. `bytedance/seedvr2-upscale` does that on hosted GPUs for $0.004 per image.
- **No ffmpeg build to maintain.** Normalising frame rate and resolution across clips before interpolation means a correct ffmpeg filter chain on every worker. `synexa/merge-videos` does it server-side for $0.004 per run.
- **No cold start.** A self-hosted SeedVR2 worker spends minutes loading weights before the first frame; hosted runs start on a warm model.
- **Per-run pricing.** Both endpoints are billed per completed run, so a batch of a thousand stills costs a few dollars and an idle pipeline costs nothing.

## Installation

```bash
pip install git+https://github.com/rife-dev/rife-api.git
```

Then set your API key (create one at [synexa.ai](https://synexa.ai)):

```bash
export SYNEXA_API_KEY="sk-..."
```

## Quickstart

```python
import rife_api

output = rife_api.run({
    "image_url": "https://example.com/input.png"
})
print(output)   # URL(s) of the generated result
```

Or with an explicit client:

```python
from rife_api import Client

client = Client(api_key="sk-...")
output = client.run({"image_url": "https://example.com/input.png"})
```

## Hosted models

| Model | Category | What it does | Price / run |
|---|---|---|---|
| [`bytedance/seedvr2-upscale`](https://synexa.ai/explore/bytedance/seedvr2-upscale) | super-resolution | SeedVR2 restores and upscales images, recovering detail rather than simply interpolating pixels. | $0.004 |
| [`synexa/merge-videos`](https://synexa.ai/explore/synexa/merge-videos) | video-to-video | Merges two or more videos into one, end to end, normalising frame rate and resolution. | $0.004 |

The default model is **`bytedance/seedvr2-upscale`**; pass `model="owner/name"` to `run()` to use another one from the table.

## Parameters

### `bytedance/seedvr2-upscale`

| Field | Type | Required | Default | Range | Description |
|---|---|---|---|---|---|
| `image_url` | file | yes | — | — | Image to upscale (.jpg/.png/.webp) |
| `upscale_mode` | string | no | `factor` | target, factor | The mode to use for the upscale. If 'target', the upscale factor will be calculated based on the target resolution. If 'factor', the upscale factor will be used directly. |
| `upscale_factor` | number | no | `2` | 1, 10 | Upscaling factor to be used. Will multiply the dimensions with this factor when `upscale_mode` is `factor`. |
| `target_resolution` | string | no | `1080p` | 720p, 1080p, 1440p, 2160p | The target resolution to upscale to when `upscale_mode` is `target`. |
| `seed` | integer | no | `random` | — | The random seed used for the generation process. |
| `noise_scale` | number | no | `0.1` | 0, 1 | The noise scale to use for the generation process. |
| `output_format` | string | no | `jpg` | png, jpg, webp | The format of the output image. |

### `synexa/merge-videos`

| Field | Type | Required | Default | Range | Description |
|---|---|---|---|---|---|
| `video_urls` | files | yes | — | — | Videos to merge, in order (.mp4/.mov/.webm). At least 2 |
| `target_fps` | number | no | — | 1, 60 | Target FPS for the output video. If not provided, uses the lowest FPS from input videos. |
| `resolution` | string | no | — | square_hd, square, portrait_4_3, portrait_16_9, landscape… | Resolution of the final video. Width and height must be between 512 and 2048. |
| `resolution_aspect_ratio_video_index` | integer | no | — | — | Zero-based index of the input video whose aspect ratio should be used when resolution is not provided. If omitted, preserves the default behavior of using the minimum width and minimum height across input videos. |

## Advanced usage

**Submit without blocking, then poll:**

```python
prediction = client.run(input, wait=False)      # returns immediately
prediction = client.wait(prediction, timeout=300)
print(prediction["output"])
```

**Webhook on completion:**

```python
client.run(input, wait=False, webhook="https://your-app.example/hooks/synexa")
```

**Errors:**

```python
from rife_api import ModelError, PredictionTimeout

try:
    output = client.run(input)
except ModelError as e:
    print("failed:", e, e.prediction and e.prediction.get("id"))
except PredictionTimeout:
    print("still running — poll later")
```

Status values you will see on a prediction: `starting` → `processing` → `succeeded` | `failed`.

## About RIFE

RIFE was introduced by Zhewei Huang and collaborators in the paper *Real-Time Intermediate Flow Estimation for Video Frame Interpolation*, first posted in 2020 and published at ECCV 2022. Instead of estimating bidirectional optical flow and then warping, its IFNet predicts the intermediate flows directly, coarse to fine, and a privileged distillation scheme trains it with a teacher that is allowed to see the ground-truth middle frame. The result is a small network that produces one interpolated frame per pass with no pretrained flow model.

The practical payoff is speed. The authors report more than 30 frames per second for 2x interpolation of 720p video on a single RTX 2080 Ti, and the arbitrary-timestep variant can produce any intermediate frame, not only the midpoint. That is why RIFE and the Practical-RIFE 4.x checkpoints sit inside Flowframes, SVFI, the ncnn-Vulkan ports and a long list of ComfyUI and video-editing plugins for slow motion, 24 to 60 fps conversion and anime upscaling pipelines.

Limits are those of flow-based interpolation: large or fast motion, thin structures, occlusions and scene cuts produce ghosting or warping, and the model does not add detail or resolution. In production it is almost always paired with a super-resolution model and a frame-rate normalisation step, which is where this client fits.

Frame interpolation is not currently hosted on Synexa, so this client does not provide it; the original RIFE weights are available at https://github.com/hzwer/ECCV2022-RIFE if you want to self-host, and they run comfortably on a consumer GPU. The hosted endpoints used here are different models covering the enhancement steps around it: `bytedance/seedvr2-upscale`, which restores and upscales images by recovering detail rather than interpolating pixels, and `synexa/merge-videos`, which concatenates clips while normalising frame rate and resolution.

**Official project:** https://github.com/hzwer/ECCV2022-RIFE

## Use cases

- **Upscale extracted frames** — call `run()` with a frame as `image_url` and `upscale_mode="factor"`, `upscale_factor=2` to get a detail-restored 2x image before re-encoding.
- **Hit a target resolution** — set `upscale_mode="target"` and `target_resolution="1080p"` so every input lands at the same size regardless of source.
- **Normalise clips before interpolation** — pass a list of `video_urls` to `synexa/merge-videos` with `target_fps=24` to get one file at a consistent frame rate for a local RIFE pass.
- **Stitch dailies** — merge shot-by-shot renders into one review video, using `resolution_aspect_ratio_video_index` to pick which clip sets the aspect ratio.
- **Batch archive restoration** — submit a folder of low-resolution stills without blocking and collect the upscaled images via a webhook.
- **Reproducible re-runs** — set `seed` and `noise_scale` explicitly so a re-processed frame matches the previous output.

## FAQ

**Is there a RIFE API?**

Not from the authors; RIFE ships as a PyTorch repository and as ncnn ports. Frame interpolation is not currently hosted on Synexa either, so this package does not provide it. What it does provide is an HTTPS client for the enhancement steps around a RIFE pass: super-resolution and frame-rate normalisation.

**How much does the RIFE API cost?**

Both hosted endpoints, `bytedance/seedvr2-upscale` and `synexa/merge-videos`, are $0.004 per run. Billing is per completed run, with no instance cost. Running RIFE itself locally is free apart from the GPU.

**Can I run RIFE without a GPU?**

RIFE runs on CPU but far below real time. It is light enough that any consumer GPU handles it, which is why this client leaves interpolation local and offloads the heavier upscaling step to the hosted `bytedance/seedvr2-upscale` endpoint.

**Does this client work with the original hzwer/ECCV2022-RIFE repo, Practical-RIFE, Flowframes or ComfyUI?**

No. It does not load RIFE checkpoints, expose an interpolation call, or talk to Flowframes or the ComfyUI frame-interpolation nodes. It is an HTTP client for the hosted upscaling and merge endpoints only.

**What input formats does it accept?**

`bytedance/seedvr2-upscale` requires `image_url` (.jpg, .png or .webp) with optional `upscale_mode`, `upscale_factor`, `target_resolution`, `seed`, `noise_scale` and `output_format`. `synexa/merge-videos` requires `video_urls`, a list of at least two .mp4, .mov or .webm files, with optional `target_fps`, `resolution` (512 to 2048 per side) and `resolution_aspect_ratio_video_index`.

**Is this the official RIFE SDK?**

No. This is an independent client and is not affiliated with the RIFE authors. The official project is at https://github.com/hzwer/ECCV2022-RIFE.

## Related

- [RIFE (official repository)](https://github.com/hzwer/ECCV2022-RIFE)
- [Synexa Python client](https://github.com/synexa-ai/synexa-python)
- [bytedance/seedvr2-upscale on Synexa](https://synexa.ai/explore/bytedance/seedvr2-upscale)
- [synexa/merge-videos on Synexa](https://synexa.ai/explore/synexa/merge-videos)

## License

MIT. This is an independent, community-maintained client and is not affiliated with or endorsed by the authors of RIFE. Model weights and trademarks belong to their respective owners.
