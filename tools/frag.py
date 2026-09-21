#!/usr/bin/env python3
"""公開用の断片 as_artifact.html を apng-scope.html から生成する。

断片は <!DOCTYPE> / <html> / <head> / <body> を剥がしたもの。
as_artifact.html は生成物なので手で編集しないこと。必ずこれで作り直す。

    python3 tools/frag.py
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir))

SRC = os.path.join(ROOT, 'apng-scope.html')
DST = os.path.join(ROOT, 'as_artifact.html')


def frag(src, dst, tf=None, tt=None):
    s = io.open(src, encoding='utf-8').read()
    s = re.sub(r'^\s*<!DOCTYPE html>\s*', '', s, flags=re.I)
    s = re.sub(r'</?html[^>]*>\s*', '', s, flags=re.I)
    s = re.sub(r'</?head>\s*', '', s, flags=re.I)
    s = re.sub(r'<body[^>]*>\s*', '', s, flags=re.I)
    s = re.sub(r'</body>\s*', '', s, flags=re.I)
    if tf:
        # 似た行を巻き添えにしないよう、出現回数を必ず確かめる
        assert s.count(tf) == 1, 'title anchor x%d: %r' % (s.count(tf), tf)
        s = s.replace(tf, tt, 1)
    io.open(dst, 'w', encoding='utf-8').write(s.strip() + '\n')
    print('%s -> %s (%d bytes)' % (
        os.path.basename(src), os.path.basename(dst), os.path.getsize(dst)))


if __name__ == '__main__':
    frag(SRC, DST)
