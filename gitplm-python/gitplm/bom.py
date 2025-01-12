from dataclasses import dataclass
from typing import List, Callable, Optional
import csv
import logging
from pathlib import Path
from .ipn import IPN
from .partmaster import Partmaster, PartmasterLine

@dataclass
class BOMLine:
    """BOM行项目"""
    ipn: IPN
    quantity: int = 0
    mpn: str = ""
    manufacturer: str = ""
    ref: str = ""
    value: str = ""
    cmp_name: str = ""
    footprint: str = ""
    description: str = ""
    vendor: str = ""
    datasheet: str = ""
    checked: str = ""
    
    def __str__(self) -> str:
        """返回BOM行的字符串表示"""
        return ";".join([
            self.ref,
            str(self.quantity),
            self.value,
            self.cmp_name,
            self.footprint,
            self.description,
            self.vendor,
            str(self.ipn),
            self.datasheet,
            self.manufacturer,
            self.mpn,
            self.checked
        ])
    
    def remove_ref(self, ref: str) -> None:
        """移除指定的引用"""
        refs = [r.strip() for r in self.ref.split(",") if r.strip() and r.strip() != ref]
        self.ref = ", ".join(refs)
        self.quantity = len(refs)

class BOM:
    """BOM（物料清单）管理类"""
    def __init__(self, lines: List[BOMLine] = None):
        self.lines = lines or []
    
    def __str__(self) -> str:
        """返回整个BOM的字符串表示"""
        return "\n".join(str(line) for line in self.lines)
    
    def merge_partmaster(self, partmaster: Partmaster, log_error: Callable[[str], None]) -> None:
        """
        将partmaster的属性合并到BOM中
        
        Args:
            partmaster: Partmaster实例
            log_error: 错误日志记录函数
        """
        for i, line in enumerate(self.lines):
            try:
                pm_part = partmaster.find_part(line.ipn)
                line.manufacturer = pm_part.manufacturer
                line.mpn = pm_part.mpn
                line.datasheet = pm_part.datasheet
                line.checked = pm_part.checked
                line.description = pm_part.description
            except ValueError as e:
                log_error(f"Error finding part ({line.cmp_name}:{line.ipn}) on bom line #{i+2} in pm: {e}")
    
    def copy(self) -> 'BOM':
        """创建BOM的深拷贝"""
        from copy import deepcopy
        return BOM([deepcopy(line) for line in self.lines])
    
    def process_our_ipn(self, pn: IPN, qty: int) -> None:
        """
        处理我们的IPN
        
        Args:
            pn: IPN实例
            qty: 数量
            
        Raises:
            FileNotFoundError: 当找不到BOM文件时
            ValueError: 当处理过程中出现错误时
        """
        logging.info(f"Processing our IPN: {pn} {qty}")
        
        # 查找BOM文件
        bom_path = self._find_bom_file(pn)
        if not bom_path:
            raise FileNotFoundError(f"Error finding sub assy BOM for {pn}")
        
        # 加载子BOM
        sub_bom = self.load_from_csv(bom_path)
        
        # 处理子BOM中的每一行
        for line in sub_bom.lines:
            if line.ipn.has_bom():
                self.process_our_ipn(line.ipn, line.quantity * qty)
            
            new_line = BOMLine(
                ipn=line.ipn,
                quantity=line.quantity * qty,
                mpn=line.mpn,
                manufacturer=line.manufacturer,
                value=line.value,
                cmp_name=line.cmp_name,
                footprint=line.footprint,
                description=line.description,
                vendor=line.vendor,
                datasheet=line.datasheet,
                checked=line.checked
            )
            self.add_item(new_line)
    
    def add_item(self, new_item: BOMLine) -> None:
        """
        添加新的BOM行项目
        
        Args:
            new_item: 新的BOM行
        """
        for i, line in enumerate(self.lines):
            if new_item.ipn == line.ipn:
                self.lines[i].quantity += new_item.quantity
                return
        
        new_item.ref = ""  # 清除引用
        self.lines.append(new_item)
    
    @staticmethod
    def load_from_csv(file_path: Path) -> 'BOM':
        """
        从CSV文件加载BOM
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            BOM实例
        """
        lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                line = BOMLine(
                    ipn=IPN(row['IPN']),
                    quantity=int(row['Qnty']),
                    mpn=row['MPN'],
                    manufacturer=row['Manufacturer'],
                    ref=row['Ref'],
                    value=row['Value'],
                    cmp_name=row['Cmp name'],
                    footprint=row['Footprint'],
                    description=row['Description'],
                    vendor=row['Vendor'],
                    datasheet=row['Datasheet'],
                    checked=row['Checked']
                )
                lines.append(line)
        return BOM(lines)
    
    def save_to_csv(self, file_path: Path) -> None:
        """
        保存BOM到CSV文件
        
        Args:
            file_path: CSV文件路径
        """
        fieldnames = [
            'IPN', 'Qnty', 'MPN', 'Manufacturer', 'Ref', 'Value',
            'Cmp name', 'Footprint', 'Description', 'Vendor',
            'Datasheet', 'Checked'
        ]
        
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for line in sorted(self.lines, key=lambda x: str(x.ipn)):
                writer.writerow({
                    'IPN': str(line.ipn),
                    'Qnty': line.quantity,
                    'MPN': line.mpn,
                    'Manufacturer': line.manufacturer,
                    'Ref': line.ref,
                    'Value': line.value,
                    'Cmp name': line.cmp_name,
                    'Footprint': line.footprint,
                    'Description': line.description,
                    'Vendor': line.vendor,
                    'Datasheet': line.datasheet,
                    'Checked': line.checked
                })
    
    @staticmethod
    def _find_bom_file(pn: IPN) -> Optional[Path]:
        """
        查找BOM文件
        
        Args:
            pn: IPN实例
            
        Returns:
            找到的文件路径，如果未找到则返回None
        """
        # 在以下位置查找BOM文件：
        # 1. 当前目录
        # 2. releases目录下对应的IPN目录
        # 3. bom目录
        search_paths = [
            Path.cwd(),
            Path('releases') / pn.category / f"{pn.number:03d}" / f"{pn.variation:04d}",
            Path('bom')
        ]
        
        # 尝试不同的文件名格式
        file_names = [
            f"{pn}.csv",
            f"{pn.category}-{pn.number:03d}-{pn.variation:04d}.csv",
            f"{pn.category}{pn.number:03d}{pn.variation:04d}.csv"
        ]
        
        for path in search_paths:
            if path.exists():
                for name in file_names:
                    file_path = path / name
                    if file_path.exists():
                        return file_path
        
        return None 