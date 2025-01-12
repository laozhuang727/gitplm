import os
import shutil
import logging
import subprocess
from pathlib import Path
from typing import List, Optional
from string import Template
from .bom import BOM, BOMLine
from .ipn import IPN

class ReleaseScript:
    """发布脚本类，用于处理发布过程中的各种操作"""
    
    def __init__(self, 
                 description: str = "",
                 remove: List[BOMLine] = None,
                 add: List[BOMLine] = None,
                 copy: List[str] = None,
                 hooks: List[str] = None,
                 required: List[str] = None):
        """
        初始化发布脚本
        
        Args:
            description: 描述信息
            remove: 要移除的BOM行列表
            add: 要添加的BOM行列表
            copy: 要复制的文件/目录列表
            hooks: 要执行的钩子脚本列表
            required: 必需文件列表
        """
        self.description = description
        self.remove = remove or []
        self.add = add or []
        self.copy = copy or []
        self.hooks = hooks or []
        self.required = required or []
    
    def process_bom(self, bom: BOM) -> BOM:
        """
        处理BOM，执行添加和移除操作
        
        Args:
            bom: 要处理的BOM
            
        Returns:
            处理后的BOM
            
        Raises:
            ValueError: 当处理过程出错时
        """
        result = bom.copy()
        
        # 处理移除操作
        for remove_item in self.remove:
            if remove_item.cmp_name:
                # 移除指定组件名的行
                result.lines = [
                    line for line in result.lines 
                    if line.cmp_name != remove_item.cmp_name
                ]
            
            if remove_item.ref:
                # 移除指定引用
                for line in result.lines:
                    line.remove_ref(remove_item.ref)
                # 移除数量为0的行
                result.lines = [
                    line for line in result.lines 
                    if line.quantity > 0
                ]
        
        # 处理添加操作
        for add_item in self.add:
            # 创建新的BOMLine实例以避免修改原始数据
            new_item = BOMLine(
                ipn=add_item.ipn,
                ref=add_item.ref,
                cmp_name=add_item.cmp_name,
                value=add_item.value,
                footprint=add_item.footprint,
                description=add_item.description,
                vendor=add_item.vendor,
                datasheet=add_item.datasheet,
                manufacturer=add_item.manufacturer,
                mpn=add_item.mpn,
                checked=add_item.checked
            )
            # 设置数量
            refs = [r.strip() for r in new_item.ref.split(",") if r.strip()]
            new_item.quantity = len(refs) if refs else 1
            result.lines.append(new_item)
        
        # 按IPN排序
        result.lines.sort(key=lambda x: str(x.ipn))
        
        return result
    
    def copy_files(self, src_dir: Path, dest_dir: Path) -> None:
        """
        复制文件和目录
        
        Args:
            src_dir: 源目录
            dest_dir: 目标目录
            
        Raises:
            FileNotFoundError: 当源文件不存在时
            OSError: 当复制操作失败时
        """
        for item in self.copy:
            src_path = src_dir / item
            dest_path = dest_dir / item
            
            if not src_path.exists():
                raise FileNotFoundError(f"Source not found: {src_path}")
                
            if src_path.is_dir():
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                shutil.copytree(src_path, dest_path, symlinks=True)
            else:
                # 确保目标目录存在
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                # 如果目标文件存在，先删除它
                if dest_path.exists():
                    dest_path.unlink()
                shutil.copy2(src_path, dest_path)
                
            logging.info(f"{item} copied to release directory")
    
    def run_hooks(self, ipn: str, src_dir: Path, dest_dir: Path) -> None:
        """
        执行钩子脚本
        
        Args:
            ipn: IPN字符串
            src_dir: 源目录
            dest_dir: 目标目录
            
        Raises:
            subprocess.SubprocessError: 当脚本执行失败时
        """
        # 确保目标目录存在
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # 准备环境变量
        env = os.environ.copy()
        env.update({
            'GITPLM_IPN': ipn,
            'GITPLM_SRC_DIR': str(src_dir).replace('\\', '/'),
            'GITPLM_REL_DIR': str(dest_dir).replace('\\', '/'),
            'GITPLM_DESCRIPTION': self.description
        })
        
        template_data = {
            'SrcDir': str(src_dir).replace('\\', '/'),
            'RelDir': str(dest_dir).replace('\\', '/'),
            'IPN': ipn,
            'Description': self.description
        }
        
        for hook in self.hooks:
            # 处理模板
            template = Template(hook)
            try:
                command = template.substitute(template_data)
            except KeyError as e:
                logging.error(f"Error parsing hook template: {e}")
                continue
                
            # 执行命令
            try:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env
                )
                
                # 实时输出日志
                while True:
                    stdout_line = process.stdout.readline()
                    stderr_line = process.stderr.readline()
                    
                    if stdout_line:
                        logging.info(stdout_line.strip())
                    if stderr_line:
                        logging.error(stderr_line.strip())
                        
                    if not stdout_line and not stderr_line and process.poll() is not None:
                        break
                        
                if process.returncode != 0:
                    logging.error(f"Hook failed with return code {process.returncode}")
                    logging.error(f"Hook contents:\n{command}")
                    raise subprocess.SubprocessError(f"Hook failed with return code {process.returncode}")
                    
            except subprocess.SubprocessError as e:
                logging.error(f"Error running hook: {e}")
                logging.error(f"Hook contents:\n{command}")
                raise
    
    def check_required(self, dest_dir: Path) -> None:
        """
        检查必需文件是否存在
        
        Args:
            dest_dir: 目标目录
            
        Raises:
            FileNotFoundError: 当必需文件不存在时
        """
        for required_file in self.required:
            file_path = dest_dir / required_file
            if not file_path.exists():
                raise FileNotFoundError(
                    f"Required file does not exist, please generate it: {file_path}"
                )
    
    @staticmethod
    def _create_bom_line(data: dict) -> BOMLine:
        """
        从字典创建BOMLine实例
        
        Args:
            data: 包含BOM行数据的字典
            
        Returns:
            BOMLine实例
            
        Note:
            如果字典中没有提供ipn，则返回一个只包含必要字段的BOMLine
        """
        if 'ipn' in data:
            data['ipn'] = IPN(data['ipn'])
            return BOMLine(**data)
        else:
            # 对于remove操作，我们只需要ref或cmp_name字段
            return BOMLine(
                ipn=IPN("TMP-000-0000"),  # 使用有效的IPN格式作为占位符
                ref=data.get('ref', ''),
                cmp_name=data.get('cmp_name', '')
            )
    
    @classmethod
    def from_yaml(cls, yaml_data: dict) -> 'ReleaseScript':
        """
        从YAML数据创建ReleaseScript实例
        
        Args:
            yaml_data: YAML数据字典
            
        Returns:
            ReleaseScript实例
        """
        return cls(
            description=yaml_data.get('description', ''),
            remove=[cls._create_bom_line(item) for item in yaml_data.get('remove', [])],
            add=[cls._create_bom_line(item) for item in yaml_data.get('add', [])],
            copy=yaml_data.get('copy', []),
            hooks=yaml_data.get('hooks', []),
            required=yaml_data.get('required', [])
        ) 