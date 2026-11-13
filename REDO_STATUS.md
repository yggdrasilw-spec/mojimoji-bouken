# 画像全作り直し（グリッド先行方式）進捗 — 2026-11-13

## 状態：完了（全80点＋ざっし単独修正をアプリへ反映済み、テスト117,305件全通過）

- 新方式で再生成・切り出し・検証済みの64点は `img_new/` にある（シート1〜4）。
- アプリ（aiueo_onigiri_v2.html）の画像はまだ差し替えていない。全80点そろってから一括で差し替える（絵柄の混在を避けるため）。
- 文16場面は差し替え済み（グリッド先行・第1弾）。

## 残り：シート5の16点

対象（この順で4x4生成）：rousoku, tebukuro, geemu, suzume / bentou, shokupan, juusu, jourou / hyou, ryokan, gyouza, kyabetsu / kyouryuu, shuukuriimu, chuurippu, konnyaku

手順：
1. `img_src/grid_template_4x4.png` を入力に渡して生成（プロンプト形式はシート1〜4と同一）
2. 罫線位置を実測（400/800/1200 から数px以内か）
3. `python3 crop_sheet.py <sheet> rousoku,tebukuro,geemu,suzume,bentou,shokupan,juusu,jourou,hyou,ryokan,gyouza,kyabetsu,kyouryuu,shuukuriimu,chuurippu,konnyaku img_new`
4. コンタクトシートで目視検証
5. `img_new/` の80点を `img/` にコピー（文16点は現行のまま）→ 再ビルド → テスト → 納品

## 検証メモ（シート1〜4）

- 罫線のずれは全シート4px以内。
- 旧版の問題点はすべて解消：かさ（犬の足跡）、きのこ、くじら（下の線）、ちょうちょう（紫の点）、ワニ（上の破片）、じゃがいも。
- たんぽぽは綿毛→黄色い花に修正済み。ふね（モーターボート）とよっと（帆船）が区別できるようになった。
- 唯一の境界例：ざっしが「開いた本」の絵で、雑誌らしさが弱い。要再生成なら単独で。
