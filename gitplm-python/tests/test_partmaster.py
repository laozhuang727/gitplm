import pytest
from io import StringIO
import csv
from gitplm.ipn import IPN
from gitplm.partmaster import Partmaster, PartmasterLine

def create_test_csv():
    """创建测试用的CSV数据"""
    csv_data = [
        {
            'IPN': 'CAP-001-1001',
            'Description': 'superduper cap',
            'Value': '',
            'Manufacturer': 'CapsInc',
            'MPN': '10045',
            'Priority': '2',
            'Footprint': '',
            'Datasheet': '',
            'Checked': ''
        },
        {
            'IPN': 'CAP-001-1001',
            'Description': '',
            'Value': '10k',
            'Manufacturer': 'MaxCaps',
            'MPN': 'abc2322',
            'Priority': '1',
            'Footprint': '',
            'Datasheet': '',
            'Checked': ''
        },
        {
            'IPN': 'CAP-001-1002',
            'Description': '',
            'Value': '',
            'Manufacturer': 'MaxCaps',
            'MPN': 'abc2323',
            'Priority': '0',
            'Footprint': '',
            'Datasheet': '',
            'Checked': ''
        }
    ]
    return [PartmasterLine(
        ipn=IPN(item['IPN']),
        description=item['Description'],
        value=item['Value'],
        manufacturer=item['Manufacturer'],
        mpn=item['MPN'],
        priority=int(item['Priority']),
        footprint=item['Footprint'],
        datasheet=item['Datasheet'],
        checked=item['Checked']
    ) for item in csv_data]

def test_partmaster_find_part():
    """测试零件查找功能"""
    # 创建测试数据
    pm = Partmaster(create_test_csv())
    
    # 测试查找存在的零件
    part = pm.find_part(IPN("CAP-001-1001"))
    assert part.mpn == "abc2322"  # 应该返回优先级最高的零件
    assert part.description == "superduper cap"  # 应该合并描述
    assert part.value == "10k"  # 应该合并值
    
    # 测试查找另一个零件
    part = pm.find_part(IPN("CAP-001-1002"))
    assert part.mpn == "abc2323"
    
    # 测试查找不存在的零件
    with pytest.raises(ValueError):
        pm.find_part(IPN("CAP-001-1003"))

def test_partmaster_add_part():
    """测试添加零件功能"""
    pm = Partmaster()
    
    # 添加新零件
    new_part = PartmasterLine(
        ipn=IPN("CAP-001-1003"),
        description="Test Cap",
        value="100nF",
        manufacturer="TestCaps",
        mpn="TC100",
        priority=0
    )
    pm.add_part(new_part)
    
    # 验证添加是否成功
    found_part = pm.find_part(IPN("CAP-001-1003"))
    assert found_part.description == "Test Cap"
    assert found_part.value == "100nF"

def test_partmaster_update_part():
    """测试更新零件功能"""
    pm = Partmaster(create_test_csv())
    
    # 更新现有零件
    updated_part = PartmasterLine(
        ipn=IPN("CAP-001-1001"),
        description="Updated Cap",
        value="20k",
        manufacturer="NewCaps",
        mpn="NC100",
        priority=0
    )
    pm.update_part(IPN("CAP-001-1001"), updated_part)
    
    # 验证更新是否成功
    found_part = pm.find_part(IPN("CAP-001-1001"))
    assert found_part.description == "Updated Cap"
    assert found_part.value == "20k"
    assert found_part.manufacturer == "NewCaps"
    
    # 测试更新不存在的零件
    with pytest.raises(ValueError):
        pm.update_part(IPN("CAP-001-9999"), updated_part)

def test_partmaster_remove_part():
    """测试移除零件功能"""
    pm = Partmaster(create_test_csv())
    
    # 移除零件
    pm.remove_part(IPN("CAP-001-1001"))
    
    # 验证移除是否成功
    with pytest.raises(ValueError):
        pm.find_part(IPN("CAP-001-1001")) 