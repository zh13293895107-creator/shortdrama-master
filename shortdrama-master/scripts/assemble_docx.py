#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把故事大纲、人物小传与分集剧本整合为一个 Word(.docx)。
用法:
  python assemble_docx.py --title "剧名" --front front.xml --parts p1.xml p2.xml ... [--subtitle "副题"] [--out out.docx]
说明:
  --front 可选(含故事大纲/人物小传, 标签 h1/h2/p/b/blockquote)；--parts 为按顺序排列的分集 XML。
  封面自动生成；A4、2.5cm 边距、页脚居中页码(封面不显示)。
"""
import os,re,argparse
import xml.etree.ElementTree as ET
from docx import Document
from docx.shared import Pt,Cm,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BLACK=RGBColor(0,0,0); GREY=RGBColor(0x59,0x59,0x59)
CROWD=('网友','弹幕','路人','围观','宾客','名媛','记者','主持人','店员','管家','护士','保安',
       '员工','观众','粉丝','前台','助理','佣人','保姆','邻居','学生','评委','股东','董事',
       '医生','警察','警官','律师','工作人员','路人甲','路人乙','群演')

def fmt(run,cn='宋体',size=11,bold=False,italic=False,color=BLACK):
    run.font.name='Arial'
    rPr=run._element.get_or_add_rPr()
    rf=rPr.find(qn('w:rFonts'))
    if rf is None:
        rf=OxmlElement('w:rFonts'); rPr.append(rf)
    rf.set(qn('w:eastAsia'),cn); rf.set(qn('w:ascii'),'Arial'); rf.set(qn('w:hAnsi'),'Arial')
    run.font.size=Pt(size); run.bold=bold; run.italic=italic; run.font.color.rgb=color

def build(title,subtitle,front,parts,out):
    doc=Document()
    sec=doc.sections[0]
    sec.page_width=Cm(21); sec.page_height=Cm(29.7)
    for m in ('top_margin','bottom_margin','left_margin','right_margin'): setattr(sec,m,Cm(2.5))
    normal=doc.styles['Normal']; normal.font.name='Arial'; normal.font.size=Pt(11)
    normal.element.rPr.rFonts.set(qn('w:eastAsia'),'宋体')

    def para(sb=0,sa=2,line=1.25,left=0.0,fi=0.0,align=None,keep=False):
        p=doc.add_paragraph(); pf=p.paragraph_format
        pf.space_before=Pt(sb); pf.space_after=Pt(sa)
        pf.line_spacing=line; pf.line_spacing_rule=WD_LINE_SPACING.MULTIPLE
        if left: pf.left_indent=Cm(left)
        if fi: pf.first_line_indent=Cm(fi)
        if align is not None: pf.alignment=align
        pf.keep_with_next=keep
        return p

    def rich(p,elem,cn='宋体',size=11,bold_cn='黑体',color=BLACK):
        if elem.text:
            r=p.add_run(elem.text); fmt(r,cn,size,color=color)
        for ch in elem:
            if ch.tag=='b':
                r=p.add_run(ch.text or ''); fmt(r,bold_cn,size,bold=True,color=color)
                if ch.tail: r=p.add_run(ch.tail); fmt(r,cn,size,color=color)
            else:
                t=''.join(ch.itertext())
                if t: r=p.add_run(t); fmt(r,cn,size,color=color)
                if ch.tail: r=p.add_run(ch.tail); fmt(r,cn,size,color=color)

    def heading(text,level):
        p=doc.add_heading(level=level); p.paragraph_format.keep_with_next=True
        if level==1: p.paragraph_format.space_before=Pt(14); p.paragraph_format.space_after=Pt(8); sz=16
        else: p.paragraph_format.space_before=Pt(10); p.paragraph_format.space_after=Pt(5); sz=13.5
        r=p.add_run(text); fmt(r,'黑体',sz,bold=True)

    # 封面
    for _ in range(5): doc.add_paragraph()
    p=para(align=WD_ALIGN_PARAGRAPH.CENTER,sa=10); r=p.add_run(title); fmt(r,'黑体',24,bold=True)
    p=para(align=WD_ALIGN_PARAGRAPH.CENTER,sa=22); r=p.add_run(subtitle); fmt(r,'楷体',14)
    p=para(align=WD_ALIGN_PARAGRAPH.CENTER,sa=6); r=p.add_run('内含：故事大纲 · 人物小传 · 分集剧本'); fmt(r,'仿宋',12,color=GREY)
    doc.add_page_break()

    def parse(path):
        raw=open(path,encoding='utf-8').read()
        return ET.fromstring('<root>'+raw+'</root>')

    def article(elem):
        t=elem.tag
        if t=='h1': heading((elem.text or '').strip(),1)
        elif t=='h2': heading((elem.text or '').strip(),2)
        elif t=='blockquote':
            for sub in elem.iter('p'):
                txt=''.join(sub.itertext()).strip()
                p=para(sb=4,sa=6,line=1.3,left=0.6); r=p.add_run(txt); fmt(r,'楷体',10.5,color=GREY)
        elif t=='p':
            txt=''.join(elem.itertext()).strip()
            if not txt: return
            p=para(sa=5,line=1.45,fi=0.74); rich(p,elem)

    def script_p(elem):
        full=''.join(elem.itertext()).strip()
        if not full: return
        b0=elem.find('b'); b0t=(b0.text or '').strip() if b0 is not None else ''
        if full.startswith('（约') and ('冷开场' in full or '爆点' in full):
            p=para(sb=2,sa=4,left=0.4,keep=True); r=p.add_run(full); fmt(r,'楷体',10.5,color=GREY); return
        if b0t and re.match(r'^场\d+',b0t):
            p=para(sb=7,sa=3,keep=True); rich(p,elem,cn='黑体',bold_cn='黑体')
            for r in p.runs: r.bold=True
            return
        if full.startswith('△'):
            p=para(sa=2); r=p.add_run(full); fmt(r,'楷体',11); return
        if full.startswith('▷'):
            p=para(sb=3,sa=8); r=p.add_run('▷ '); fmt(r,'宋体',11,bold=True)
            if b0t:
                rich(p,elem)
                for r in p.runs: r.bold=True
            else:
                r=p.add_run(full[1:].strip()); fmt(r,'宋体',11,bold=True)
            return
        if ('（心声）' in full) or ('（OS' in full) or ('(OS' in full):
            p=para(sa=2,left=0.74)
            if b0t:
                rich(p,elem,cn='楷体',bold_cn='楷体')
            else:
                r=p.add_run(full); fmt(r,'楷体',11)
            return
        if '【系统】' in full or b0t=='系统':
            p=para(sa=2,left=0.74); rich(p,elem,cn='仿宋',bold_cn='仿宋')
            for r in p.runs: r.bold=True
            return
        if b0t and any(b0t.startswith(c) or b0t==c for c in CROWD):
            p=para(sa=2,left=0.74); rich(p,elem,cn='仿宋',bold_cn='仿宋'); return
        p=para(sa=2)
        if b0t: rich(p,elem)
        else:
            r=p.add_run(full); fmt(r,'宋体',11)

    ep=[]
    if front and os.path.exists(front):
        for elem in parse(front): article(elem)
    if parts:
        doc.add_page_break(); heading('第三部分　分集剧本',1)
        for idx,pt in enumerate(parts):
            doc.add_page_break()
            for elem in parse(pt):
                t=elem.tag
                if t=='h1': heading((elem.text or '').strip(),1)
                elif t=='h2':
                    ht=(elem.text or '').strip(); heading(ht,2)
                    m=re.search(r'第(\d+)集',ht)
                    if m: ep.append(int(m.group(1)))
                elif t=='blockquote':
                    for sub in elem.iter('p'):
                        txt=''.join(sub.itertext()).strip()
                        p=para(sb=2,sa=6,left=0.5,keep=True); r=p.add_run(txt); fmt(r,'楷体',10.5,color=GREY)
                elif t=='p': script_p(elem)

    # 页脚页码
    sec.different_first_page_header_footer=True
    fp=sec.footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
    run=fp.add_run()
    a=OxmlElement('w:fldChar'); a.set(qn('w:fldCharType'),'begin')
    b=OxmlElement('w:instrText'); b.set(qn('xml:space'),'preserve'); b.text='PAGE'
    c=OxmlElement('w:fldChar'); c.set(qn('w:fldCharType'),'end')
    run._element.append(a); run._element.append(b); run._element.append(c); fmt(run,'宋体',10)

    doc.save(out)
    print('已保存:',out,' 集数:',len(ep),
          (' 连续' if ep==list(range(min(ep),max(ep)+1)) else ' 不连续!'))

if __name__=='__main__':
    ap=argparse.Argument()
    ap.add_argument('--title',required=True)
    ap.add_argument('--subtitle',default='——竖屏短剧完整剧本（含故事大纲·人物小传）——')
    ap.add_argument('--front',default='')
    ap.add_argument('--parts',nargs='*',default=[])
    ap.add_argument('--out',default='')
    a=ap.parse_args()
    out=a.out or (a.title+'.docx')
    build(a.title,a.subtitle,a.front,a.parts,out)
