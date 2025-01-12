# GitPLM (Python Version)

![gitplm logo](../gitplm-logo.png)

## 基于 Git 的产品生命周期管理工具

GitPLM 是一个用于管理产品制造所需信息的工具和最佳实践集合。这是原
始[Go 版本](https://github.com/git-plm/gitplm)的 Python 实现。

**GitPLM 的核心理念是避免重复的手动操作。你只需要做一次，之后工具就会自动为你完
成。这就是 GitPLM 要解决的问题。**

GitPLM 的主要功能：

- 将源 BOM 与零件主数据（partmaster）结合，生成包含制造信息的 BOM
- 自动生成发布/制造信息
- 创建包含所有子装配件的组合 BOM
- 将设计中所有自制组件的发布数据收集到一个目录中，用于制造发布

## 最近更新

### 功能增强

1. BOM 处理改进

   - 优化了 BOM 行项目的添加和移除逻辑
   - 支持按组件名称或引用移除项目
   - 自动计算组件数量
   - 按 IPN 排序输出结果

2. 文件操作增强

   - 更安全的文件复制机制
   - 支持目录和文件的递归复制
   - 自动创建目标目录结构
   - 改进了文件覆盖处理逻辑

3. 钩子脚本功能增强

   - 增加了更多模板变量支持：
     - ${IPN}: 内部零件编号
     - ${SrcDir}: 源目录路径
     - ${RelDir}: 目标目录路径
     - ${Description}: 发布描述
   - 新增环境变量支持：
     - GITPLM_IPN: 内部零件编号
     - GITPLM_SRC_DIR: 源目录路径
     - GITPLM_REL_DIR: 目标目录路径
     - GITPLM_DESCRIPTION: 发布描述
   - 改进了跨平台兼容性
   - 实时日志输出支持

4. 错误处理改进
   - 更详细的错误信息
   - 改进了异常处理机制
   - 增加了必需文件检查功能

## 安装

### 从源码安装

```bash
git clone https://github.com/yourusername/gitplm-python.git
cd gitplm-python
pip install -r requirements.txt
python setup.py install
```

### 使用 pip 安装（待发布）

```bash
pip install gitplm
```

## 使用方法

GitPLM 提供以下主要命令：

```bash
# 处理发布版本
gitplm release PCB-056-0005

# 添加或更新零件主数据
gitplm add-part PCB-001-0001 -d "主控板" -f "PCBA" -v "V1.0" -m "ACME" --mpn "ABC123"

# 查看零件信息
gitplm show-part PCB-001-0001

# 检查BOM文件
gitplm check-bom PCB-001-0001.csv

# 查看版本
gitplm --version
```

## 钩子脚本示例

```yaml
description: 修改 BOM 并运行钩子
hooks:
  # 使用模板变量
  - echo "Processing ${IPN} (${Description})" > ${RelDir}/process.log

  # 使用环境变量
  - python scripts/generate_docs.py %GITPLM_IPN% %GITPLM_REL_DIR%
```

## 零件编号系统

每个用于制造产品的零件都由 IPN（内部零件编号）定义。GitPLM 使用的格式为
：`CCC-NNN-VVVV`

- `CCC`: 主要类别（RES 电阻, CAP 电容, DIO 二极管等）
- `NNN`: 每个零件的递增序列号
- `VVVV`: 变体编号，用于编码**具有相同数据手册**的零件变体（电阻值、电容值、稳压
  器电压、IC 封装等）。也用于编码自制零件或装配件的版本。

## 零件主数据（Partmaster）

整个组织使用单个 `partmaster.csv` 文件，其中包含用于构建产品的所有资产的内部零件
编号（IPN）。对于外购件，还包括制造商零件编号（MPN）等采购信息。

如果一个零件有多个供应商，可以使用相同的 IPN 添加多行，并指定不同的制造商
/MPN。GitPLM 会合并其他字段（如描述、值等），因此这些只需要在其中一行指定。使用
`Priority` 列选择首选零件（数字越小优先级越高）。

## 自制组件

产品通常是自制件和外购件的组合。自制件由以下 `CCC` 代码标识：

| 代码 | 描述                                                       |
| ---- | ---------------------------------------------------------- |
| PCA  | 印刷电路组件。当组件的 BOM 发生变化时，版本号递增。        |
| PCB  | 印刷电路板。标识裸板。                                     |
| ASY  | 装配件（可以是机械或顶层子装配 - 通常由 BOM 和文档表示）。 |
| DOC  | 独立文档                                                   |
| DFW  | 数据 - MCU 固件                                            |
| DSW  | 数据 - 软件（嵌入式 Linux 系统镜像、应用程序等）           |
| DCL  | 数据 - 设计校准数据                                        |
| FIX  | 制造夹具                                                   |

## 源文件和发布目录

对于自制件，GitPLM 通过以下文件识别源目录：

- 输入 BOM 文件。例如：`ASY-023.csv`
- 发布配置文件。例如：`PCB-019.yml`

发布目录由完整的 IPN 标识。例如：

- `PCA-019-0012`
- `ASY-012-0002`
- `DOC-055-0006`

## 特殊文件

以下文件如果在项目目录中存在，将被复制到发布目录：

- `MFG.md`: 包含制造注意事项
- `CHANGELOG.md`: 包含每个版本的变更列表

## 发布配置

源目录中的发布配置文件（`CCC-NNN.yml`）可用于自定义发布过程。文件格式为 YAML，示
例：

```yaml
remove:
  - cmpName: 测试点
  - ref: D12
add:
  - cmpName: "4号螺丝"
    ref: S3
    ipn: SCR-002-0002
copy:
  - gerber
  - mfg
  - pcb.schematic
required:
  - PCA-019-0002_ibom.html
```

## 原则

- 避免对机器生成的文件进行手动修改
- 使用声明式而不是命令式的方式定义更改
- 使用文本文件以便于 Git 工作流程中的审查
- 版本号应该经常递增
- PLM 软件不应该绑定到特定的 CAD 工具

## 许可证

MIT License
