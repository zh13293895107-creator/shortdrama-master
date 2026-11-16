#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台词/OS 人物感审核工具。
用法:
  python review_lines.py <xml 文件或目录>               逐角色列出全部台词 OS
  python review_lines.py <xml 文件或目录> --anonymous   匿名打乱，做遮名辨人
  python review_lines.py <xml 文件或目录> --audio       纯听版：按顺序只列台词/OS（去画面），做“只听不看”测试
配合“朗读测试 / 遮名辨人 / 情绪落地 / 只听不看”使用。
"""
import sys, os, re, glob, random

def collect(paths):
    files=[]
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, '*.xml')))
        else:
            files.append(p)
    return files

LINE_RE = re.compile(r'<p><b>([^<]+)</b>([^：:]*)[：:](.*?)</p>')
H2_RE = re.compile(r'<h2>第(\d+)集')
SCENE_RE = re.compile(r'<p><b>(场\d+)[^<]*</b></p>')

def parse(files):
    rows=[]  # (序, 集, 场, 角色, 提示, 内容)
    seq=0
    for f in files:
        ep='?'; scene=''
        for line in open(f, encoding='utf-8'):
            m=H2_RE.search(line)
            if m: ep=m.group(1)
            ms=SCENE_RE.search(line)
            if ms: scene=ms.group(1)
            ml=LINE_RE.search(line)
            if ml:
                rows.append((seq, int(ep) if ep.isdigit() else 999, scene,
                             ml.group(1).strip(), ml.group(2).strip(), ml.group(3).strip()))
                seq+=1
    return rows

def main():
    flags=[a for a in sys.argv[1:] if a.startswith('--')]
    args=[a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__); return 2
    rows=parse(collect(args))
    if not rows:
        print('未解析到台词'); return 2
    if '--anonymous' in flags:
        names=sorted(set(r[3] for r in rows))
        keymap={n: chr(65+i) for i,n in enumerate(names)}
        deck=[(keymap[r[3]], r[5]) for r in rows]
        random.seed(7); random.shuffle(deck)
        for k,c in deck: print('[%s] %s'%(k,c))
        print('\n--- 答案 ---')
        for n in names: print('%s = %s'%(keymap[n], n))
        return 0
    if '--audio' in flags:
        curep=None; cursc=None
        for _,ep,scene,name,hint,content in sorted(rows, key=lambda r:(r[1],r[0])):
            if ep!=curep:
                print('\n===== 第%d集 纯听版 ====='%ep); curep=ep; cursc=None
            if scene!=cursc:
                print('— %s —'%scene); cursc=scene
            tag='【心声】' if (('OS' in hint) or ('心声' in hint)) else ''
            print('%s%s：%s'%(name, tag, content))
        return 0
    cur=None
    for _,ep,scene,name,hint,content in sorted(rows, key=lambda r:r[3]):
        if name != cur:
            print('\n【%s】'%name); cur=name
        print('  EP%s %s：%s'%(ep, scene, content))
    return 0

if __name__=='__main__':
    sys.exit(main())
