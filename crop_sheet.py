#!/usr/bin/env python3
"""グリッドシート画像を「内容ベース」で切り出す（v2: 連結成分フィルタ付き）。

使い方:
  python3 crop_sheet.py SHEET画像 名前1,名前2,... 出力dir [--rows 4] [--cols 4] [--size 360] [--pad 0.07]

なぜこの手順か:
  生成シートは見た目が均一なグリッドでも、実際には (a) 対象の大きさ・位置がセルごとにばらつく、
  (b) 隣のセルの対象の一部（足先・しぶき等）がセル境界を越えて入り込む、ことがある。
  固定グリッドで切ると余白がばらつき、内容ベースで外接矩形を取ると隣の破片まで拾って対象が小さくなる。
  そこで:
  1. セルごとに「白でないピクセル」を連結成分に分解する
  2. 最大の成分を本体とし、「面積が本体の2%以上」または「本体の近く(18px以内)」の成分だけを残す
     （本体の一部＝クジラの潮吹き等は残り、遠くて小さい隣の破片は落ちる）
  3. 残した成分の外接矩形に余白を足して切り出す（セルの外には絶対にはみ出さない）
  4. 正方形の白キャンバスの中央に配置し、決まったサイズにそろえる
  5. 外接矩形がセル端に接する場合は警告（元画像で対象自体が欠けている疑い）
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageChops
from scipy import ndimage


def content_bbox(cell: Image.Image, thresh: int = 12, near_px: int = 18, min_frac: float = 0.02, pad: float = 0.07):
    white = Image.new("RGB", cell.size, (255, 255, 255))
    diff = np.asarray(ImageChops.difference(cell, white).convert("L"))
    mask = diff > thresh
    # セルの外周はグリッド線（罫線）が描かれていることがあるため検出対象から外す
    INSET = 6
    mask[:INSET, :] = False; mask[-INSET:, :] = False
    mask[:, :INSET] = False; mask[:, -INSET:] = False
    if not mask.any():
        return None
    lab, n = ndimage.label(mask, structure=np.ones((3, 3), int))
    objs = ndimage.find_objects(lab)
    areas = ndimage.sum_labels(mask, lab, index=np.arange(1, n + 1))
    # グリッドの罫線は「セル全体に広がる中空の枠」状の成分になる。本体と誤認しないよう除外する
    def is_frame(i):
        yy, xx = objs[i]
        bw, bh = xx.stop - xx.start, yy.stop - yy.start
        return bw >= 0.9 * cell.width and bh >= 0.9 * cell.height and areas[i] <= 0.10 * bw * bh
    frames = {i for i in range(n) if is_frame(i)}
    main = max((i for i in range(n) if i not in frames), key=lambda i: areas[i])
    my, mx = objs[main]
    main_area = areas[main]
    keep = [main]
    for i in range(n):
        if i == main or i in frames:
            continue
        y, x = objs[i]
        dx = max(0, max(mx.start - x.stop, x.start - mx.stop))
        dy = max(0, max(my.start - y.stop, y.start - my.stop))
        if areas[i] >= min_frac * main_area or (dx <= near_px and dy <= near_px):
            keep.append(i)
    x0 = min(objs[i][1].start for i in keep); x1 = max(objs[i][1].stop for i in keep)
    y0 = min(objs[i][0].start for i in keep); y1 = max(objs[i][0].stop for i in keep)
    # 端のゴミ取り（帯トリム）: 内容を行（列）方向の「帯」に分け、端の帯が
    # 薄い・白い溝で離れている・面積が小さい、をすべて満たすときだけ隣セルの破片とみなして落とす。
    # 本体の一部（クジラの潮吹き=厚い帯、ロウソクの炎=つながっている）は残る。
    kept_mask = np.isin(lab, [i + 1 for i in keep])
    total = kept_mask.sum()

    def bands_of(indices):
        if len(indices) == 0:
            return []
        out = []
        s = p = indices[0]
        for v in indices[1:]:
            if v - p >= 4:
                out.append((s, p)); s = v
            p = v
        out.append((s, p))
        return out

    def trim_axis(bbox, axis):
        x0, y0, x1, y1 = bbox
        sub = kept_mask[y0:y1, x0:x1]
        if sub.size == 0:
            return bbox
        proj = np.where(sub.any(axis=axis))[0]  # axis=1 -> rows, axis=0 -> cols
        bands = bands_of(proj)
        if len(bands) < 2:
            return bbox
        total_sub = sub.sum()
        def band_area(b):
            return sub[b[0]:b[1] + 1].sum() if axis == 1 else sub[:, b[0]:b[1] + 1].sum()
        first, second = bands[0], bands[1]
        gap = second[0] - first[1]; thick = first[1] - first[0] + 1
        if thick <= 28 and gap >= 14 and band_area(first) <= 0.06 * total_sub:
            cut = first[1] + gap // 2
            if axis == 1: y0 += cut + 1
            else: x0 += cut + 1
            sub = kept_mask[y0:y1, x0:x1]
            proj = np.where(sub.any(axis=axis))[0]
            bands = bands_of(proj)
            if len(bands) < 2:
                return (x0, y0, x1, y1)
            total_sub = sub.sum()
        last, prevb = bands[-1], bands[-2]
        gap = last[0] - prevb[1]; thick = last[1] - last[0] + 1
        min_gap = 8 if axis == 1 else 14  # 下端は薄い線状の破片が多いので少し緩める
        if thick <= 28 and gap >= min_gap and band_area(last) <= 0.06 * total_sub:
            cut = prevb[1] + gap // 2
            if axis == 1: y1 = y0 + cut + 1
            else: x1 = x0 + cut + 1
        return (x0, y0, x1, y1)

    # 先に余白を足してからトリムする（トリム後に余白を足すと、落とした破片をまた拾ってしまう）
    # 余白側もグリッド線の帯（外周6px）には踏み込まない
    m = int(max(x1 - x0, y1 - y0) * pad)
    bbox = (max(6, x0 - m), max(6, y0 - m), min(cell.width - 6, x1 + m), min(cell.height - 6, y1 + m))
    bbox = trim_axis(bbox, 1)
    bbox = trim_axis(bbox, 0)
    return bbox


def crop_sheet(sheet_path, names, outdir, rows=4, cols=4, size=360, pad=0.07):
    src = Image.open(sheet_path).convert("RGB")
    W, H = src.size
    cw, ch = W / cols, H / rows
    if len(names) != rows * cols:
        raise SystemExit(f"名前の数が {rows * cols} ではありません: {len(names)}")
    os.makedirs(outdir, exist_ok=True)
    warnings = []
    for i, name in enumerate(names):
        r, c = divmod(i, cols)
        cell = src.crop((int(c * cw), int(r * ch), int((c + 1) * cw), int((r + 1) * ch)))
        bbox = content_bbox(cell, pad=pad)
        if bbox is None:
            warnings.append(f"{name}: 内容が検出できません（真っ白）")
            continue
        x0, y0, x1, y1 = bbox
        if x0 <= 2 or y0 <= 2 or x1 >= cell.width - 2 or y1 >= cell.height - 2:
            warnings.append(f"{name}: 内容がセル端に接しています（欠けの疑い） bbox={bbox}")
        obj = cell.crop((x0, y0, x1, y1))
        side = max(obj.width, obj.height)
        canvas = Image.new("RGB", (side, side), (255, 255, 255))
        canvas.paste(obj, ((side - obj.width) // 2, (side - obj.height) // 2))
        canvas = canvas.resize((size, size), Image.LANCZOS)
        out = os.path.join(outdir, name + ".jpg")
        canvas.save(out, quality=78)
        print(f"{name}: bbox={bbox} -> {out} ({os.path.getsize(out)} bytes)")
    for w in warnings:
        print("WARN:", w, file=sys.stderr)
    return warnings


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("names")
    ap.add_argument("outdir")
    ap.add_argument("--rows", type=int, default=4)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--size", type=int, default=360)
    ap.add_argument("--pad", type=float, default=0.07)
    a = ap.parse_args()
    crop_sheet(a.sheet, a.names.split(","), a.outdir, a.rows, a.cols, a.size, a.pad)
