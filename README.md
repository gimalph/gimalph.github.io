# 儀間達也の研究者個人サイト

Hugo 0.169.0 とリポジトリ内のテンプレート、CSS で生成する日英の静的サイトです。本文は Markdown、研究業績・研究費・職歴・受賞歴・追加のお知らせは YAML で管理します。数式はビルド時に MathML に変換します。Python はデータ検証とテストに使い、サイトの HTML は Hugo が生成します。

## ローカルでの確認

[Hugo 0.169.0](https://github.com/gohugoio/hugo/releases/tag/v0.169.0) と Python 3.9 以降を用意します。CI では Python 3.12 を使用します。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/validate_data.py
hugo server
```

ブラウザーで [日本語版](http://localhost:1313/) または [英語版](http://localhost:1313/en/) を開きます。研究業績は `/research/` と `/en/research/`、研究費は `/funding/` と `/en/funding/` です。公開用のビルドと回帰テストは次のコマンドで実行できます。

```bash
python -B -m unittest discover -s tests -v
hugo --gc --minify --printPathWarnings --printI18nWarnings --panicOnWarning
```

日本語の本文は `content/`、英語の本文は `content/en/` にあります。対応する日英ページには同じファイル名を使います。公開成果物は `public/` に生成されます。

## 論文を追加・更新する

`data/publications.yml` の該当分類（`conference`、`journal`、`arxiv`、`workshop`、`domestic`）に追加します。論文一覧は各分類のファイル内の順番を使うため、新しいものは通常先頭に追加します。以下は架空の会議論文です。

```yaml
conference:
  - id: example-2026
    title: "Example Paper"
    author:
      - "Tatsuya Gima"
      - "Author B"
    booktitle: "Example Conference 2026"
    year: "2026"
    accepted_on: "2026-06-15"
```

- `id` は分類をまたいで一意にします。英数字で始め、英数字・ハイフン・アンダースコアを使えます。題名や DOI を変更しても ID は維持します。
- 採択通知を受けたら、確認した日を `accepted_on` に入力します。正式なオンライン版の公開日と DOI が確認できたら、同じレコードに `online_on: "2026-09-10"` と `doi: "https://doi.org/…"` を追加します。それぞれが独立した News になります。
- 日付は引用符付きの `YYYY-MM-DD` で入力します。日が分からなければ日付欄を省略します。書誌上の `year` や `month` は論文一覧で使います。
- 論文誌名は `journal`、会議名は `booktitle` を使用します。巻 `volume`、号 `issue`、ページ `pages`、`arxiv` URL などは確認できたものを追加します。タイトル内のインライン数式は `$…$` で囲みます。
- 会議版・論文誌版・プレプリントはそれぞれ別レコードにします。関係を確認できたものは `related_publication_ids: [example-journal-2027]` のように相手の既存 ID を指定します。片方向の登録で構いません。各レコードは `#publication-<id>` で参照できます。

Web サイトとは別に、`python papers_to_tex.py` で `list.tex` を生成できます。

## 研究費を追加する

`data/funding.yml` はリストです。初期値の `[]` を置き換えて項目を追加します。課題名 `title` は必須です。`agency`、`period`、`role`、`number`、`url` は分かる範囲で入力します。英語表記には `title_en`、`agency_en`、`period_en`、`role_en` を使えます。`accepted_on` に採択日を入力すると News にも掲載されます。

```yaml
- title: "研究課題の例"
  title_en: "Example Research Project"
  agency: "助成機関の例"
  period: "2026–2028年度"
  role: "研究代表者"
  number: "EXAMPLE-01"
  accepted_on: "2026-06-15"
```

## News の生成

| データ | イベントを生成する欄 |
| --- | --- |
| `data/publications.yml` | `accepted_on`（採択）、`online_on`（公開） |
| `data/funding.yml` | `accepted_on`（採択） |
| `data/positions.yml` | `started_on`（着任） |
| `data/awards.yml` | `received_on`（受賞） |
| `data/news_extra.yml` | `date`（自由記述。本文は `text_ja` と `text_en`、リンクは任意の `url`） |

職歴は `positions.yml` の `title`、受賞歴は `awards.yml` の `award` を編集します。任意の英語表記は `title_en` と `award_en` です。日まで分からない既存の記録は `year` と `month` で CV に表示します。職歴の終了年月には `end_year` と `end_month` を使えます。

表示は東京時間のビルド日を基準に、新しい日付順です。同日は上のデータ種別順、同じ種別では YAML の記載順です。論文は同日に限り、会議・論文誌・プレプリント・ワークショップ・国内発表の順です。未来の日付は公開対象から外れます。年月は閲覧言語に合わせ、年の境目に見出しを表示します。

ホームの `{{< recent-news limit=5 months=12 >}}` は、当日を含む直近12か月から最大5件を表示します。News ページは公開対象の全件と、従来の手書きのアーカイブを掲載します。既存の記録はアーカイブにまとめています。後からアーカイブの記録を YAML に移すときは、同じイベントが二重に掲載されないよう、そのアーカイブ行も同じ変更で整理してください。

共通の文面は `i18n/ja.yaml` と `i18n/en.yaml` で変更できます。文面を直す際は `{{ .title }}` などの差し込み名を維持します。リンク先は YAML で設定します。

## 検証と公開

`python scripts/validate_data.py` は `schemas/` の JSON Schema と追加の整合性チェックを実行します。エラーに表示されたファイル・ID・項目を確認して修正してください。VS Code で YAML Language Server を使用している場合は、各 YAML 冒頭のコメントからスキーマを参照できます。

作業ブランチを GitHub に push し、Pull Request を作成します。GitHub Actions がデータ検証・回帰テスト・Hugo ビルドを実行します。公開元はリポジトリの **Settings → Pages → Build and deployment → Source → GitHub Actions** です。`master` が更新されると、同じチェックが成功したビルドを GitHub Pages に公開します。[GitHub Pages の設定手順](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

直近12か月の範囲や未来日の判定は、最後に公開したビルド時点のものです。`master` 更新時のみ公開する要件に合わせ、定期実行は設定していません。将来定期公開を導入する場合、GitHub Actions の `schedule` は既定ブランチ上で動作し、混雑時に遅延や実行の省略があり、公開リポジトリでは60日間活動がないと停止します。[定期実行の仕様](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
