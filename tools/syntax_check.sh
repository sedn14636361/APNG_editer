#!/usr/bin/env bash
# apng-scope.html を編集したら必ず通すこと。
# <script> は3本あり、1本目=pako、2本目=UPNG.js、3本目がアプリ本体。
# 巨大な1ファイルなので、構文エラーは画面上は無言で消える。
set -euo pipefail
cd "$(dirname "$0")/.."

out="$(mktemp -t app-XXXXXX.js)"
trap 'rm -f "$out"' EXIT

python3 -c "
import io, re, sys
s = io.open('apng-scope.html', encoding='utf-8').read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', s, re.S)
assert len(scripts) == 3, 'script タグが %d 本ある（想定は3本）' % len(scripts)
io.open(sys.argv[1], 'w', encoding='utf-8').write(scripts[-1])
" "$out"

node --check "$out"
echo "OK  apng-scope.html"
