from model_loader import get_pipeline
from utils_deploy import preprocess_image
import os

def generate_image(models, subject_image_path, prompt, guidance_scale, output_path, lora_weights_path=None):
    # Preprocess the subject image
    subject_image_tensor = preprocess_image(subject_image_path)

    # Get the pipeline
    pipeline = get_pipeline(models)

    # Load fine-tuned LoRA weights if provided
    if lora_weights_path:
        pipeline.load_lora_weights(lora_weights_path)

    # Generate the image
    generator = models["generator"]
    generated_image = pipeline(
        prompt=prompt,
        num_inference_steps=4,
        guidance_scale=guidance_scale,
        generator=generator,
        height=512,
        width=512,
    ).images[0]

    # Save the generated image
    generated_image.save(output_path)
    return output_path
