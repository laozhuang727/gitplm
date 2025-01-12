import pytest
from gitplm.ipn import IPN
from gitplm.bom import BOM, BOMLine
from gitplm.partmaster import Partmaster, PartmasterLine

def test_bom_line_creation():
    """测试 BOM 行项目的创建"""
    line = BOMLine(
        ipn=IPN("CAP-001-1001"),
        quantity=2,
        ref="C1, C2",
        value="1nF_50V",
        cmp_name="C_0805",
        manufacturer="AVX",
        mpn="08055C102JAT2A",
        datasheet="http://datasheets.avx.com/X7RDielectric.pdf"
    )
    
    assert str(line.ipn) == "CAP-001-1001"
    assert line.quantity == 2
    assert line.ref == "C1, C2"
    assert line.value == "1nF_50V"
    assert line.cmp_name == "C_0805"
    assert line.manufacturer == "AVX"
    assert line.mpn == "08055C102JAT2A"
    assert line.datasheet == "http://datasheets.avx.com/X7RDielectric.pdf"

def test_bom_creation():
    """测试 BOM 的创建和基本操作"""
    lines = [
        BOMLine(
            ipn=IPN("CAP-001-1001"),
            quantity=2,
            ref="C1, C2",
            value="1nF_50V",
            cmp_name="C_0805"
        ),
        BOMLine(
            ipn=IPN("RES-001-1001"),
            quantity=1,
            ref="R1",
            value="10K",
            cmp_name="R_0805"
        )
    ]
    
    bom = BOM(lines)
    assert len(bom.lines) == 2
    
    # 测试获取特定 IPN 的行项目
    cap_lines = bom.get_lines_by_ipn(IPN("CAP-001-1001"))
    assert len(cap_lines) == 1
    assert cap_lines[0].ref == "C1, C2"

def test_bom_merge_partmaster():
    """测试 BOM 与零件主数据的合并"""
    # 创建 BOM
    bom = BOM([
        BOMLine(
            ipn=IPN("CAP-001-1001"),
            quantity=2,
            ref="C1, C2",
            value="1nF_50V",
            cmp_name="C_0805"
        )
    ])
    
    # 创建零件主数据
    partmaster = Partmaster([
        PartmasterLine(
            ipn=IPN("CAP-001-1001"),
            description="1nF, 50V cap",
            value="1nF_50V",
            manufacturer="AVX",
            mpn="08055C102JAT2A",
            datasheet="http://datasheets.avx.com/X7RDielectric.pdf",
            priority=1
        )
    ])
    
    # 合并数据
    warnings = []
    bom.merge_partmaster(partmaster, lambda x: warnings.append(x))
    
    # 验证合并结果
    merged_line = bom.lines[0]
    assert merged_line.manufacturer == "AVX"
    assert merged_line.mpn == "08055C102JAT2A"
    assert merged_line.datasheet == "http://datasheets.avx.com/X7RDielectric.pdf"
    assert len(warnings) == 0  # 没有警告

def test_bom_merge_warnings():
    """测试 BOM 合并时的警告情况"""
    # 创建 BOM，使用不存在的 IPN
    bom = BOM([
        BOMLine(
            ipn=IPN("CAP-001-9999"),  # 不存在的 IPN
            quantity=1,
            ref="C1",
            value="1nF",
            cmp_name="C_0805"
        )
    ])
    
    # 创建零件主数据
    partmaster = Partmaster([
        PartmasterLine(
            ipn=IPN("CAP-001-1001"),
            description="1nF cap",
            manufacturer="AVX",
            priority=1
        )
    ])
    
    # 合并数据
    warnings = []
    bom.merge_partmaster(partmaster, lambda x: warnings.append(x))
    
    # 验证是否产生警告
    assert len(warnings) == 1
    assert "CAP-001-9999" in warnings[0]  # 警告中应包含未找到的 IPN 