import torch
from diffusers import FluxPipeline
from transformers import CLIPTokenizer, T5TokenizerFast
from utils.dino_utils import get_model_and_transforms_configs
from utils.ir_features_utils import get_ir_model_and_transforms
from accelerate import Accelerator
from accelerate.utils import DistributedDataParallelKwargs
from transformers import PretrainedConfig
from diffusers import AutoencoderKL, FlowMatchEulerDiscreteScheduler, FluxTransformer2DModel
from local_pipelines.pipeline_flux_with_grads import FluxPipelineWithGrads
from pathlib import Path
import time

_last_model_load_time = None
_models = None

# Static Paths
base_path = Path(__file__).resolve().parents[2]
print('base_path', base_path)
flux_model_root = base_path / "models" / "flux_schnell"
print('flux_model_root', flux_model_root)
ir_features_path = base_path / "models" / "ir_features.pth"
general_lora_path = base_path / "models" / "general_lora" / "pytorch_lora_weights.safetensors"

# Accelerator Setup
kwargs = DistributedDataParallelKwargs(find_unused_parameters=True)
accelerator = Accelerator(
    gradient_accumulation_steps=1,
    mixed_precision="bf16",
    kwargs_handlers=[kwargs],
)
weight_dtype = torch.bfloat16

def import_model_class_from_model_name_or_path(pretrained_model_name_or_path: str, subfolder: str = "text_encoder"):
    text_encoder_config = PretrainedConfig.from_pretrained(pretrained_model_name_or_path, subfolder=subfolder, local_files_only=True)
    model_class = text_encoder_config.architectures[0]
    if model_class == "CLIPTextModel":
        from transformers import CLIPTextModel
        return CLIPTextModel
    elif model_class == "T5EncoderModel":
        from transformers import T5EncoderModel
        return T5EncoderModel
    else:
        raise ValueError(f"{model_class} is not supported.")

def load_text_encoders(class_one, class_two):
    text_encoder_one = class_one.from_pretrained(flux_model_root, subfolder="text_encoder", local_files_only=True)
    text_encoder_two = class_two.from_pretrained(flux_model_root, subfolder="text_encoder_2", local_files_only=True)
    return text_encoder_one, text_encoder_two

def load_models():
    global _models, _last_model_load_time

    if _models is None or time.time() - _last_model_load_time > 900:    # 15 minutes
        print("Loading models into memory...")

        # Load tokenizers
        tokenizer_one = CLIPTokenizer.from_pretrained(flux_model_root, subfolder="tokenizer", local_files_only=True)
        tokenizer_two = T5TokenizerFast.from_pretrained(flux_model_root, subfolder="tokenizer_2", local_files_only=True)

        # Load text encoders
        text_encoder_cls_one = import_model_class_from_model_name_or_path(flux_model_root)
        text_encoder_cls_two = import_model_class_from_model_name_or_path(flux_model_root, subfolder="text_encoder_2")
        text_encoder_one, text_encoder_two = load_text_encoders(text_encoder_cls_one, text_encoder_cls_two)

        # Load VAE and Transformer
        vae = AutoencoderKL.from_pretrained(flux_model_root, subfolder="vae", local_files_only=True)
        transformer = FluxTransformer2DModel.from_pretrained(flux_model_root, subfolder="transformer", local_files_only=True)

        transformer.requires_grad_(False)
        vae.requires_grad_(False)
        text_encoder_one.requires_grad_(False)
        text_encoder_two.requires_grad_(False)

        # Construct pipeline
        pipeline = FluxPipelineWithGrads.from_pretrained(
            flux_model_root,
            vae=vae,
            text_encoder=accelerator.unwrap_model(text_encoder_one),
            text_encoder_2=accelerator.unwrap_model(text_encoder_two),
            transformer=accelerator.unwrap_model(transformer),
            torch_dtype=weight_dtype,
        )

        # Load LoRA weights
        pipeline.load_lora_weights(general_lora_path)

        # Load DINO and IR models
        dino, transforms_configs = get_model_and_transforms_configs("vit_large_patch14_dinov2.lvd142m")
        ir_feature_extractor, feature_extractor_transforms = get_ir_model_and_transforms(
            ir_features_path, device=accelerator.device
        )
        ir_feature_extractor.eval()

        _models = {
            "vae": vae,
            "transformer": transformer,
            "text_encoder_one": text_encoder_one,
            "text_encoder_two": text_encoder_two,
            "tokenizer_one": tokenizer_one,
            "tokenizer_two": tokenizer_two,
            "pipeline": pipeline,
            "dino": dino,
            "transforms_configs": transforms_configs,
            "ir_feature_extractor": ir_feature_extractor,
            "feature_extractor_transforms": feature_extractor_transforms,
        }
        _last_model_load_time = time.time()

    return _models

def load_inference_pipeline():
    print("Loading inference pipeline...")
    pipeline_inference = FluxPipeline.from_pretrained(flux_model_root, torch_dtype=torch.bfloat16).to("cuda")
    return pipeline_inference

if __name__ == "__main__":
    import time

    start = time.time()
    models = load_models()
    pipeline_inference = load_inference_pipeline()
    end = time.time()

    duration_minutes = (end - start) / 60
    print(f"✅ Models loaded successfully in {duration_minutes:.2f} minutes")
