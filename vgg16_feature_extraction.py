import matplotlib.pyplot as plt
import numpy as np
import torch
from torch import nn
from torchvision import models
import yaml
from loguru import logger
from typing import Optional,Tuple
from PIL import Image

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

# 构造特征获取函数
class FeatureModule(nn.Module):
    def __init__(self,base_module:nn.Module):
        """
        Args:
            base_module: 基础模型（图片特征提取模型）
        """
        super().__init__()
        # 获取模型特征提取部分
        try:
            self.feature_part=base_module.features
        except AttributeError:
            logger.error(f"The model doesn't have a feature extraction part!")
            raise None
        # 获取自适应平均池化，仅发出警告
        try:
            self.avgpool=base_module.avgpool
        except AttributeError:
            logger.warning(f"The model doesn't have a avgpool part!")
            self.avgpool = None
        self.avgpool_1x1=nn.AdaptiveAvgPool2d(output_size=(1,1))
        self.flatten=nn.Flatten(start_dim=1,end_dim=-1)
    def forward(self,x):
        feature=self.feature_part(x)
        if self.avgpool is not None:
            feature=self.avgpool(feature)
        # (batch_size,channels,n,n)->(batch_size,channels,1,1)
        result=self.avgpool_1x1(feature)
        # (batch_size,channels)
        result=self.flatten(result)
        return result

# Vgg16获取图片特征
class Vgg16FeatureExtractor:
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
        """
        登录vgg16模型
        """
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
    def feature_fetch_module(self,module:nn.Module):
        module=FeatureModule(base_module=module)
        module=module.to(device=self.device)
        return module
    def image_to_array(self,image_path:str,shape:Tuple[int,int]=(224,224))->torch.Tensor:
        image = Image.open(fp=image_path)
        image=image.resize(size=shape)
        image=np.array(image)
        # 转化为tensor张量
        image=torch.from_numpy(image)
        # 转置(height,width,channels)->(channels,height,width)
        image = image.permute(2,0,1)
        # 在dim=0上添加维度，作为batch_size
        image=image.unsqueeze(dim=0)
        # 转化图片数据类型
        image=image.to(dtype=torch.float32,device=self.device)
        return image
    def extract_feature(self,image:torch.Tensor):
        pass

if __name__=="__main__":
    vgg16_feature_extract=Vgg16FeatureExtractor(config_path="./config.yml")
    vgg16=models.vgg16(weights=None)
    feature=vgg16_feature_extract.feature_fetch_module(vgg16)
    img=vgg16_feature_extract.image_to_array(image_path="./ciocan.jpg")
    print(feature(img).shape)