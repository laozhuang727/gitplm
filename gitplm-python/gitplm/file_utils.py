import os
from pathlib import Path
from typing import Optional, List
import yaml
import csv
from .ipn import IPN

def find_file(filename: str, search_paths: List[Path] = None) -> Optional[Path]:
    """
    在指定路径中查找文件
    
    Args:
        filename: 要查找的文件名
        search_paths: 搜索路径列表，如果为None则使用当前目录
        
    Returns:
        找到的文件路径，如果未找到则返回None
    """
    if search_paths is None:
        search_paths = [Path.cwd()]
        
    for path in search_paths:
        file_path = path / filename
        if file_path.exists():
            return file_path
            
    return None

def load_yaml(file_path: Path) -> dict:
    """
    加载YAML文件
    
    Args:
        file_path: YAML文件路径
        
    Returns:
        YAML文件内容的字典
        
    Raises:
        FileNotFoundError: 当文件不存在时
        yaml.YAMLError: 当YAML解析错误时
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml(data: dict, file_path: Path) -> None:
    """
    保存数据到YAML文件
    
    Args:
        data: 要保存的数据
        file_path: YAML文件路径
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, default_flow_style=False)

def load_csv_to_dict(file_path: Path, delimiter: str = ';') -> List[dict]:
    """
    加载CSV文件到字典列表
    
    Args:
        file_path: CSV文件路径
        delimiter: CSV分隔符
        
    Returns:
        字典列表，每个字典代表一行数据
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return list(reader)

def save_dict_to_csv(data: List[dict], file_path: Path, fieldnames: List[str], delimiter: str = ';') -> None:
    """
    保存字典列表到CSV文件
    
    Args:
        data: 要保存的数据
        file_path: CSV文件路径
        fieldnames: CSV字段名列表
        delimiter: CSV分隔符
    """
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(data)

def ensure_directory(path: Path) -> None:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
    """
    path.mkdir(parents=True, exist_ok=True)

def get_release_path(ipn: IPN) -> Path:
    """
    获取发布文件的路径
    
    Args:
        ipn: IPN实例
        
    Returns:
        发布文件的路径
    """
    # 创建发布目录结构：category/number/variation
    release_path = Path('releases') / ipn.category / f"{ipn.number:03d}" / f"{ipn.variation:04d}"
    ensure_directory(release_path)
    return release_path 