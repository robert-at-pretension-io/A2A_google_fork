#!/usr/bin/env python3
"""generate_vertex_images.py

Bulk image generator for Google Vertex AI Imagen.

Requirements:
  pip install google-cloud-aiplatform --upgrade

Before running:
  * Enable the Vertex AI API and Generative AI features in your Google Cloud project.
  * Authenticate with Application Default Credentials (`gcloud auth application-default login`)
  * Set the environment variable GOOGLE_APPLICATION_CREDENTIALS if needed.

Usage:
  python generate_vertex_images.py prompts.json --project YOUR_PROJECT_ID --location us-central1 --model imagen-3.0-generate-002 --output-dir ./out --n 1

The JSON must look like:
[
  { "prompt": "A cat riding a rocket", "filename": "rocket_cat.png" },
  ...
]
"""

import json
import pathlib
import argparse
import sys
import time
import os

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from google.api_core.exceptions import ResourceExhausted
from tenacity import retry, stop_after_attempt, wait_exponential


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate images from a JSON prompt list using Vertex AI Imagen."
    )
    parser.add_argument("json_file", help="Path to JSON file with prompts")
    parser.add_argument(
        "--project", required=True, help="Google Cloud project ID to bill"
    )
    parser.add_argument(
        "--location",
        default="us-central1",
        help="Vertex AI region (default: us-central1)",
    )
    parser.add_argument(
        "--model",
        default="imagen-3.0-generate-002",
        help="Model name (see docs for available versions)",
    )
    parser.add_argument(
        "--output-dir",
        default="out",
        help="Directory to write generated images (will be created if absent)",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="Number of images per prompt (1-8 depending on model version)",
    )
    parser.add_argument(
        "--aspect_ratio",
        default="1:1",
        help="Aspect ratio, e.g. 1:1, 16:9, etc.",
    )
    parser.add_argument("--language", default="en", help="Prompt language code")
    parser.add_argument(
        "--safety_filter_level",
        default="block_medium_and_above",
        help="Safety filter level (see docs)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    prompt_entries = json.loads(pathlib.Path(args.json_file).read_text())
    out_dir = pathlib.Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    vertexai.init(project=args.project, location=args.location)
    model = ImageGenerationModel.from_pretrained(args.model)

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        retry=lambda retry_state: isinstance(retry_state.outcome.exception(), ResourceExhausted),
        reraise=True,
    )
    def generate_and_save_image_with_retry(
        current_model, current_prompt, num_images, aspect_ratio, language, safety_filter_level, output_path_base, entry_filename
    ):
        sys.stderr.write(f"[+] Attempting to generate '{entry_filename}'...\n")
        images = current_model.generate_images(
            prompt=current_prompt,
            number_of_images=num_images,
            aspect_ratio=aspect_ratio,
            language=language,
            safety_filter_level=safety_filter_level,
        )
        for i, img in enumerate(images):
            out_path_final = output_path_base
            if num_images > 1:
                stem = output_path_base.stem
                suffix = output_path_base.suffix or ".png"
                out_path_final = out_dir / f"{stem}_{i}{suffix}"
            img.save(location=str(out_path_final), include_generation_parameters=False)
            sys.stderr.write(f"[+] Saved '{out_path_final}'\n")

    for entry in prompt_entries:
        prompt = entry.get("prompt")
        filename = entry.get("filename")
        if not prompt or not filename:
            sys.stderr.write(f"Skipping malformed entry: {entry}\n")
            continue

        # Check if file(s) already exist
        all_files_exist = True
        if args.n == 1:
            if not (out_dir / filename).exists():
                all_files_exist = False
        else:
            for i in range(args.n):
                stem = pathlib.Path(filename).stem
                suffix = pathlib.Path(filename).suffix or ".png"
                potential_path = out_dir / f"{stem}_{i}{suffix}"
                if not potential_path.exists():
                    all_files_exist = False
                    break
        
        if all_files_exist:
            sys.stderr.write(f"[*] Skipping '{filename}' as output file(s) already exist.\n")
            continue

        try:
            base_output_path = out_dir / filename
            generate_and_save_image_with_retry(
                model,
                prompt,
                args.n,
                args.aspect_ratio,
                args.language,
                args.safety_filter_level,
                base_output_path,
                filename
            )
        except ResourceExhausted as exc:
            sys.stderr.write(
                f"[!] Quota error generating '{filename}' after retries: {exc}\n"
            )
            continue
        except Exception as exc:
            sys.stderr.write(f"[!] Error generating '{filename}': {exc}\n")
            continue

        # time.sleep(0.4) # Replaced by tenacity's wait logic


if __name__ == "__main__":
    main()
