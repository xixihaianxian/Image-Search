import torch
from torch.utils import data
from pathlib import Path
from typing import List,Tuple
from torchvision import transforms
from . import vgg16_feature_extraction
import numpy as np
from PIL import Image
from torch import nn
from torch.nn import functional as F

def collate_fn(batch):
    pass

# 创建dataset
class VggDataset(data.Dataset):
    def __init__(self,image_collection:List[str],need_transform:bool=True):
        super().__init__()
        self.image_collection=image_collection
        if need_transform:
            self.transform=transforms.Compose([
                transforms.Resize(size=224),
                transforms.CenterCrop(size=224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
            ])
        else:
            self.transform=transforms.Compose([
                transforms.ToTensor(),
            ])
    def __len__(self):
        return len(self.image_collection)
    def __getitem__(self,item):
        image_path=self.image_collection[item]
        image=Image.open(image_path).convert("RGB")
        image=self.transform(image)
        image=image.to(dtype=torch.float32)
        return image_path,image

class FeatureStripping(vgg16_feature_extraction.FeatureModule):
    def __init__(self,base_model:nn.Module):
        super().__init__(base_module=base_model)
    def forward(self,x):
        feature=self.feature_part(x)
        if self.avgpool is not None:
            feature=self.avgpool(feature)
        # (batch_size,channels,n,n)->(batch_size,channels,1,1)
        result=self.avgpool_1x1(feature)
        # (batch_size,channels)
        result=self.flatten(result)
        # normalize
        result=F.normalize(result,dim=1,p=2)
        return result

if __name__=="__main__":
    images=[
        r"E:\Pictures\壁纸\1697x981-px-Artifacts-black-brown-clothes-eyes-1855075-wallhere.com.jpg",
        r"E:\Pictures\壁纸\20220408235839_f8d98.jpeg",
        r"E:\Pictures\壁纸\96yottea-anime-anime-girls-2302816-wallhere.com.jpg",
        r"E:\Pictures\壁纸\96yottea-anime-anime-girls-2302834-wallhere.com.jpg",
    ]
    dataset=VggDataset(images)
    dataloader=data.DataLoader(dataset=dataset,batch_size=2)
    for item in dataloader:
        print(item)