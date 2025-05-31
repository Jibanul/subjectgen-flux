import timm
import torch
import kornia.geometry.transform as KTF
import kornia.enhance as KE
from pathlib import Path


def get_model_and_transforms_configs(model_name: str):
    dino_model_path = Path(__file__).resolve().parents[3] / "models" / "dinov2.pth"
    # model = timm.create_model(model_name, pretrained=True, num_classes=0)
    model = timm.create_model(model_name, pretrained=False, num_classes=0)
    model.load_state_dict(torch.load(dino_model_path, map_location="cuda"))
    model = model.to("cuda")
    model.eval()
    data_config = timm.data.resolve_model_data_config(model)
    transforms = timm.data.create_transform(**data_config, is_training=False)

    transforms_resize_size = transforms.transforms[0].size
    transforms_center_crop_size = transforms.transforms[1].size
    transforms_normalize_mean = transforms.transforms[-1].mean.clone().detach()
    transforms_normalize_std = transforms.transforms[-1].std

    return model, {
        "resize_size": transforms_resize_size,
        "center_crop_size": transforms_center_crop_size,
        "normalize_mean": transforms_normalize_mean,
        "normalize_std": transforms_normalize_std,
    }


def prepare_for_dino(image, transforms_configs: dict = None):
    # print(f"Image shape BEFORE DINO transforms: {image.shape}")
    # print("prepare for dino", transforms_configs)
    image = KTF.resize(image, transforms_configs["resize_size"], "bicubic")
    # print("After resizing:", image.shape)
    image = KTF.center_crop(image, transforms_configs["center_crop_size"])
    #J: for some reason the center crop is not working properly. that's why for now.
    # if image.shape[2:] != transforms_configs["center_crop_size"]:
    #     image = KTF.resize(image, transforms_configs["center_crop_size"], interpolation="bicubic")
    # print("transforms_configs center crop", transforms_configs["center_crop_size"])
    # print("After center cropping:", image.shape)
    image = KE.normalize(
        image,
        torch.tensor(transforms_configs["normalize_mean"]),
        torch.tensor(transforms_configs["normalize_std"]),
    )
    # print(f"Image shape after DINO transforms: {image.shape}")
    return image


def get_dino_features(model, image):
    # print(f"Image shape: {image.shape}")
    features = model(image)
    return features


def get_dino_features_negative_mean_cos_sim(
    model,
    transforms_configs,
    query_image,
    key_images_features,
):
    cos_sims = []
    # if type of key_images_features is not list, convert it to a list
    if not isinstance(key_images_features, list):
        key_images_features = [key_images_features]
    key_images_features_clones = [
        key_images_features.detach().clone()
        for key_images_features in key_images_features
    ]
    query_image_inputs = prepare_for_dino(query_image, transforms_configs)
    query_image_features = get_dino_features(model, query_image_inputs)
    for key_image_features in key_images_features_clones:
        cos_sim = torch.nn.functional.cosine_similarity(
            query_image_features.squeeze(), key_image_features.squeeze(), dim=0
        )
        cos_sims.append(cos_sim)
    mean_cos_sim = torch.mean(torch.stack(cos_sims))
    return -mean_cos_sim
