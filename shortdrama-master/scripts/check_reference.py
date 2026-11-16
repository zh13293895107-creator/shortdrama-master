#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悬空引用核对：OS/台词里“引用一个词/一句话”时，这个词必须在前面真实说出口的台词里出现。
用法: python check_reference.py <文件.xml ...> 或 <目录>
典型漏洞:
  前面没人说“心善”，OS 却写“就一句心善……”  -> 观众听声音找不到落点
本工具按“引用词在之前发声行里是否出现”做硬筛，命中即标 [DANGLING]，退出码 1。
语义上的承接机器不一定判得准，最终仍需人工闭眼听一遍。
"""
import sys, os, re, glob, argparse

# 引用一个“词”：这/那/就 + 句 + 词
QUOTE_RES = [
    re.compile(r'[这那](?:一)?句([^，。；：、！？\s]{1,4})'),
    re.compile(r'就(?:一)?句([^，。；：、！？\s]{1,4})'),
    re.compile(r'([^，。；：、！？\s]{1,4})这两个字'),
]
# 引用“这话/这俩字”，前面必须有内容
BARE_RES = [
    re.compile(r'这(?:俩|两)个?字'),
    re.compile(r'这话(?:儿)?'),
]

def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, '*.xml')))
        else:
            files.append(p)
    return files

def spoken_bodies(s):
    """返回按顺序的发声行正文（已去标签、括号、标点）。"""
    out = []
    for l in s.splitlines():
        t = l.strip()
        if t.startswith('<p><b>') and '：' in l and not t.startswith('▷'):
            body = l.split('：', 1)[1]
            body = re.sub(r'（[^）]*）', '', body)
            body = re.sub(r'<[^>]+>', '', body)
            body = re.sub(r'[^一-鿿A-Za-z0-9]', '', body)
            if body:
                out.append(body)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='+')
    a = ap.parse_args()
    issues = 0
    for f in collect(a.paths):
        s = open(f, encoding='utf-8').read()
        ep = (re.findall(r'<h2>第(\d+)集', s) or ['?'])[0]
        bodies = spoken_bodies(s)
        prior = ''
        for i, b in enumerate(bodies):
            for rx in QUOTE_RES:
                for word in rx.findall(b):
                    if word and word not in prior:
                        print('[DANGLING] %s 集%s 第%d行引用“%s”，前面台词里没出现：%s'
                              % (os.path.basename(f), ep, i + 1, word, b))
                        issues += 1
            for rx in BARE_RES:
                if rx.search(b) and not prior:
                    print('[DANGLING] %s 集%s 第%d行引用前面内容，但前面没有发声行：%s'
                          % (os.path.basename(f), ep, i + 1, b))
                    issues += 1
            prior += b
        print('%s 集%s：发声行%d，悬空引用%d' % (os.path.basename(f), ep, len(bodies), issues))
    print('悬空引用数:', issues)
    return 1 if issues else 0

if __name__ == '__main__':
    sys.exit(main())
