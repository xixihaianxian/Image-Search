from typing import Optional
import yaml
from loguru import logger

def load_config(config_file:Optional[str]):
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
        raise FileNotFoundError(f"Failed to get configuration!") from None