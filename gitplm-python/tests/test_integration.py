import pytest
import yaml
import csv
from pathlib import Path
import tempfile
import shutil
from gitplm.ipn import IPN
from gitplm.bom import BOM, BOMLine
from gitplm.partmaster import Partmaster, PartmasterLine
from gitplm.release_script import ReleaseScript

def create_test_partmaster():
    """创建测试用的零件主数据"""
    return [
        PartmasterLine(
            ipn=IPN("CAP-000-1001"),
            description="1nF, 50V cap",
            value="1nF_50V",
            manufacturer="Bogus Caps, Inc",
            mpn="1234",
            priority=2
        ),
        PartmasterLine(
            ipn=IPN("CAP-000-1001"),
            description="1nF, 50V cap",
            footprint="Capacitor_SMD:C_0805_2012Metric",
            manufacturer="AVX",
            mpn="08055C102JAT2A",
            datasheet="http://datasheets.avx.com/X7RDielectric.pdf",
            priority=1,
            checked="Y"
        ),
        PartmasterLine(
            ipn=IPN("ASY-001-0000"),
            description="productA",
            value="productA",
            manufacturer="mycompany"
        )
    ]

def create_test_bom():
    """创建测试用的BOM"""
    return BOM([
        BOMLine(
            ipn=IPN("CAP-000-1001"),
            quantity=2,
            ref="C1, C2",
            value="1nF_50V",
            cmp_name="C_0805"
        ),
        BOMLine(
            ipn=IPN("ASY-001-0000"),
            quantity=1,
            ref="A1",
            value="productA",
            cmp_name="Assembly"
        )
    ])

def create_test_release_script():
    """创建测试用的发布脚本"""
    yaml_data = """
    description: 修改 BOM 并运行钩子
    remove:
      - cmp_name: Test point
      - ref: TP1
    add:
      - cmp_name: "screw #4,2"
        ref: S1
        ipn: SCR-002-0002
    copy:
      - MFG.md
      - CHANGELOG.md
    hooks:
      - echo "Processing ${IPN}" > ${RelDir}/process.log
    required:
      - MFG.md
    """
    return ReleaseScript.from_yaml(yaml.safe_load(yaml_data))

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_complete_workflow(temp_dir):
    """测试完整的工作流程"""
    # 创建测试数据
    partmaster = Partmaster(create_test_partmaster())
    bom = create_test_bom()
    script = create_test_release_script()
    
    # 创建源文件
    src_dir = temp_dir / "src"
    src_dir.mkdir()
    
    mfg_file = src_dir / "MFG.md"
    mfg_file.write_text("Manufacturing instructions")
    
    changelog_file = src_dir / "CHANGELOG.md"
    changelog_file.write_text("Version history")
    
    # 创建目标目录
    dest_dir = temp_dir / "dest"
    dest_dir.mkdir()
    
    # 处理 BOM
    bom.merge_partmaster(partmaster, lambda x: print(f"Warning: {x}"))
    processed_bom = script.process_bom(bom)
    
    # 验证 BOM 处理结果
    assert len(processed_bom.lines) == 3  # 原有2个 + 新增1个
    
    # 验证零件信息合并
    cap = next(line for line in processed_bom.lines if line.ipn == IPN("CAP-000-1001"))
    assert cap.manufacturer == "AVX"  # 使用优先级高的信息
    assert cap.mpn == "08055C102JAT2A"
    assert cap.datasheet == "http://datasheets.avx.com/X7RDielectric.pdf"
    assert cap.checked == "Y"
    
    # 复制文件
    script.copy_files(src_dir, dest_dir)
    
    # 验证文件复制
    assert (dest_dir / "MFG.md").exists()
    assert (dest_dir / "CHANGELOG.md").exists()
    assert (dest_dir / "MFG.md").read_text() == "Manufacturing instructions"
    
    # 运行钩子
    script.run_hooks("ASY-001-0000", src_dir, dest_dir)
    
    # 验证钩子执行结果
    assert (dest_dir / "process.log").exists()
    assert "Processing ASY-001-0000" in (dest_dir / "process.log").read_text()
    
    # 检查必需文件
    script.check_required(dest_dir)  # 不应该抛出异常 