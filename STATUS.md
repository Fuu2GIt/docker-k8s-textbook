# 現状

2026-10-16 時点です。作業は継続中です。

- 静的サイトの骨組みと第1章は、ローカルのブラウザで確認しました。幅 360px、OSタブ、検索、コピー、進捗の保存を含みます。
- Linux で実行したコマンドは、第1章の `uname -s`、`uname -r`、`uname --not-a-real-option` です。出力は本文に貼ってあります。
- Windows の3コマンドは未確認です。一覧は `UNVERIFIED.md` です。
- Docker Engine 29.9.1 は、この環境に入っています。デーモンは systemd が無いため、`dockerd` を直接起動しています。
- GitHub にはログインしていません。`gh auth status` は未ログインで、トークンもありません。リポジトリ `docker-k8s-textbook` は、まだ作れていません。

## 公開するときにやること

認証できるようになったら、次を実行します。

1. `gh auth login`
2. `gh repo create docker-k8s-textbook --public --source=. --remote=origin`
3. `git push -u origin main`
4. GitHub Pages を、`main` ブランチの `/docs` から公開する

Pages の設定画面は、リポジトリの Settings、Pages です。Branch を `main`、Folder を `/docs` にします。
