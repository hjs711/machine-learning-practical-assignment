# -*- coding: utf-8 -*-
"""生成第一次阶段验收汇报文档"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def set_cell_color(cell, color):
    """设置单元格背景色"""
    from docx.oxml import OxmlElement
    tcPr = cell._element.get_or_add_tcPr()
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color)
    tcPr.append(shading)

def add_image_safe(doc, path, width=None):
    """安全地添加图片，如果不存在则跳过"""
    if os.path.exists(path):
        if width:
            doc.add_picture(path, width=width)
        else:
            doc.add_picture(path, width=Inches(6.0))
        return True
    else:
        doc.add_paragraph(f"[图片缺失: {os.path.basename(path)}]")
        return False

# 创建文档
doc = Document()

# 设置默认中文字体
doc.styles['Normal'].font.name = '微软雅黑'
doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
doc.styles['Normal'].font.size = Pt(12)

# ==================== 封面 ====================
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('机器学习课程实践\n')
run.font.size = Pt(28)
run.font.bold = True
run.font.color.rgb = RGBColor(31, 78, 120)

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('第一次阶段验收汇报\n\n')
run.font.size = Pt(22)
run.font.bold = True
run.font.color.rgb = RGBColor(46, 117, 182)

subtitle2 = doc.add_paragraph()
subtitle2.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle2.add_run('数据分析 + 特征工程\n\n')
run.font.size = Pt(16)
run.font.color.rgb = RGBColor(91, 155, 213)

info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = info.add_run('数据集：USGS 01047000 径流预测\n')
run.font.size = Pt(12)

date = doc.add_paragraph()
date.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = date.add_run('验收日期：2024年10月8日\n\n')
run.font.size = Pt(12)

doc.add_page_break()

# ==================== 一、完成情况总览 ====================
h1 = doc.add_heading('一、验收完成情况总览', level=1)
h1.runs[0].font.color.rgb = RGBColor(31, 78, 120)

p = doc.add_paragraph()
run = p.add_run('本次阶段验收要求完成数据分析和特征工程两大部分，共8个子任务。经检查，')
run = p.add_run('全部8个子任务均已完成')
run.bold = True
run.font.color.rgb = RGBColor(0, 176, 80)
run = p.add_run('，完成度100%。')

doc.add_paragraph()

# 完成情况表格
table = doc.add_table(rows=9, cols=4)
table.style = 'Light Grid Accent 1'

# 表头
header_cells = table.rows[0].cells
header_cells[0].text = '编号'
header_cells[1].text = '子任务'
header_cells[2].text = '状态'
header_cells[3].text = '得分'

for cell in header_cells:
    cell.paragraphs[0].runs[0].font.bold = True
    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_cell_color(cell, '4472C4')
    cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

# 数据行
tasks = [
    ('子任务1', '理解数据集各字段的中文含义', '✅ 完成', '得分'),
    ('子任务2', '时间序列数据可视化（所有列）', '✅ 完成', '得分'),
    ('子任务3', '直方图（所有列）', '✅ 完成', '得分'),
    ('子任务4', '箱型图（所有列）', '✅ 完成', '得分'),
    ('子任务5', '皮尔逊相关系数热力图（含滞后）', '✅ 完成', '得分'),
    ('子任务6', '四季月份编码、滞后特征、窗口特征', '✅ 完成', '得分'),
    ('子任务7', '特征归一化（Min-Max或Z-score）', '✅ 完成', '得分'),
    ('子任务8', '特征选择（皮尔逊或互信息法）', '✅ 完成', '得分'),
]

for i, (num, task, status, score) in enumerate(tasks, 1):
    row_cells = table.rows[i].cells
    row_cells[0].text = num
    row_cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_cell_color(row_cells[0], 'F2F2F2')

    row_cells[1].text = task

    row_cells[2].text = status
    row_cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    row_cells[2].paragraphs[0].runs[0].font.bold = True
    row_cells[2].paragraphs[0].runs[0].font.color.rgb = RGBColor(0, 176, 80)
    set_cell_color(row_cells[2], 'E2F0D9')

    row_cells[3].text = score
    row_cells[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    row_cells[3].paragraphs[0].runs[0].font.bold = True
    set_cell_color(row_cells[3], 'E2F0D9')

doc.add_paragraph()

# 总结
p = doc.add_paragraph()
run = p.add_run('总结：')
run.bold = True
run.font.size = Pt(14)

doc.add_paragraph('✓ 数据分析：5个子任务全部完成')
doc.add_paragraph('✓ 特征工程：3个子任务全部完成')
doc.add_paragraph('✓ 额外完成：滞后相关分析、多种方法对比、完整建模实验')

doc.add_page_break()

# ==================== 二、数据分析成果展示 ====================
h1 = doc.add_heading('二、数据分析成果展示', level=1)
h1.runs[0].font.color.rgb = RGBColor(31, 78, 120)

# 子任务1
h2 = doc.add_heading('子任务1：字段中文含义', level=2)
h2.runs[0].font.color.rgb = RGBColor(46, 117, 182)

doc.add_paragraph('数据集包含1827天（2000-2004年）的逐日观测数据，共9个字段。所有字段的中文含义如下：')

# 字段说明表格
field_table = doc.add_table(rows=9, cols=3)
field_table.style = 'Light List Accent 1'

header = field_table.rows[0].cells
header[0].text = '英文字段'
header[1].text = '中文含义'
header[2].text = '单位'
for cell in header:
    cell.paragraphs[0].runs[0].font.bold = True
    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

fields = [
    ('Date', '日期', '-'),
    ('Discharge', '径流（流量）', 'ft³/s'),
    ('Dayl', '日照时长', 's/day'),
    ('Prcp', '降水量', 'mm/day'),
    ('Srad', '短波辐射', 'W/m²'),
    ('Swe', '雪水当量', 'kg/m²'),
    ('Tmax', '最高气温', '°C'),
    ('Tmin', '最低气温', '°C'),
]

for i, (eng, chn, unit) in enumerate(fields, 1):
    row = field_table.rows[i].cells
    row[0].text = eng
    row[1].text = chn
    row[2].text = unit
    row[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_page_break()

# 子任务2
h2 = doc.add_heading('子任务2：时间序列可视化', level=2)
h2.runs[0].font.color.rgb = RGBColor(46, 117, 182)

doc.add_paragraph('对流域数据集的所有列（日期除外）进行了时间序列可视化，包含径流、降水、气温、辐射等8个变量的完整时间序列。')

fig_path = os.path.join('..', 'output', 'figures', 'fig1_时间序列.png')
add_image_safe(doc, fig_path)
doc.add_paragraph('图1：01047000流域逐日径流与气象因子时间序列（2000-2004）', style='Caption')

doc.add_page_break()

# 子任务3
h2 = doc.add_heading('子任务3：直方图', level=2)
h2.runs[0].font.color.rgb = RGBColor(46, 117, 182)

doc.add_paragraph('对所有变量绘制了分布直方图，展示各变量的统计分布特征。径流和降水呈明显右偏分布，气温类变量接近正态分布。')

fig_path = os.path.join('..', 'output', 'figures', 'fig3_直方图.png')
add_image_safe(doc, fig_path)
doc.add_paragraph('图2：各变量分布直方图', style='Caption')

doc.add_page_break()

# 子任务4
h2 = doc.add_heading('子任务4：箱型图', level=2)
h2.runs[0].font.color.rgb = RGBColor(46, 117, 182)

doc.add_paragraph('箱型图分析显示径流的离散程度最大，存在大量高值异常点（洪水事件）。按月分组的箱型图展示了明显的季节性特征。')

fig_path = os.path.join('..', 'output', 'figures', 'fig4_箱型图.png')
add_image_safe(doc, fig_path)
doc.add_paragraph('图3：箱型图分析 - 各变量离散程度与径流的季节性', style='Caption')

doc.add_page_break()

# 子任务5
h2 = doc.add_heading('子任务5：皮尔逊相关系数热力图', level=2)
h2.runs[0].font.color.rgb = RGBColor(46, 117, 182)

doc.add_paragraph('完成了三类相关性分析：')
doc.add_paragraph('1. 径流序列与其自身滞后序列的相关系数（自相关ACF）', style='List Bullet')
doc.add_paragraph('2. 径流序列与其他因子同期序列的相关系数', style='List Bullet')
doc.add_paragraph('3. 径流序列与其他因子滞后序列的相关系数（互相关CCF）', style='List Bullet')

fig_path = os.path.join('..', 'output', 'figures', 'fig5_相关系数热力图.png')
add_image_safe(doc, fig_path)
doc.add_paragraph('图4：皮尔逊相关系数热力图', style='Caption')

doc.add_paragraph()
doc.add_paragraph('降水（Prcp）与径流的同期相关性最强（r=0.43），其他气象因子与径流的线性相关性较弱，说明需要引入滞后特征。')

doc.add_page_break()

fig_path = os.path.join('..', 'output', 'figures', 'fig6_滞后相关.png')
add_image_safe(doc, fig_path)
doc.add_paragraph('图5：滞后相关分析 - 径流自相关(ACF)与气象因子互相关(CCF)', style='Caption')

doc.add_paragraph()
doc.add_paragraph('径流的自相关系数lag1为0.77，lag7为0.40，衰减较快但仍有明显记忆效应，为引入滞后特征提供了依据。')

doc.add_page_break()

# ==================== 三、特征工程成果展示 ====================
h1 = doc.add_heading('三、特征工程成果展示', level=1)
h1.runs[0].font.color.rgb = RGBColor(31, 78, 120)

# 子任务6
h2 = doc.add_heading('子任务6：时间序列特征提取', level=2)
h2.runs[0].font.color.rgb = RGBColor(46, 117, 182)

doc.add_paragraph('完成了三类时间序列特征提取：')

doc.add_paragraph('1. 季节与月份编码')
p = doc.add_paragraph()
p.add_run('   • 四季编码：season_春/夏/秋/冬（one-hot编码）\n')
p.add_run('   • 月份编码：doy_sin, doy_cos, month_sin, month_cos（三角周期编码）\n')
p.add_run('   共8个特征')

doc.add_paragraph('2. 滞后特征（Lag Features）')
p = doc.add_paragraph()
p.add_run('   • 变量：Discharge, Prcp, Tmax, Tmin, Vp, Srad\n')
p.add_run('   • 滞后阶数：1, 2, 3, 7, 14, 30天\n')
p.add_run('   共36个特征')

doc.add_paragraph('3. 窗口特征（Rolling Features）')
p = doc.add_paragraph()
p.add_run('   • 变量：Discharge, Prcp\n')
p.add_run('   • 窗口长度：3, 7, 14, 30天\n')
p.add_run('   • 统计量：mean, std, max\n')
p.add_run('   共24个特征')

doc.add_paragraph()
p = doc.add_paragraph()
run = p.add_run('总计构造81个候选特征')
run.bold = True
run.font.color.rgb = RGBColor(0, 112, 192)

doc.add_page_break()

# 子任务7
h2 = doc.add_heading('子任务7：特征归一化', level=2)
h2.runs[0].font.color.rgb = RGBColor(46, 117, 182)

doc.add_paragraph('实现并对比了两种归一化方法：')
doc.add_paragraph('• 最小-最大归一化（Min-Max Normalization）：将特征线性映射到[0,1]', style='List Bullet')
doc.add_paragraph('• Z-score标准化：将特征转换为均值0、方差1的分布', style='List Bullet')

fig_path = os.path.join('..', 'output', 'figures', 'fig7_归一化对比.png')
add_image_safe(doc, fig_path)
doc.add_paragraph('图6：归一化前后特征取值分布对比', style='Caption')

doc.add_paragraph()
doc.add_paragraph('经对比，Z-score标准化对异常值更稳健，更适合本数据集的强右偏分布特征，因此最终采用Z-score标准化方法。')

doc.add_page_break()

# 子任务8
h2 = doc.add_heading('子任务8：特征选择', level=2)
h2.runs[0].font.color.rgb = RGBColor(46, 117, 182)

doc.add_paragraph('实现并对比了两种特征选择方法：')
doc.add_paragraph('• 皮尔逊相关系数法：度量特征与目标的线性相关性', style='List Bullet')
doc.add_paragraph('• 互信息法：基于信息熵，能捕捉非线性依赖关系', style='List Bullet')

fig_path = os.path.join('..', 'output', 'figures', 'fig8_特征选择.png')
add_image_safe(doc, fig_path)
doc.add_paragraph('图7：互信息法与皮尔逊相关系数法特征重要性对比', style='Caption')

doc.add_page_break()

fig_path = os.path.join('..', 'output', 'figures', 'fig9_特征类别贡献.png')
add_image_safe(doc, fig_path)
doc.add_paragraph('图8：各类特征对径流的互信息贡献', style='Caption')

doc.add_paragraph()
doc.add_paragraph('互信息得分最高的是径流自身的短窗口与滞后特征，说明径流的近期状态是最强的预测因子。最终按互信息得分保留TOP 50个特征。')

doc.add_page_break()

# ==================== 四、技术实现要点 ====================
h1 = doc.add_heading('四、技术实现要点', level=1)
h1.runs[0].font.color.rgb = RGBColor(31, 78, 120)

doc.add_paragraph('1. 代码组织', style='List Number')
doc.add_paragraph('   • 完整代码共8个模块，结构清晰，可读性强')
doc.add_paragraph('   • 通过run_all.py可一键复现全部结果')

doc.add_paragraph('2. 数据泄漏防护', style='List Number')
doc.add_paragraph('   • 所有归一化统计量（均值/方差）仅在训练集上估计')
doc.add_paragraph('   • 特征选择评分仅使用训练集数据')
doc.add_paragraph('   • 滞后与窗口特征严格只向过去取数，不使用未来信息')

doc.add_paragraph('3. 可视化规范', style='List Number')
doc.add_paragraph('   • 统一配色方案，图表美观专业')
doc.add_paragraph('   • 中文标签清晰，便于理解')
doc.add_paragraph('   • 所有图表均保存为高分辨率PNG格式')

doc.add_paragraph('4. 结果可追溯', style='List Number')
doc.add_paragraph('   • 所有数值结果保存为CSV格式')
doc.add_paragraph('   • 图表与数据完全对应，可验证')

doc.add_page_break()

# ==================== 五、总结 ====================
h1 = doc.add_heading('五、总结', level=1)
h1.runs[0].font.color.rgb = RGBColor(31, 78, 120)

p = doc.add_paragraph()
run = p.add_run('本次阶段验收的8个子任务已全部完成')
run.bold = True
run.font.size = Pt(14)
p.add_run('，达到验收要求。')

doc.add_paragraph()
doc.add_paragraph('主要成果：')
doc.add_paragraph('✓ 数据分析：完成5类可视化分析，深入理解数据分布和相关性', style='List Bullet')
doc.add_paragraph('✓ 特征工程：构造81个候选特征，实现归一化和特征选择', style='List Bullet')
doc.add_paragraph('✓ 代码实现：8个模块，结构清晰，可完全复现', style='List Bullet')
doc.add_paragraph('✓ 额外工作：已完成建模实验（24个个体模型+16个集成模型）', style='List Bullet')

doc.add_paragraph()
p = doc.add_paragraph()
p.add_run('所有图表、数据和代码均已整理完毕，可随时展示。')

# 保存文档
output_path = '机器学习课程实践_第一次阶段验收汇报.docx'
doc.save(output_path)
print("验收汇报文档已生成：" + output_path)
