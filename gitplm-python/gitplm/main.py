import click
import logging
import os
import shutil
from pathlib import Path
from typing import Optional
import yaml
from .ipn import IPN, IPNError
from .bom import BOM, BOMLine
from .partmaster import Partmaster, PartmasterLine
from .release_script import ReleaseScript
from .file_utils import (
    find_file,
    load_yaml,
    save_yaml,
    load_csv_to_dict,
    save_dict_to_csv,
    ensure_directory,
    get_release_path
)

VERSION = "0.1.0"

def setup_logging(log_file: Optional[Path] = None):
    """设置日志配置"""
    format_str = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=format_str)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_str))
        logging.getLogger().addHandler(file_handler)

@click.group()
@click.version_option(version=VERSION)
def cli():
    """GitPLM - Git-based Product Lifecycle Management Tool"""
    pass

@cli.command()
@click.argument('release_id')
def release(release_id: str):
    """处理指定的发布版本"""
    try:
        # 解析IPN
        try:
            ipn = IPN(release_id)
        except IPNError as e:
            raise click.ClickException(f"Invalid IPN format: {e}")
            
        # 设置日志
        release_path = get_release_path(ipn)
        log_file = release_path / f"{ipn.category}-{ipn.number:03d}.log"
        setup_logging(log_file)
        
        # 处理发布
        logging.info(f"Processing release: {release_id}")
        process_release(ipn)
        logging.info(f"Release {release_id} updated")
        
    except Exception as e:
        logging.error(f"Error processing release {release_id}: {str(e)}")
        raise click.ClickException(str(e))

def process_release(ipn: IPN) -> Optional[Path]:
    """
    处理发布版本的核心逻辑
    
    Args:
        ipn: IPN实例
    
    Returns:
        Path: 发布文件的路径
        
    Raises:
        click.ClickException: 当处理过程中出现错误时
    """
    release_path = get_release_path(ipn)
    
    # 检查是否有BOM
    if not ipn.has_bom():
        logging.info(f"IPN {ipn} does not have a BOM")
        return release_path
        
    # 查找BOM文件
    bom_file = find_file(f"{ipn}.csv")
    if not bom_file:
        raise click.ClickException(f"BOM file not found for {ipn}")
        
    try:
        # 加载BOM
        bom = BOM.load_from_csv(bom_file)
        
        # 加载零件主数据
        partmaster_file = find_file("partmaster.csv")
        if partmaster_file:
            partmaster_data = load_csv_to_dict(partmaster_file)
            partmaster = Partmaster([
                PartmasterLine(
                    ipn=IPN(item['IPN']),
                    description=item['Description'],
                    footprint=item['Footprint'],
                    value=item['Value'],
                    manufacturer=item['Manufacturer'],
                    mpn=item['MPN'],
                    datasheet=item['Datasheet'],
                    priority=int(item.get('Priority', 0)),
                    checked=item['Checked']
                ) for item in partmaster_data
            ])
            
            # 合并零件主数据
            bom.merge_partmaster(partmaster, logging.error)
        
        # 查找并加载发布脚本
        script_file = find_file(f"{ipn.category}-{ipn.number:03d}.yml")
        if script_file:
            script_data = load_yaml(script_file)
            release_script = ReleaseScript.from_yaml(script_data)
            
            # 处理BOM
            bom = release_script.process_bom(bom)
            
            # 复制文件
            src_dir = script_file.parent
            release_script.copy_files(src_dir, release_path)
            
            # 运行钩子脚本
            release_script.run_hooks(str(ipn), src_dir, release_path)
            
            # 检查必需文件
            release_script.check_required(release_path)
        
        # 处理子装配
        bom.process_our_ipn(ipn, 1)
        
        # 保存处理后的BOM
        output_file = release_path / f"{ipn}.csv"
        bom.save_to_csv(output_file)
        
        # 复制特殊文件
        special_files = ['MFG.md', 'CHANGELOG.md']
        for file_name in special_files:
            src_file = find_file(file_name)
            if src_file:
                shutil.copy2(src_file, release_path / file_name)
        
        return release_path
        
    except Exception as e:
        raise click.ClickException(f"Error processing release: {e}")

@cli.command()
@click.argument('ipn')
@click.option('--description', '-d', help='零件描述')
@click.option('--footprint', '-f', help='封装类型')
@click.option('--value', '-v', help='值/规格')
@click.option('--manufacturer', '-m', help='制造商')
@click.option('--mpn', help='制造商零件编号')
@click.option('--datasheet', help='数据手册链接')
@click.option('--priority', type=int, default=0, help='优先级')
def add_part(ipn: str, **kwargs):
    """添加或更新零件主数据"""
    try:
        # 解析IPN
        part_ipn = IPN(ipn)
        
        # 加载现有的零件主数据
        partmaster_file = find_file("partmaster.csv")
        partmaster = Partmaster([])
        
        if partmaster_file:
            partmaster_data = load_csv_to_dict(partmaster_file)
            partmaster = Partmaster([
                PartmasterLine(
                    ipn=IPN(item['IPN']),
                    description=item['Description'],
                    footprint=item['Footprint'],
                    value=item['Value'],
                    manufacturer=item['Manufacturer'],
                    mpn=item['MPN'],
                    datasheet=item['Datasheet'],
                    priority=int(item.get('Priority', 0)),
                    checked=item.get('Checked', '')
                ) for item in partmaster_data
            ])
        
        # 创建新的零件数据
        new_part = PartmasterLine(
            ipn=part_ipn,
            description=kwargs.get('description', ''),
            footprint=kwargs.get('footprint', ''),
            value=kwargs.get('value', ''),
            manufacturer=kwargs.get('manufacturer', ''),
            mpn=kwargs.get('mpn', ''),
            datasheet=kwargs.get('datasheet', ''),
            priority=kwargs.get('priority', 0),
            checked=''
        )
        
        # 更新或添加零件
        try:
            partmaster.update_part(part_ipn, new_part)
        except:
            partmaster.add_part(new_part)
        
        # 保存更新后的零件主数据
        output_file = Path('partmaster.csv')
        fieldnames = [
            'IPN', 'Description', 'Footprint', 'Value',
            'Manufacturer', 'MPN', 'Datasheet', 'Priority', 'Checked'
        ]
        
        data = [{
            'IPN': str(part.ipn),
            'Description': part.description,
            'Footprint': part.footprint,
            'Value': part.value,
            'Manufacturer': part.manufacturer,
            'MPN': part.mpn,
            'Datasheet': part.datasheet,
            'Priority': part.priority,
            'Checked': part.checked
        } for part in partmaster.parts]
        
        save_dict_to_csv(data, output_file, fieldnames)
        click.echo(f"零件 {ipn} 已添加/更新到主数据")
        
    except Exception as e:
        raise click.ClickException(str(e))

