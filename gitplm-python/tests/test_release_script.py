import pytest
import yaml
from pathlib import Path
import tempfile
import shutil
import os
from gitplm.ipn import IPN
from gitplm.bom import BOM, BOMLine
from gitplm.release_script import ReleaseScript

YAML_DATA = """
description: modify bom
remove:
  - cmp_name: Test point 2
  - ref: D13
  - ref: R11
add:
  - cmp_name: "screw #4,2"
    ref: S3
    ipn: SCR-002-0002
copy:
  - test_file.txt
hooks:
  - echo "Test hook for ${IPN} (${Description})" > ${RelDir}/hook_output.txt
  - echo %GITPLM_IPN% > ${RelDir}/env_output.txt
required:
  - test_file.txt
"""

def create_test_bom():
    """创建测试用的BOM"""
    return BOM([
        BOMLine(
            ipn=IPN("RES-006-0232"),
            quantity=2,
            value="100K_100mw",
            ref="R1, R2",
            cmp_name="100K_100mw"
        ),
        BOMLine(
            ipn=IPN("DIO-023-0023"),
            quantity=4,
            ref="D1, D2, D13, D14",
            cmp_name="diode"
        ),
        BOMLine(
            ipn=IPN("TST-001-0001"),
            quantity=2,
            ref="TP4, TP5",
            cmp_name="Test point 2"
        ),
        BOMLine(
            ipn=IPN("RES-008-1005"),
            quantity=1,
            value="2010_500mW_1%_3000V_10M",
            ref="R11",
            cmp_name="2010_500mW_1%_3000V_10M",
            footprint="Resistor_SMD:R_2010_5025Metric",
            datasheet="https://www.bourns.com/docs/Product-Datasheets/CHV.pdf"
        )
    ])

def test_release_script_process_bom():
    """测试BOM处理功能"""
    # 创建测试数据
    script_data = yaml.safe_load(YAML_DATA)
    script = ReleaseScript.from_yaml(script_data)
    bom = create_test_bom()
    
    # 处理BOM
    result = script.process_bom(bom)
    
    # 验证结果
    assert len(result.lines) == 3  # 应该有3个项目
    
    # 验证移除操作
    assert not any(line.cmp_name == "Test point 2" for line in result.lines)
    assert not any("D13" in line.ref for line in result.lines)
    assert not any("R11" in line.ref for line in result.lines)
    
    # 验证添加操作
    screw = next(line for line in result.lines if line.ipn == IPN("SCR-002-0002"))
    assert screw.cmp_name == "screw #4,2"
    assert screw.ref == "S3"
    assert screw.quantity == 1

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_release_script_copy_files(temp_dir):
    """测试文件复制功能"""
    # 创建测试数据
    script_data = yaml.safe_load(YAML_DATA)
    script = ReleaseScript.from_yaml(script_data)
    
    # 创建源文件
    src_dir = temp_dir / "src"
    src_dir.mkdir()
    test_file = src_dir / "test_file.txt"
    test_file.write_text("test content")
    
    # 创建目标目录
    dest_dir = temp_dir / "dest"
    dest_dir.mkdir()
    
    # 复制文件
    script.copy_files(src_dir, dest_dir)
    
    # 验证结果
    assert (dest_dir / "test_file.txt").exists()
    assert (dest_dir / "test_file.txt").read_text() == "test content"

def test_release_script_run_hooks(temp_dir):
    """测试钩子脚本执行功能"""
    # 创建测试数据
    script_data = yaml.safe_load(YAML_DATA)
    script = ReleaseScript.from_yaml(script_data)
    
    # 执行钩子
    script.run_hooks(
        "PCB-001-0001",
        temp_dir / "src",
        temp_dir / "dest"
    )
    
    # 验证结果
    hook_output = temp_dir / "dest" / "hook_output.txt"
    env_output = temp_dir / "dest" / "env_output.txt"
    assert hook_output.exists()
    assert env_output.exists()
    assert "Test hook for PCB-001-0001 (modify bom)" in hook_output.read_text()
    assert "PCB-001-0001" in env_output.read_text()

def test_release_script_check_required(temp_dir):
    """测试必需文件检查功能"""
    # 创建测试数据
    script_data = yaml.safe_load(YAML_DATA)
    script = ReleaseScript.from_yaml(script_data)
    
    # 测试缺少文件时
    with pytest.raises(FileNotFoundError):
        script.check_required(temp_dir)
    
    # 创建必需文件
    test_file = temp_dir / "test_file.txt"
    test_file.write_text("test content")
    
    # 测试文件存在时
    script.check_required(temp_dir)  # 不应该抛出异常 