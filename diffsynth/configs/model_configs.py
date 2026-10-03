qwen_image_series = [
    {
        # Example: ModelConfig(model_id="Qwen/Qwen-Image", origin_file_pattern="text_encoder/model*.safetensors")
        "model_hash": "0319a1cb19835fb510907dd3367c95ff",
        "model_name": "qwen_image_dit",
        "model_class": "diffsynth.models.qwen_image_dit.QwenImageDiT",
    },
    {
        # Example: ModelConfig(model_id="Qwen/Qwen-Image", origin_file_pattern="transformer/diffusion_pytorch_model*.safetensors")
        "model_hash": "8004730443f55db63092006dd9f7110e",
        "model_name": "qwen_image_text_encoder",
        "model_class": "diffsynth.models.qwen_image_text_encoder.QwenImageTextEncoder",
        "state_dict_converter": "diffsynth.utils.state_dict_converters.qwen_image_text_encoder.QwenImageTextEncoderStateDictConverter",
    },
    {
        # Example: ModelConfig(model_id="Qwen/Qwen-Image", origin_file_pattern="vae/diffusion_pytorch_model.safetensors")
        "model_hash": "ed4ea5824d55ec3107b09815e318123a",
        "model_name": "qwen_image_vae",
        "model_class": "diffsynth.models.qwen_image_vae.QwenImageVAE",
    },
    {
        # Example: ModelConfig(model_id="DiffSynth-Studio/Qwen-Image-Blockwise-ControlNet-Depth", origin_file_pattern="model.safetensors")
        "model_hash": "073bce9cf969e317e5662cd570c3e79c",
        "model_name": "qwen_image_blockwise_controlnet",
        "model_class": "diffsynth.models.qwen_image_controlnet.QwenImageBlockWiseControlNet",
    },
    {
        # Example: ModelConfig(model_id="DiffSynth-Studio/Qwen-Image-Blockwise-ControlNet-Inpaint", origin_file_pattern="model.safetensors")
        "model_hash": "a9e54e480a628f0b956a688a81c33bab",
        "model_name": "qwen_image_blockwise_controlnet",
        "model_class": "diffsynth.models.qwen_image_controlnet.QwenImageBlockWiseControlNet",
        "extra_kwargs": {"additional_in_dim": 4},
    },
    {
        # Example: ModelConfig(model_id="DiffSynth-Studio/General-Image-Encoders", origin_file_pattern="SigLIP2-G384/model.safetensors")
        "model_hash": "469c78b61e3e31bc9eec0d0af3d3f2f8",
        "model_name": "siglip2_image_encoder",
        "model_class": "diffsynth.models.siglip2_image_encoder.Siglip2ImageEncoder",
    },
    {
        # Example: ModelConfig(model_id="DiffSynth-Studio/General-Image-Encoders", origin_file_pattern="DINOv3-7B/model.safetensors")
        "model_hash": "5722b5c873720009de96422993b15682",
        "model_name": "dinov3_image_encoder",
        "model_class": "diffsynth.models.dinov3_image_encoder.DINOv3ImageEncoder",
    },
    {
        "model_hash": "a166c33455cdbd89c0888a3645ca5c0f",
        "model_name": "qwen_image_image2lora_coarse",
        "model_class": "diffsynth.models.qwen_image_image2lora.QwenImageImage2LoRAModel",
    },
    {
        "model_hash": "a5476e691767a4da6d3a6634a10f7408",
        "model_name": "qwen_image_image2lora_fine",
        "model_class": "diffsynth.models.qwen_image_image2lora.QwenImageImage2LoRAModel",
        "extra_kwargs": {"residual_length": 37*37+7, "residual_mid_dim": 64}
    },
    {
        "model_hash": "0aad514690602ecaff932c701cb4b0bb",
        "model_name": "qwen_image_image2lora_style",
        "model_class": "diffsynth.models.qwen_image_image2lora.QwenImageImage2LoRAModel",
        "extra_kwargs": {"compress_dim": 64, "use_residual": False}
    },
    {
        # Example: ModelConfig(model_id="Qwen/Qwen-Image-Layered", origin_file_pattern="transformer/diffusion_pytorch_model*.safetensors")
        "model_hash": "8dc8cda05de16c73afa755e2c1ce2839",
        "model_name": "qwen_image_dit",
        "model_class": "diffsynth.models.qwen_image_dit.QwenImageDiT",
        "extra_kwargs": {"use_layer3d_rope": True, "use_additional_t_cond": True}
    },
    {
        # Example: ModelConfig(model_id="Qwen/Qwen-Image-Layered", origin_file_pattern="vae/diffusion_pytorch_model.safetensors")
        "model_hash": "44b39ddc499e027cfb24f7878d7416b9",
        "model_name": "qwen_image_vae",
        "model_class": "diffsynth.models.qwen_image_vae.QwenImageVAE",
        "extra_kwargs": {"image_channels": 4}
    },
]

MODEL_CONFIGS = qwen_image_series
