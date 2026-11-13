# もじもじぼうけん

未就学〜小学1年向けの文字学習Webアプリ。ひらがな／カタカナを12レベルで段階的に学ぶ。
紹介（もじ）・ことばづくり・チェックの3モードと、五十音表の進捗画面つき。
マスコットはひよこ。

公開ページ: https://yggdrasilw-spec.github.io/mojimoji-bouken/mojimoji_bouken.html

## ファイル構成

- `mojimoji_bouken.html` — **生成物**。直接編集しないこと
- `aiueo_onigiri_v2_template.html` — 本体テンプレート（コードの編集はこちら）
- `img/` — 単語の絵（160点）。`IMG` マップはここへの相対パス参照
- `img_src/` — 生成シートとコンタクトシート（切り出し元）
- `crop_sheet.py` — シート画像の内容ベース切り出しスクリプト
- `build.py` — ビルドスクリプト
- `tests/test_harness.js` — 自動テスト（DOMスタブによる不変条件チェック）
- `aiueo_onigiri.html` / `aiueo_onigiri_v2.html` — 旧バージョン（あいうえおにぎり時代）

## ビルド

```sh
python3 build.py           # 通常ビルド（画像は外部ファイル参照、GitHub Pages用）
python3 build.py --embed   # 単一HTMLビルド（画像をbase64埋め込み、オフライン配布用）
```

編集ルール：修正はテンプレートと `img/` に対して行い、`build.py` で再ビルドする。
生成HTMLを直接編集すると、次の再ビルドで上書きされて消える。

## テスト

```sh
# テンプレートからビルド後、生成HTMLのスクリプトを tests/test_harness.js の
# /*__APP_SCRIPT__*/ 位置に差し込んで node で実行する
```
