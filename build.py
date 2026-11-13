#!/usr/bin/env python3
"""もじもじぼうけん ビルドスクリプト

テンプレート（aiueo_onigiri_v2_template.html）から mojimoji_bouken.html を生成する。

使い方:
  python3 build.py            画像を外部ファイル参照（img/<id>.jpg）でビルド（通常はこちら）
  python3 build.py --embed    画像を base64 で埋め込んだ単一HTMLでビルド（オフライン配布用）

編集ルール: 生成物の mojimoji_bouken.html を直接編集しないこと。
修正はテンプレートと img/ に対して行い、このスクリプトで再ビルドする。
"""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "aiueo_onigiri_v2_template.html")
IMG_DIR = os.path.join(HERE, "img")
OUT = os.path.join(HERE, "mojimoji_bouken.html")
PLACEHOLDER = "/*__IMG_DATA__*/{}"


def main():
    embed = "--embed" in sys.argv
    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()
    if PLACEHOLDER not in tpl:
        raise SystemExit("テンプレートに画像プレースホルダが見つかりません")
    img = {}
    for fn in sorted(os.listdir(IMG_DIR)):
        if fn.endswith(".jpg"):
            wid = fn[:-4]
            if embed:
                with open(os.path.join(IMG_DIR, fn), "rb") as f:
                    img[wid] = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
            else:
                img[wid] = "img/" + fn
    out = tpl.replace(PLACEHOLDER, json.dumps(img, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    mode = "embed（単一HTML）" if embed else "external（画像は外部ファイル）"
    print(f"built mojimoji_bouken.html [{mode}]: {len(img)} images, {os.path.getsize(OUT)} bytes")


if __name__ == "__main__":
    main()
