#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
钩子承接核对：每集结尾钩子是否在下一集开头有对应（人物当场反应/讨论/铺垫）。
用法: python check_hook_link.py <xml 文件...> 或 <目录>
机器按关键词重合做硬筛：无重合标“待人工核对”并以退出码 1 结束。
语义承接可能不共用原词，最终是否承接由人工对照两集文本判断。
"""
import sys, os, re

def collect(args):
    files = []
    for a in args:
        if os.path.isdir(a):
            files += [os.path.join(a, f) for f in sorted(os.listdir(a)) if f.lower().endswith('.xml')]
        else:
            files.append(a)
    return files

def clean(s):
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'[^一-龥A-Za-z0-9]', '', s)

def bigrams(s):
    return set(s[i:i+2] for i in range(len(s) - 1))

def segments(text):
    summary = scene1 = hook = ''
    m = re.search(r'<h2>.*?</h2>\s*<p>(.*?)</p>', text, flags=re.S)
    if m:
        summary = m.group(1)
    sm = re.search(r'(<p><b>场1\b.*?)(?=<p><b>场2\b)', text, flags=re.S)
    if sm:
        scene1 = sm.group(1)
    hm = re.search(r'(<p>▷.*)$', text, flags=re.S)
    if hm:
        hook = hm.group(1)
    return summary, scene1, hook

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    data = []
    for f in collect(sys.argv[1:]):
        t = open(f, encoding='utf-8').read()
        m = re.findall(r'<h2>第(\d+)集', t)
        n = int(m[0]) if m else -1
        data.append((n,) + segments(t))
    data.sort(key=lambda x: x[0])
    issues = 0
    for i in range(len(data) - 1):
        n, _, _, hook = data[i]
        n2, sum2, sc2, _ = data[i + 1]
        if n2 != n + 1:
            continue
        common = sorted(bigrams(clean(hook)) & (bigrams(clean(sum2)) | bigrams(clean(sc2))))
        if not common:
            issues += 1
            print('EP%02d钩子 → EP%02d开头：⚠ 待人工核对（无明显关键词重合）' % (n, n2))
        else:
            print('EP%02d钩子 → EP%02d开头：✓ 承接关键词 %s' % (n, n2, '、'.join(common[:6])))
    print('待人工核对数:', issues)
    return 1 if issues else 0

if __name__ == '__main__':
    sys.exit(main())
