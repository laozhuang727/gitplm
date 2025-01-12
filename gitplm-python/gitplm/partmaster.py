from dataclasses import dataclass
from typing import List, Optional
from .ipn import IPN

@dataclass
class PartmasterLine:
    """零件主数据行"""
    ipn: IPN
    description: str = ""
    footprint: str = ""
    value: str = ""
    manufacturer: str = ""
    mpn: str = ""
    datasheet: str = ""
    priority: int = 0
    checked: str = ""

class Partmaster:
    """零件主数据管理类"""
    def __init__(self, parts: List[PartmasterLine] = None):
        self.parts = parts or []

    def find_part(self, pn: IPN) -> Optional[PartmasterLine]:
        """
        查找具有最高优先级的零件
        
        Args:
            pn: 零件编号
            
        Returns:
            找到的零件信息，如果未找到则返回None
            
        Raises:
            ValueError: 当未找到零件时抛出
        """
        found = [part for part in self.parts if part.ipn == pn]
        
        if not found:
            raise ValueError(f"Part not found: {pn}")
            
        # 按优先级排序
        found.sort(key=lambda x: x.priority)
        
        if len(found) > 1:
            # 用其他项的非空值填充空字段
            main_part = found[0]
            for other_part in found[1:]:
                if not main_part.description and other_part.description:
                    main_part.description = other_part.description
                if not main_part.footprint and other_part.footprint:
                    main_part.footprint = other_part.footprint
                if not main_part.value and other_part.value:
                    main_part.value = other_part.value
                    
        return found[0]

    def add_part(self, part: PartmasterLine) -> None:
        """添加新的零件到主数据"""
        self.parts.append(part)

    def remove_part(self, pn: IPN) -> None:
        """从主数据中移除零件"""
        self.parts = [part for part in self.parts if part.ipn != pn]

    def update_part(self, pn: IPN, new_data: PartmasterLine) -> None:
        """
        更新零件信息
        
        Args:
            pn: 要更新的零件编号
            new_data: 新的零件数据
            
        Raises:
            ValueError: 当未找到零件时抛出
        """
        for i, part in enumerate(self.parts):
            if part.ipn == pn:
                self.parts[i] = new_data
                return
        raise ValueError(f"Part not found: {pn}") 