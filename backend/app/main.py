import os
import shutil
import uvicorn
import uuid
import hashlib
import time
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from model_loader import load_models, load_inference_pipeline
from flux_infer_combined import parse_args, finetune_lora, generate_img
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Allow CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (generated image results)
os.makedirs("generated_outputs", exist_ok=True)
app.mount("/generated_outputs", StaticFiles(directory="generated_outputs"), name="generated_outputs")

# Preload models (excluding inference pipeline)
models = load_models()

# Simple in-memory cache to avoid refinetuning for the same image
image_cache = {}
"""

# # sample images are cached here for faster demonstrations
image_cache["f3b73110efadabcad8205315a18cace4"] = "generated_outputs/f3b73110efadabcad8205315a18cace4/796e2174"    #armcahir
image_cache["48994ab7ba64a0eccf900ce2634ee709"] = "generated_outputs/48994ab7ba64a0eccf900ce2634ee709/3dc7a183"    #cat
image_cache["1fd8cea55af7229ee1ee52b2ef27aa7e"] = "generated_outputs/1fd8cea55af7229ee1ee52b2ef27aa7e/7ae9ae3c"    #dresser
image_cache["a4692daad15eef9598ff059bde76c83a"] = "generated_outputs/a4692daad15eef9598ff059bde76c83a/423d1bbf"    #mower
image_cache["e0917864df7d6c84bf98fc9a0bb8dbd4"] = "generated_outputs/e0917864df7d6c84bf98fc9a0bb8dbd4/e59bbc38"    #alpaca
image_cache["14f7784c921f286841b9f619119dcf4e"] = "generated_outputs/14f7784c921f286841b9f619119dcf4e/72b407eb"    #tv stand
image_cache["252ea5a79a7bf450acbe5a0e9532219f"] = "generated_outputs/252ea5a79a7bf450acbe5a0e9532219f/b20c4cec"    #adirondack_chair
image_cache["1471469edaf41b97b58a6a6642f2e658"] = "generated_outputs/1471469edaf41b97b58a6a6642f2e658/c4d5a8d1"    #throw pillow
"""
# Store timestamp of when weights were cached
# image_cache_timestamp = {}
# CACHE_EXPIRY_SECONDS = 36000  # 1 hour

# Helper to hash image bytes
def get_image_hash(image_path):
    with open(image_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

@app.post("/generate")
async def generate(
    product_image: UploadFile,
    prompt: str = Form(...),
    # guidance_scale: float = Form(...),
    output_path: str = "output.png"
):
    try:
        # Save uploaded image temporarily
        temp_image_path = f"temp_{product_image.filename}"
        with open(temp_image_path, "wb") as buffer:
            shutil.copyfileobj(product_image.file, buffer)

        # Generate image hash
        image_hash = get_image_hash(temp_image_path)
        output_dir = f"generated_outputs/{image_hash}"
        os.makedirs(output_dir, exist_ok=True)

        # Split prompt
        subject_prompt = prompt.split('.')[0]
        target_prompt = '. '.join([s.strip() for s in prompt.split('.') if s.strip()][1:]) + '.'

        current_time = time.time()

        # Auto-delete expired cache
        # expired_hashes = [h for h, ts in image_cache_timestamp.items() if current_time - ts > CACHE_EXPIRY_SECONDS]
        # for h in expired_hashes:
        #     print(f"🧹 Removing expired cache for {h}")
        #     shutil.rmtree(image_cache[h], ignore_errors=True)
        #     del image_cache[h]
        #     del image_cache_timestamp[h]

        # If weights for this image already exist, skip fine-tuning
        if image_hash in image_cache:
            print("⚡ Using cached LoRA weights")
            weights_output_dir = image_cache[image_hash]
        else:
            print("🛠️ Fine-tuning LoRA for new image")
            session_id = str(uuid.uuid4())[:8]
            weights_output_dir = os.path.join(output_dir, session_id)

            args_list = [
                "--subject_image_path", temp_image_path,
                "--prompt", subject_prompt,
                "--train_text_encoder",
                "--output_dir", weights_output_dir,
                "--lr_warmup_steps", "0",
                "--lr_scheduler", "constant",
                "--train_batch_size", "1",
                "--resolution", "512",
                "--num_train_epochs", "50",
                "--early_stopping_threshold_percentage", "3",
                "--early_stopping_max_count", "7",
                "--num_inference_steps", "1",
                "--learning_rate", "2e-4",
                "--seed", "42",
                "--save_weights",
                "--output_path", os.path.join(weights_output_dir, "result.png"),
                "--mixed_precision", "bf16",
                "--weights_output_dir", weights_output_dir,
                "--guidance_scale", "0.0",
            ]

            args = parse_args(args_list)
            _ = finetune_lora(args, models)
            image_cache[image_hash] = weights_output_dir
            # image_cache_timestamp[image_hash] = current_time

        # Generate image with environment prompt using saved weights
        print("🧠 Loading inference pipeline after fine-tuning...")
        pipeline_inference = load_inference_pipeline()
        final_output_path = os.path.join(image_cache[image_hash], "final_output.png")

        args_list = [
            "--prompt", target_prompt,
            "--output_path", final_output_path,
            "--weights_output_dir", image_cache[image_hash],
            "--num_inference_steps", "4",
            "--guidance_scale", "0.0",
            "--seed", "42",
        ]
        args = parse_args(args_list)
        generated_image_path = generate_img(args, pipeline_inference)

        os.remove(temp_image_path)

        # Serve correct image URL relative to static mount
        image_url = f"/{generated_image_path}"
        print(f"✅ Image generated successfully: {image_url}")
        return JSONResponse(content={"url": image_url}, status_code=200)

    except Exception as e:
        import traceback
        traceback.print_exc()  # 🔍 print the full traceback to terminal
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
