import numpy as np
import torch
from torch import nn
from torchvision import models
import yaml
from loguru import logger
from typing import Optional

def load_config(config_file:str):
    """登录yaml配置文件
    Args:
        config_file: yaml配置文件的路径
    Returns:
        返回配置文件json数据
    """
    try:
        with open(config_file,"r",encoding="utf-8") as file:
            config=yaml.safe_load(file)
        return config
    except Exception as error:
        logger.error(f"Failed to get configuration!")
        raise None

class FeatureExtractor:
    def __init__(self,config_path:str):
        config = load_config(config_file=config_path)
        self.weight_path=config.get("weight_path",None)
        device = config.get("device")
        if device == "cuda":
            # 判断设备存不存在GPU
            if not torch.cuda.is_available():
                logger.warning(f"CUDA is not available, using CPU")
                self.device = torch.device(device="cpu")
        logger.info(f"Using device: {device}")
        self.device = torch.device(device=device)
    def load_vgg16(self):
        logger.info(f"Loading vgg16 model!")
        if self.weight_path is None:
            vgg16=models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_V1)
            return vgg16
        logger.info(f"Loading vgg16 model from {self.weight_path}")
        vgg16=models.vgg16(weights=None)
        # 从配置文件中获取权重路径
        vgg16_static_dict=torch.load(f=self.weight_path,weights_only=True)
        # 严格匹配
        vgg16.load_state_dict(state_dict=vgg16_static_dict,strict=True)
        logger.info(f"Loading vgg16 model successfully!")
        # 模型登录设备
        vgg16=vgg16.to(device=self.device)
        return vgg16
    def extract_feature(self,image:np.ndarray):
        pass

if __name__=="__main__":
    feature_extractor = FeatureExtractor(config_path="./config.yml")
    print(feature_extractor.load_vgg16())