@cli.command()
@click.argument('ipn')
def show_part(ipn: str):
    """显示零件主数据信息"""
    try:
        # 解析IPN
        part_ipn = IPN(ipn)
        
        # 加载零件主数据
        partmaster_file = find_file("partmaster.csv")
        if not partmaster_file:
            raise click.ClickException("未找到零件主数据文件")
            
        partmaster_data = load_csv_to_dict(partmaster_file)
        partmaster = Partmaster([
            PartmasterLine(
                ipn=IPN(item['IPN']),
                description=item['Description'],
                footprint=item['Footprint'],
                value=item['Value'],
                manufacturer=item['Manufacturer'],
                mpn=item['MPN'],
                datasheet=item['Datasheet'],
                priority=int(item.get('Priority', 0)),
                checked=item.get('Checked', '')
            ) for item in partmaster_data
        ])
        
        # 查找并显示零件信息
        try:
            part = partmaster.find_part(part_ipn)
            click.echo(f"IPN: {part.ipn}")
            click.echo(f"描述: {part.description}")
            click.echo(f"封装: {part.footprint}")
            click.echo(f"值/规格: {part.value}")
            click.echo(f"制造商: {part.manufacturer}")
            click.echo(f"MPN: {part.mpn}")
            click.echo(f"数据手册: {part.datasheet}")
            click.echo(f"优先级: {part.priority}")
            click.echo(f"检查状态: {part.checked}")
        except ValueError as e:
            raise click.ClickException(f"未找到零件: {e}")
            
    except Exception as e:
        raise click.ClickException(str(e))

@cli.command()
@click.argument('bom_file')
def check_bom(bom_file: str):
    """检查BOM文件的完整性和正确性"""
    try:
        # 加载BOM文件
        bom_path = Path(bom_file)
        if not bom_path.exists():
            raise click.ClickException(f"BOM文件不存在: {bom_file}")
            
        bom = BOM.load_from_csv(bom_path)
        
        # 加载零件主数据
        partmaster_file = find_file("partmaster.csv")
        if not partmaster_file:
            click.echo("警告: 未找到零件主数据文件，跳过零件验证")
            partmaster = None
        else:
            partmaster_data = load_csv_to_dict(partmaster_file)
            partmaster = Partmaster([
                PartmasterLine(
                    ipn=IPN(item['IPN']),
                    description=item['Description'],
                    footprint=item['Footprint'],
                    value=item['Value'],
                    manufacturer=item['Manufacturer'],
                    mpn=item['MPN'],
                    datasheet=item['Datasheet'],
                    priority=int(item.get('Priority', 0)),
                    checked=item.get('Checked', '')
                ) for item in partmaster_data
            ])
        
        # 检查项目
        errors = []
        warnings = []
        
        # 1. 检查每个IPN的有效性
        for line in bom.lines:
            try:
                if not line.ipn.is_our_ipn():
                    warnings.append(f"IPN {line.ipn} 不是内部IPN")
            except Exception as e:
                errors.append(f"无效的IPN格式 {line.ipn}: {e}")
        
        # 2. 检查零件主数据匹配
        if partmaster:
            for line in bom.lines:
                try:
                    part = partmaster.find_part(line.ipn)
                    if not part.checked:
                        warnings.append(f"零件 {line.ipn} 未经检查确认")
                except ValueError:
                    errors.append(f"零件 {line.ipn} 在主数据中未找到")
        
        # 3. 检查数量
        for line in bom.lines:
            if line.quantity <= 0:
                errors.append(f"零件 {line.ipn} 的数量无效: {line.quantity}")
        
        # 4. 检查必填字段
        for line in bom.lines:
            if not line.value:
                warnings.append(f"零件 {line.ipn} 缺少值/规格信息")
            if not line.description:
                warnings.append(f"零件 {line.ipn} 缺少描述信息")
        
        # 输出检查结果
        if errors:
            click.echo("\n错误:")
            for error in errors:
                click.echo(f"- {error}")
                
        if warnings:
            click.echo("\n警告:")
            for warning in warnings:
                click.echo(f"- {warning}")
                
        if not errors and not warnings:
            click.echo("BOM检查通过，未发现问题")
        elif not errors:
            click.echo("\nBOM检查完成，仅有警告")
        else:
            raise click.ClickException("BOM检查失败，存在错误")
            
    except Exception as e:
        raise click.ClickException(str(e))

if __name__ == '__main__':
    cli()
