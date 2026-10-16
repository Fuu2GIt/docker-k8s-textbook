# 現状

2026-10-16 時点です。作業は継続中です。

- 静的サイトの骨組みと第1章は、ローカルのブラウザで確認しました。幅 360px、OSタブ、検索、コピー、進捗の保存を含みます。第2章はビルドとリンク検査まで終わっています。ブラウザの再確認は、全章のあとにもう一度します。
- Linux で実行したコマンドの出力は、各章の本文に貼ってあります。第2章の `systemctl is-active docker` は、この環境では systemd が無く失敗しました。成功時の `active` は未確認です。
- Windows のコマンドは未確認です。一覧は `UNVERIFIED.md` です。
- Docker Engine 29.9.1 は、この環境に入っています。デーモンは systemd が無いため、`dockerd` を直接起動しています。
- GitHub にはログインしていません。`gh auth status` は未ログインで、トークンもありません。リポジトリ `docker-k8s-textbook` は、まだ作れていません。

## 公開するときにやること

認証できるようになったら、次を実行します。

1. `gh auth login`
2. `gh repo create docker-k8s-textbook --public --source=. --remote=origin`
3. `git push -u origin main`
4. GitHub Pages を、`main` ブランチの `/docs` から公開する

Pages の設定画面は、リポジトリの Settings、Pages です。Branch を `main`、Folder を `/docs` にします。
