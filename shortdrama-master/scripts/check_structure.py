#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结构爽感总审（头号规矩，最严格，逐集+整批必过）。
用法: python check_structure.py <文件.xml ...> 或 <目录>
头号规矩（每集都必须满足，循环到结局）：
  开头：第一集引人入胜、第一帧即冲突；其余每集开头必须回应上集钩子，且回应本身有吸引力。
  中段：必须有强烈冲突和爽点（至少两个角色对上、有来有回、有反转/打脸）。
  结尾：必须留让人想看下一集的钩子（▷ 行）。
  下一集开头必须对钩子做出让人想看的回应，如此循环，直到结局。
机器只对“能确定的结构缺失”硬判：
  [NO-HOOK] 没有结尾 ▷ 钩子；
  [THIN] 发声行太少（<5），没有中段；
  [NO-CONFLICT] 说话角色不足两个，没有冲突；
  钩子→下一集开头无明显关键词重合，列“待人工确认回应”（语义回应可能不共用原词）。
同时打印“人工签字表”，每集必须逐条 ✓ 才允许交付。
"""
import sys, os, re, glob, argparse

H2_RE = re.compile(r'<h2>第(\d+)集[^《]*《([^》]+)》')
SPOKEN_RE = re.compile(r'^<p><b>([^<]+)</b>(（[^）]*）)?[：:](.*?)</p>$')
SCENE_RE = re.compile(r'<p><b>(场\d+)[^<]*</b></p>')

def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, '*.xml')))
        else:
            files.append(p)
    return files

def clean(s):
    return re.sub(r'[^一-龥A-Za-z0-9]', '', re.sub(r'<[^>]+>', '', s))

def bigrams(s):
    return set(s[i:i+2] for i in range(len(s) - 1))

def parse(f):
    t = open(f, encoding='utf-8').read()
    n, title = (H2_RE.search(t).groups() if H2_RE.search(t) else ('?', '?'))
    spoken = []          # (role, is_os, body_plain)
    hook = ''
    opening = ''
    for line in t.splitlines():
        s = line.strip()
        if s.startswith('<p>▷'):
            hook = s
        m = SPOKEN_RE.match(s)
        if m and not s.startswith('▷'):
            role, cue, body = m.group(1), m.group(2) or '', m.group(3)
            is_os = ('OS' in cue) or ('心声' in cue)
            spoken.append((role, is_os, clean(body)))
            if not opening:
                opening = s
    roles = set(r for r, is_os, _ in spoken if not is_os)
    return int(n) if n.isdigit() else -1, title, spoken, roles, hook, opening

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='+')
    a = ap.parse_args()
    data = [parse(f) for f in collect(a.paths)]
    data.sort(key=lambda x: x[0])
    hard = 0
    print('===== 结构爽感总审（头号规矩）=====')
    for n, title, spoken, roles, hook, opening in data:
        errs = []
        if not hook:
            errs.append('[NO-HOOK] 没有结尾钩子')
        if len(spoken) < 5:
            errs.append('[THIN] 发声行%d，中段撑不起来' % len(spoken))
        if len(roles) < 2:
            errs.append('[NO-CONFLICT] 在场说话角色不足两个')
        if errs:
            hard += len(errs)
        print('EP%02d《%s》：发声%d行、角色%s %s'
              % (n, title, len(spoken), '、'.join(sorted(roles)) or '无',
                 '  '.join(errs) or '结构齐全'))
    print('\n--- 钩子→下一集开头 回应闭环 ---')
    for i in range(len(data) - 1):
        n, _, _, _, hook, _ = data[i]
        n2, _, _, _, _, opening2 = data[i + 1]
        if n2 != n + 1:
            continue
        common = bigrams(clean(hook)) & bigrams(clean(opening2))
        if common:
            print('EP%02d钩 → EP%02d开头：✓ 回应关键词 %s' % (n, n2, '、'.join(sorted(common)[:5])))
        else:
            print('EP%02d钩 → EP%02d开头：待人工确认回应（无明显关键词，闭眼听是否真接住）' % (n, n2))
    print('\n--- 人工签字表（每集逐条 ✓，否则不许交付）---')
    for n, title, spoken, roles, hook, opening in data:
        first = '第一集：开头引人入胜、第一帧即冲突？' if n == data[0][0] else '开头回应上集钩子、且回应本身有吸引力？'
        print('EP%02d《%s》：%s  中段强冲突/爽？  结尾钩子让人想看下一集？' % (n, title, first))
    print('\n机器硬伤数:', hard)
    if hard:
        print('结构有硬伤，禁止交付，先返工。')
    return 1 if hard else 0

if __name__ == '__main__':
    sys.exit(main())
