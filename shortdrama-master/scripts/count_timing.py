#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竖屏短剧 单集时长结算（锁定版口径：发声净字 260—280，动作预留约 10 秒，成片卡 80 秒）。
用法:
  python count_timing.py <文件.xml ...> [--action 10] [--target 80]
  python count_timing.py <目录>
口径:
  - 发声净字 = 对白 + OS 正文（去角色名、括号提示、标签、标点），只数实际文字（汉字/数字/字母）
  - 标点不占发声字，只定语气、停顿和节奏
  - 发声时间 = 发声净字 / 4（4 字/秒）
  - 成片 = 发声时间 + 动作预留（默认 10 秒：气口/独立动作/反应/剪接）
  - 硬判：净字须在 260—280；成片 > 80 即 FAIL，退出码 1
  - 独立动作偏多的集允许压到 260—270，不强行凑 280
"""
import sys, os, re, argparse

def collect(args):
    files = []
    for a in args:
        if os.path.isdir(a):
            files += [os.path.join(a, f) for f in sorted(os.listdir(a))
                      if f.lower().endswith('.xml')]
        else:
            files.append(a)
    return files

def spoken_lines(s):
    out = []
    for l in s.splitlines():
        t = l.strip()
        if t.startswith('<p><b>') and '：' in l and not t.startswith('▷'):
            body = l.split('：', 1)[1]
            body = re.sub(r'（[^）]*）', '', body)
            body = re.sub(r'<[^>]+>', '', body)
            body = body.replace(' ', '').replace('\u3000', '')
            body = re.sub(r'[^一-鿿A-Za-z0-9]', '', body)
            if body:
                out.append(body)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='+')
    ap.add_argument('--action', type=float, default=10.0, help='动作/反应/剪接预留秒数，默认10')
    ap.add_argument('--target', type=float, default=80.0, help='成片目标秒数，默认80')
    ap.add_argument('--lo', type=int, default=260, help='发声净字下限，默认260')
    ap.add_argument('--hi', type=int, default=280, help='发声净字上限，默认280')
    a = ap.parse_args()
    files = collect(a.paths)
    if not files:
        print('未找到 xml 文件'); return 2
    fails = 0
    for f in files:
        s = open(f, encoding='utf-8').read()
        nums = re.findall(r'<h2>第(\d+)集', s)
        chars = sum(len(x) for x in spoken_lines(s))
        voice = chars / 4
        total = voice + a.action
        problems = []
        if chars < a.lo or chars > a.hi:
            problems.append('净字%d越界（须%d—%d）' % (chars, a.lo, a.hi))
        if total > a.target:
            problems.append('成片%.1f秒超%.0f秒' % (total, a.target))
        if problems:
            fails += 1
        ep = ('第%s集' % nums[0]) if nums else os.path.basename(f)
        verdict = 'FAIL: ' + '；'.join(problems) if problems else 'PASS'
        print('%s %s：发声%d字 → %.1f秒 + 动作%.0f秒 = 成片%.1f秒  %s'
              % (os.path.basename(f), ep, chars, voice, a.action, total, verdict))
    print('锁定口径：发声净字%d—%d（4字/秒，不含标点），成片≤%.0f秒；FAIL数 %d'
          % (a.lo, a.hi, a.target, fails))
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main())
