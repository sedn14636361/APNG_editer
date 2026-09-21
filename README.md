# APNG SCOPE

アニメーションPNGを重ねて、コマ単位で編集して、書き出すツールです。
**ビルド工程はありません。** `apng-scope.html` をブラウザで直接開けばそのまま動きます。
npm も bundler も使いません。

👉 **[sedn14636361.github.io/APNG_editer](https://sedn14636361.github.io/APNG_editer/)**

## できること

- APNG / PNG / GIF を読み込んでレイヤーにする（複数選べばそのまま重なる）
- レイヤーごとの位置・大きさ・不透明度・合成モード
- **コマ個別の上書き** — フレーム単位での差し替え
- **表示区間とフェード** — 台形カーブを数値で作る
- **不透明度カーブのグラフ** — 点を直接ドラッグして編集
- 多段トラックのタイムライン
- APNG / PNG 書き出し（5MB以下に収める圧縮つき）

## ファイル

| ファイル | 役割 |
|---|---|
| `apng-scope.html` | **本体。これが正。** 2702行の単一HTML |
| `as_artifact.html` | `<!DOCTYPE>`〜`<body>` を剥がした公開用の断片。**生成物なので手で編集しない** |
| `tools/frag.py` | 断片を生成する |
| `tools/syntax_check.sh` | 本体の構文チェック |

`index.html` はリポジトリに置いていません。GitHub Pages へ上げるときに workflow が
`apng-scope.html` を複製して作ります。本体のファイル名を唯一の正に保つためです。

## 編集の流れ

巨大な1ファイルなので、アンカー文字列で置換する形で編集し、**置換前に出現回数を必ず確かめて**ください。
似た行を巻き添えで書き換える事故が防げます。

```bash
tools/syntax_check.sh     # 1. 構文チェック（編集後に必ず）
python3 tools/frag.py     # 2. 断片を作り直す
```

この2つは `main` への push 時に CI でも回ります。断片が本体と食い違っていると失敗します。

## 構造

```
読み込み              APNG/PNG/GIFを読んでレイヤー化
コマ個別の上書き       フレーム単位の差し替え
表示区間とフェード      curveOf / curveAlpha / fadeAlpha / curveFromFade / ensureFramesFor
合成                  レイヤーを1枚に焼く
レイヤーUI
不透明度カーブのグラフ   drawCurve / bindCurve / curveGeom / curveHit / curveCommit
タイムライン           多段トラック表示 tlKey / compChips / rebuildTimeline / drawThumbs
ドキュメント / 再生 / ファイル入力
書き出し              5MB以下に収める圧縮
```

レイヤーの形:

```js
{ id, name, w, h, canvases, srcDelays, animated, visible, opacity, blend,
  x, y, dw, dh, lockAspect, fit,
  init:{...},                       // リセット用の初期状態
  fade:{inAt,inLen,outAt,outLen,ease},
  curve:[{f,v}] }                   // ★ 不透明度の真の出どころはこの curve
```

## 破ってはいけない約束

**すべて実測で痛い目を見た結果です。理由なく変えないでください。**

1. **不透明度の正は `curve` であって `fade` ではない。**
   `fade` の数値欄は `#fdApply` を押したときだけ `curveFromFade()` が台形カーブを作って
   `curve` に流し込みます。数値欄は**即時反映しません**。
   テストスクリプトを書くときはここを間違えないでください（過去に一度踏みました）。

2. **レイヤーパネルは `column-reverse`。** タイムラインは `[...D.layers].reverse()` で
   並べて見た目を一致させています。片方だけ直すと順序がひっくり返ります。

3. **UPNG は `blend=0`（SOURCE）を必ず書く**ようにパッチ済み（`UPNG.encode` 内、
   `blend = 0;` の直前に経緯のコメントあり）。`blend_op=OVER` のAPNGは読み手によって
   結果が割れます（Pillow がα43を43²/255と解釈しました）。
   フェードはまさに「透明の次に半透明のコマ」を作るので、このツールでは特に効きます。
   自作のチャンクパーサで「ファイル自体は正しい」と確認したうえで、割れない書き方に寄せました。
   ファイルも小さくなります。

4. **減色は最後の手段。** 5MBに収めるときは、まず可逆のまま縮小し、そこまでで収まらないときだけ
   256色に落とします。落とす直前に 4×4 Bayer ディザを必ず掛けます。掛けないと帯が出ます。

5. **UIを切ってあるときは `disabled` を立てる。**
   `pointer-events:none` だけだとキーボードで到達して操作できてしまいます。

## 検証のやり方

**推測でなく数値で確かめてください。** JSの例外は画面上は無言で消えるので、`pageerror` を必ず拾うこと。

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={'width':1500,'height':1000})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file:///.../apng-scope.html'); pg.wait_for_timeout(700)
    print(pg.evaluate("() => D.layers.length"), errs)
    b.close()
```

不透明度を検証するときは `fade` の数値欄ではなく `curve` を見ること（約束1）。

### APNGの独立検証

**Pillow を信用しきらないでください。** 過去に Pillow と UPNG の言い分が割れ、
`acTL` / `fcTL` / `fdAT` を自前で読む Python スクリプトを書いて決着させました。
同じ状況になったら同じ手を使ってください。

## 過去に踏んだ罠

| 症状 | 原因 | 直し方 |
|---|---|---|
| APNGの半透明が他ツールで濃く出る | `blend_op=OVER` | UPNGを `blend=0` に |
| フェードの数値を変えても絵が変わらない | `fade` は `#fdApply` を押すまで `curve` に入らない | 仕様。`curve` を直接見る |
| コマ送りがトラック行をスクロールする | 多段タイムライン化で対象がずれた | `compChips()[D.cur]` |
| 輪のドラッグが1/6しか動かない | 再描画のたびに要素を作り直していた | `dragging` フラグ中は位置だけ更新 |
| タイムラインの順序がレイヤーパネルと逆 | `column-reverse` を考慮していない | `[...D.layers].reverse()` |

## 同梱しているライブラリ

どちらも本体HTMLの中に貼り込んであります（`<script>` の1本目と2本目）。**別ファイルとしては読み込みません。**

| ライブラリ | 版 | ライセンス | 上流 |
|---|---|---|---|
| pako | 3.0.1 | MIT / Zlib | https://github.com/nodeca/pako |
| UPNG.js | — | MIT | https://github.com/photopea/UPNG.js |

UPNG.js には上記「約束3」の `blend=0` パッチを当ててあります。**上流版とは異なります。**
MITライセンス全文はまだ同梱していません（ヘッダコメントに表示とURLのみ）。
MITは全文の同梱を求めるので、`THIRD-PARTY-NOTICES.md` を置くのが本来です。
