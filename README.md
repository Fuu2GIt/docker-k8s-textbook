# DockerとKubernetesの教科書

コマンドラインをほぼ初めて使う人向けの、手を動かす教科書です。Docker で自作のWebアプリを動かし、Docker Compose でデータベースとまとめ、ローカルの Kubernetes で複数台の起動、更新、障害からの復旧まで進みます。

画面は日本語です。Windows は Docker Desktop と WSL2、Linux は Ubuntu を基準にしています。

## 読む

生成済みの画面は `docs/` にあります。

```bash
python3 -m http.server 8765 --directory docs
```

ブラウザで `http://127.0.0.1:8765/` を開きます。`docs/index.html` をファイルとして直接開いても読めます。

## 作り直す

変換に使うものは Python 3 の標準ライブラリだけです。

```bash
python3 scripts/build.py
python3 scripts/check_site.py
```

章の本文は `book/chapters/` です。`scripts/build.py` が HTML、用語集、コマンド早見表、検索の索引、`UNVERIFIED.md` を作ります。

`python3 scripts/check_site.py --complete` は、第1章から第21章まで揃っているときにだけ成功します。

## 公開

`main` ブランチの `/docs` を GitHub Pages の公開元にします。`docs/.nojekyll` があるので、Jekyll は通りません。

リポジトリの Settings、Pages で、Branch を `main`、Folder を `/docs` にします。公開先は `https://<ユーザー名>.github.io/docker-k8s-textbook/` です。

この作業環境では GitHub にログインできていません。手順の続きは `STATUS.md` にあります。

## サンプル

アプリの実体は `samples/` に置きます。本文のコードと、このディレクトリのファイルは、ビルド時に一致しているかを見ます。
