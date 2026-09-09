import open_clip
from pathlib import Path
from typing import List,Optional,Dict,Any
import torch
from PIL import Image
from torchvision import transforms
from torch.utils import data
from crud import inquiry

class ClipModel:
    def __init__(self,config:Dict[str,Any]):
        weight_path=config["open_clip_weight"]
        device=config["device"]
        root=Path(__file__).parent.parent
        self.weight=root.joinpath(weight_path)
        cuda_available=torch.cuda.is_available()
        # 设备
        if device=="cuda":
            if cuda_available:
                self.device=torch.device(device)
            else:
                self.device=torch.device("cpu")
        else:
            self.device=torch.device(device)
    def load_clip_model(self):
        model, _, preprocess = open_clip.create_model_and_transforms(
            model_name="ViT-B-32",
            pretrained=str(self.weight),
        )
        return model,preprocess

class ClipDataset(data.Dataset):
    def __init__(self, images:List[str], transform:Optional[transforms.Compose]=None):
        super().__init__()
        self.images=images
        if transform is None:
            self.transform=transforms.ToTensor()
        else:
            self.transform=transform
    def __len__(self):
        return len(self.images)
    def __getitem__(self,item):
        image_path = self.images[item]
        image = Image.open(image_path).convert("RGB")
        image = self.transform(image)
        image = image.to(dtype=torch.float32)
        return image,image_path

if __name__=="__main__":
    config_file=Path(__file__).parent.parent.joinpath("config","config.yml")
    config=inquiry.load_config(config_file=config_file)
    clip_model=ClipModel(config=config)
    model,preprocess=clip_model.load_clip_model()
    images=["E:/pythonProject/ImageSearch/static/ciocan.jpg"]
    clip_dateset=ClipDataset(images=images,transform=preprocess)
    dataloader=data.DataLoader(clip_dateset,batch_size=2,shuffle=True,num_workers=2)
    for images, image_paths in dataloader:
        image_feature=model.encode_image(images)
        print(image_paths)