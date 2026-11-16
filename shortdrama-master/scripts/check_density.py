#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
制作密度审核（防止“只压发声字、把画面动作表演一起砍”的骨架剧本）。
用法:
  python check_density.py <xml 文件或目录> [--tri-min 120] [--cue-ratio 0.8]
检查:
  1. 每个场至少 1 条 △ 画面行；
  2. 每集 △ 总字数不低于 --tri-min（默认120，参考原稿170—320）；
  3. 发声行带括号表演提示的比例不低于 --cue-ratio（默认0.8）；
  4. 口号/格言腔（SLOGAN 表）与“数字罗列摘要腔”（≥2个数字+单位、无语气词、过短）。
任一问题退出码 1。
"""
import sys, os, re, glob, argparse

SLOGAN=['一分分挣','一分一分挣','钱是一分','一分一分挣出来','靠的是','才是硬道理','吃得苦中苦','人善被人欺']
PARTICLES='啊呢呗吧呀嘛啦哟哩嘞喽哇喔'
UNIT_RE=re.compile(r'\d+\.?\d*[块毛分只条刀亩罐]|[零一二两三四五六七八九十百]+[块毛分只条刀亩罐][零一二三四五六七八九十]*')
SPOKEN_RE=re.compile(r'^<p><b>([^<]+)</b>(（[^）]*）)?[：:](.*?)</p>$')
H2_RE=re.compile(r'<h2>第(\d+)集')
SCENE_RE=re.compile(r'<p><b>(场\d+)[^<]*</b></p>')

def collect(paths):
    files=[]
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p,'*.xml')))
        else:
            files.append(p)
    return files

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('paths',nargs='+')
    ap.add_argument('--tri-min',type=int,default=120)
    ap.add_argument('--cue-ratio',type=float,default=0.8)
    a=ap.parse_args()
    issues=0
    for f in collect(a.paths):
        s=open(f,encoding='utf-8').read()
        ep=(re.findall(H2_RE,s) or ['?'])[0]
        base=os.path.basename(f)
        cur_scene=None; scene_tri=0; scene_hook=False; tri_total=0; spoken=0; cued=0
        scene_seen=[]
        for l in s.splitlines():
            t=l.strip()
            ms=SCENE_RE.search(l)
            if ms:
                if cur_scene is not None and scene_tri==0 and not scene_hook:
                    print('[NO-TRI] %s 集%s %s 无△画面行'%(base,ep,cur_scene)); issues+=1
                cur_scene=ms.group(1); scene_tri=0; scene_hook=False; scene_seen.append(cur_scene)
            if '▷' in l:
                scene_hook=True
            if t.startswith('<p>△'):
                scene_tri+=1
                tri_total+=len(re.sub(r'<[^>]+>','',t).replace('△','').replace('　','').replace(' ',''))
            m=SPOKEN_RE.match(t)
            if m and not t.startswith('▷'):
                hint=m.group(2) or ''; body=m.group(3)
                spoken+=1
                if hint.strip(): cued+=1
                for w in SLOGAN:
                    if w in body:
                        print('[SLOGAN %s] %s 集%s：%s'%(w,base,ep,body[:60])); issues+=1
                nums=UNIT_RE.findall(body)
                if len(nums)>=2 and not any(p in body for p in PARTICLES) and len(body)<22:
                    print('[SUMMARY] %s 集%s 数字罗列摘要腔：%s'%(base,ep,body[:60])); issues+=1
        if cur_scene is not None and scene_tri==0 and not scene_hook:
            print('[NO-TRI] %s 集%s %s 无△画面行'%(base,ep,cur_scene)); issues+=1
        if tri_total < a.tri_min:
            print('[THIN-TRI] %s 集%s △总字%d < %d，画面动作太薄'%(base,ep,tri_total,a.tri_min)); issues+=1
        ratio=cued/spoken if spoken else 0
        if ratio < a.cue_ratio:
            print('[THIN-CUE] %s 集%s 表演提示覆盖 %.0f%% < %.0f%%'%(base,ep,ratio*100,a.cue_ratio*100)); issues+=1
        print('%s 集%s：场%d △字%d 表演覆盖%.0f%%'%(base,ep,len(scene_seen),tri_total,ratio*100))
    print('问题数:',issues)
    return 1 if issues else 0

if __name__=='__main__':
    sys.exit(main())
