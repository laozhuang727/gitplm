import pytest
from gitplm.ipn import IPN, IPNError

@pytest.mark.parametrize("ipn_str,category,number,variation,is_valid", [
    ("PCB-001-0500", "PCB", 1, 500, True),
    ("ASY-200-1000", "ASY", 200, 1000, True),
    ("SY-200-1000", "", 0, 0, False),
    ("ASY-20-1000", "", 0, 0, False),
    ("ASY-200-100", "", 0, 0, False),
])
def test_ipn_parsing(ipn_str: str, category: str, number: int, variation: int, is_valid: bool):
    """测试IPN解析功能"""
    if is_valid:
        ipn = IPN(ipn_str)
        assert ipn.category == category
        assert ipn.number == number
        assert ipn.variation == variation
    else:
        with pytest.raises(IPNError):
            IPN(ipn_str)

def test_ipn_from_parts():
    """测试从部件创建IPN"""
    # 有效的IPN
    ipn = IPN.from_parts("PCB", 1, 500)
    assert str(ipn) == "PCB-001-0500"
    
    # 无效的类别
    with pytest.raises(IPNError):
        IPN.from_parts("PC", 1, 500)
    
    # 无效的编号
    with pytest.raises(IPNError):
        IPN.from_parts("PCB", 1000, 500)
    
    # 无效的变体号
    with pytest.raises(IPNError):
        IPN.from_parts("PCB", 1, 10000)

def test_ipn_properties():
    """测试IPN属性"""
    ipn = IPN("PCB-001-0500")
    assert ipn.is_our_ipn()
    assert not ipn.has_bom()
    
    ipn = IPN("ASY-200-1000")
    assert ipn.is_our_ipn()
    assert ipn.has_bom()
    
    ipn = IPN("XXX-001-0001")
    assert not ipn.is_our_ipn()
    assert not ipn.has_bom()

def test_ipn_equality():
    """测试IPN相等性比较"""
    ipn1 = IPN("PCB-001-0500")
    ipn2 = IPN("PCB-001-0500")
    ipn3 = IPN("PCB-001-0501")
    
    assert ipn1 == ipn2
    assert ipn1 != ipn3
    assert hash(ipn1) == hash(ipn2)
    assert hash(ipn1) != hash(ipn3) 