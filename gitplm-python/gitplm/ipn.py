import re
from dataclasses import dataclass
from typing import Tuple, Optional

class IPNError(Exception):
    """IPN相关错误的基类"""
    pass

@dataclass
class IPN:
    """内部零件编号(Internal Part Number)类"""
    _value: str
    
    # 编译正则表达式
    _RE_IPN = re.compile(r'^([A-Z][A-Z][A-Z])-(\d{3})-(\d{4})$')
    _RE_C = re.compile(r'^[A-Z][A-Z][A-Z]$')
    
    # 定义有效的IPN类别
    _OUR_IPNS = {"PCA", "PCB", "ASY", "DOC", "DFW", "DSW", "DCL", "FIX"}
    _BOMS = {"PCA", "ASY"}
    
    def __init__(self, value: str):
        """
        初始化IPN
        
        Args:
            value: IPN字符串
            
        Raises:
            IPNError: 当IPN格式无效时抛出
        """
        self._value = value
        # 验证格式
        self.parse()
    
    @classmethod
    def from_parts(cls, category: str, number: int, variation: int) -> 'IPN':
        """
        从部件创建IPN
        
        Args:
            category: 类别代码（3个大写字母）
            number: 编号（0-999）
            variation: 变体号（0-9999）
            
        Returns:
            IPN实例
            
        Raises:
            IPNError: 当参数无效时抛出
        """
        if not (0 <= number <= 999):
            raise IPNError("Number out of range (0-999)")
        
        if not (0 <= variation <= 9999):
            raise IPNError("Variation out of range (0-9999)")
            
        if len(category) != 3 or not cls._RE_C.match(category):
            raise IPNError("Category must be 3 uppercase letters")
            
        value = f"{category}-{number:03d}-{variation:04d}"
        return cls(value)
    
    def parse(self) -> Tuple[str, int, int]:
        """
        解析IPN字符串
        
        Returns:
            元组 (category, number, variation)
            
        Raises:
            IPNError: 当IPN格式无效时抛出
        """
        match = self._RE_IPN.match(self._value)
        if not match:
            raise IPNError(f"Invalid IPN format: {self._value}")
            
        category = match.group(1)
        try:
            number = int(match.group(2))
            variation = int(match.group(3))
        except ValueError as e:
            raise IPNError(f"Error parsing numbers: {e}")
            
        return category, number, variation
    
    @property
    def category(self) -> str:
        """获取IPN类别"""
        return self.parse()[0]
    
    @property
    def number(self) -> int:
        """获取IPN编号"""
        return self.parse()[1]
    
    @property
    def variation(self) -> int:
        """获取IPN变体号"""
        return self.parse()[2]
    
    def is_our_ipn(self) -> bool:
        """检查是否是我们的IPN类别"""
        return self.category in self._OUR_IPNS
    
    def has_bom(self) -> bool:
        """检查是否有BOM（物料清单）"""
        return self.category in self._BOMS
    
    def __str__(self) -> str:
        return self._value
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IPN):
            return NotImplemented
        return self._value == other._value
    
    def __hash__(self) -> int:
        return hash(self._value) 