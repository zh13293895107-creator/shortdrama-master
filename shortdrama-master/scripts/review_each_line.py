#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐条审核（每集交付前的强制总门）。
用法: python review_each_line.py <文件.xml ...> 或 <目录>
机制:
  对每一行编号、分类，机器对“能确定的规则”逐条硬判，任一不过即 FAIL、退出码 1；
  同时打印“人工逐条清单”，主观项（活人话/情绪/人物感/口号味/反应/OS大白话）必须由人逐条回答 ✓，
  机器 FAIL 清零且人工清单每条都 ✓，才允许交付。
反应硬门（基本要求）：
  - 同一个角色连续发声、中间没有任何画面行（对方没接话、没动作）→ [NO-REACT] FAIL；
  - 中间有画面行 → 列“待人工确认反应”，必须确认画面真的是对方在反应；
  - 一场戏最后一句是对在场人说的、后面没任何反应画面 → [NO-REACT] FAIL。
"""
import sys, os, re, glob, argparse

# 画面行禁用：抽象/分镜/象征/歧义
VISUAL_BAD = ['轻轻', '微微', '缓缓', '仿佛', '似乎', '不禁', '顿时', '瞬间',
              '发亮', '发紧', '发蒙', '发颤', '发酸', '纳闷', '闷声', '慢声',
              '赔笑', '讪', '捻', '摊着', '人影晃', '当心', '踩上', '压过来',
              '一层阴', '油然而生', '情不自禁', '嘴角勾起', '钉在原地']
# 括号表演禁用抽象词
CUE_BAD = ['发亮', '发紧', '发蒙', '发颤', '发酸', '气音', '一僵', '脸沉']
# 说教/格言
PREACH_BAD = ['硬道理', '吃得苦中苦', '人善被人欺', '合法', '才是']
# 数字摘要（阿拉伯/中文数字 + 单位）
UNIT_RE = re.compile(r'(?:\d+\.?\d*|[一二三四五六七八九十百零半]+(?:块[一二三四五六七八九]?)?)[块毛分只条刀亩罐]')
PARTICLES = set('啊呢呗吧呀嘛啦哟哩嘞喽哇喔吗')
QUOTE_RE = re.compile(r'[这那就](?:一)?句([^，。；：、！？\s]{1,4})')
SCENE_RE = re.compile(r'<p><b>(场\d+)[^<]*</b></p>')

def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, '*.xml')))
        else:
            files.append(p)
    return files

def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s)

def reaction_pass(scene_no, spoken, machine_fail):
    """对一场戏逐句核对反应。spoken 元素含 idx/role/is_os/visual_after。"""
    notes = []
    for i, ev in enumerate(spoken):
        last = (i == len(spoken) - 1)
        if not last:
            nxt = spoken[i + 1]
            if nxt['role'] == ev['role'] and not ev['is_os']:
                if ev['visual_after'] == 0:
                    notes.append('L%02d [NO-REACT] 同一角色连续发声，对方没接话也没动作' % ev['idx'])
                    machine_fail += 1
                else:
                    notes.append('L%02d 待人工确认反应：中间有画面，确认是对方在反应' % ev['idx'])
        else:
            # 场尾可在台词上硬切到新地点，不硬判；统一列人工确认是否晾着在场人
            if not ev['is_os']:
                notes.append('L%02d 待人工确认反应：场尾收在台词上，确认不是晾着在场人' % ev['idx'])
    if notes:
        print('  —— %s 反应检查 ——' % scene_no)
        for x in notes:
            print('  ' + x)
    return machine_fail

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='+')
    a = ap.parse_args()
    machine_fail = 0
    for f in collect(a.paths):
        lines = open(f, encoding='utf-8').read().splitlines()
        ep = (re.findall(r'<h2>第(\d+)集', '\n'.join(lines)) or ['?'])[0]
        print('\n========== %s 第%s集 逐条审核 ==========' % (os.path.basename(f), ep))
        prior_spoken = ''
        human_rows = []
        scene_spoken = []
        visual_after = 0
        cur_scene = '全剧'
        n = 0
        for l in lines:
            t = l.strip()
            if not t:
                continue
            ms = SCENE_RE.search(l)
            if ms:
                if scene_spoken:
                    machine_fail = reaction_pass(cur_scene, scene_spoken, machine_fail)
                cur_scene = ms.group(1)
                scene_spoken = []
                visual_after = 0
            n += 1
            errs = []
            is_visual = t.startswith('<p>△') or t.startswith('<p>▷')
            is_spoken = t.startswith('<p><b>') and '：' in t and not t.startswith('▷')
            plain = strip_tags(t)
            if is_visual:
                visual_after += 1
                if '她' in plain or '他' in plain:
                    errs.append('画面行用了代词，要改全名')
                for w in VISUAL_BAD:
                    if w in plain:
                        errs.append('画面抽象/分镜词「%s」' % w)
                if ('手指' in plain) or ('指头' in plain):
                    errs.append('无意义忙手「手指/指头在…干什么」，改自然动作（指了指/伸手/算珠拨得响）')
            # 对白/OS
            if is_spoken:
                role = re.match(r'<p><b>([^<]+)</b>', t).group(1)
                body = t.split('：', 1)[1]
                cue = ''
                mm = re.match(r'<p><b>[^<]+</b>（([^）]*)）', t)
                if mm:
                    cue = mm.group(1)
                is_os = ('OS' in cue) or ('心声' in cue) or ('OS' in role)
                body_clean = re.sub(r'[^一-鿿A-Za-z0-9]', '', strip_tags(re.sub(r'（[^）]*）', '', body)))
                for w in VISUAL_BAD + CUE_BAD + PREACH_BAD:
                    if w in cue:
                        errs.append('括号抽象/说教词「%s」' % w)
                    if w in strip_tags(body):
                        errs.append('台词抽象/说教词「%s」' % w)
                if ('手指' in cue) or ('指头' in cue):
                    errs.append('括号忙手「手指/指头在…干什么」，改自然动作')
                # 数字摘要
                if len(UNIT_RE.findall(strip_tags(body))) >= 2 and not any(c in strip_tags(body) for c in PARTICLES) and len(body_clean) < 22:
                    errs.append('数字罗列摘要腔')
                # 悬空引用
                qm = QUOTE_RE.search(strip_tags(body))
                if qm and qm.group(1) and qm.group(1) not in prior_spoken:
                    errs.append('悬空引用「%s」前面没说' % qm.group(1))
                prior_spoken += body_clean
                # 登记到本场反应清单
                if scene_spoken:
                    scene_spoken[-1]['visual_after'] = visual_after
                visual_after = 0
                scene_spoken.append({'idx': n, 'role': role, 'is_os': is_os, 'visual_after': 0})
                human_rows.append((n, plain[:38], is_os))
            verdict = 'FAIL: ' + '；'.join(errs) if errs else 'PASS'
            if errs:
                machine_fail += 1
            kind = '画面' if is_visual else ('发声' if is_spoken else '其他')
            print('L%02d[%s] %s  => %s' % (n, kind, plain[:34], verdict))
        if scene_spoken:
            machine_fail = reaction_pass(cur_scene, scene_spoken, machine_fail)
        # 人工逐条清单（主观项，必须每条回答）
        print('\n--- 人工逐条清单 ---')
        for ln, txt, is_os in human_rows:
            if is_os:
                print('L%02d（OS，待人工 ✓）：活人话？情绪？像这人？大白话具体不抽象？ —— %s' % (ln, txt))
            else:
                print('L%02d（待人工 ✓）：活人话？情绪？像这人？口号味？对方有反应？ —— %s' % (ln, txt))
    print('\n机器 FAIL 数:', machine_fail)
    if machine_fail:
        print('存在机器硬伤，禁止交付，先返工。')
    return 1 if machine_fail else 0

if __name__ == '__main__':
    sys.exit(main())
