#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
女频/下沉竖屏短剧剧本确定性自检。
用法:
  python scan_script.py <文件.xml> [文件2.xml ...]
  python scan_script.py <目录>            # 扫描目录下全部 .xml（按文件名排序）
检查: 集数连续性 / 去AI味禁词 / △画面行心理词 / 编辑批注 / 标签配平 / 说教金句。
有任一问题时以退出码 1 结束。
"""
import sys,os,re

BANNED=['然而','不禁','仿佛','似乎','缓缓','轻轻','微微','顿时','瞬间','深深',
        '钉在原地','闪过一丝','嘴角勾起','油然而生','情不自禁']
# △ 画面行不应出现的心理/不可见词
PSY=['心说','心里','暗自','心想','暗忖','心道','心中','心头','暗喜','暗惊',
     '盘算','本想','假意','故作','暗自得意','内心']
# OS/心声里禁止的“讲道理/格言/普法金句”模式（观众反感的 AI 说教腔）
PREACH=[r'这种东西',r'这种事',r'这种人',r'趁早',r'终究',r'终归',r'向来',r'从来',
        r'不过是',r'无非是',r'只不过',r'罢了',r'而已',r'说白了',r'所谓',r'这就是',
        r'才是',r'道理',r'东西[，,](要|得|就)',r'事情[，,](要|得)']
TAGS=['p','h1','h2','b','blockquote']

def collect(args):
    files=[]
    for a in args:
        if os.path.isdir(a):
            files += [os.path.join(a,f) for f in sorted(os.listdir(a)) if f.lower().endswith('.xml')]
        else:
            files.append(a)
    return files

def main():
    if len(sys.argv)<2:
        print(__doc__); return 2
    files=collect(sys.argv[1:])
    def first_ep(path):
        try:
            nums=re.findall(r'<h2>第(\d+)集',open(path,encoding='utf-8').read())
            return int(min(nums)) if nums else -1
        except Exception:
            return -1
    files.sort(key=first_ep)
    if not files:
        print('未找到 xml 文件'); return 2
    issues=0; allnums=[]; total=0
    for f in files:
        try:
            s=open(f,encoding='utf-8').read()
        except Exception as e:
            print('[OPEN FAIL] %s %s'%(f,e)); issues+=1; continue
        total+=len(s)
        nums=[int(x) for x in re.findall(r'<h2>第(\d+)集',s)]
        if nums: allnums+=nums
        for i,line in enumerate(s.splitlines(),1):
            for w in BANNED:
                if w in line:
                    print('[BAN %s] %s L%d: %s'%(w,os.path.basename(f),i,line.strip()[:80])); issues+=1
            if line.strip().startswith('△'):
                for w in PSY:
                    if w in line:
                        print('[PSY %s] %s L%d: %s'%(w,os.path.basename(f),i,line.strip()[:80])); issues+=1
            if '（注：' in line or '(注：' in line:
                print('[NOTE] %s L%d: %s'%(os.path.basename(f),i,line.strip()[:100])); issues+=1
            if re.search(r'<场\d+>',line):
                print('[BADTAG] %s L%d'%(os.path.basename(f),i)); issues+=1
            # 说教金句：OS/心声里禁止格言/普法/讲道理腔
            if ('（OS）' in line or '(OS)' in line or '（心声）' in line or '(心声)' in line):
                for wp in PREACH:
                    if re.search(wp,line):
                        print('[PREACH %s] %s L%d: %s'%(wp,os.path.basename(f),i,line.strip()[:80])); issues+=1
        for tag in TAGS:
            o=len(re.findall(r'<%s[ >]'%tag,s)); c=len(re.findall(r'</%s>'%tag,s))
            if o!=c:
                print('[TAG %s] %s open=%d close=%d'%(tag,os.path.basename(f),o,c)); issues+=1
        # 冷开场/爆点/钩子是写作前的内部规划，不写进成品剧本，故不在此检查
        if nums:
            print('%s 集%d-%d 共%d 字符%d'%(os.path.basename(f),nums[0],nums[-1],len(nums),len(s)))
    if allnums:
        continuous = allnums==list(range(min(allnums),max(allnums)+1))
        print('集数 %d-%d 共%d, 连续: %s'%(min(allnums),max(allnums),len(allnums),continuous))
        if not continuous: issues+=1
    print('总字符数(含标签):',total)
    print('问题数:',issues)
    return 1 if issues else 0

if __name__=='__main__':
    sys.exit(main())
