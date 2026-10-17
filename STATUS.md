# 現状

2026-10-17 時点です。第1章から第21章まで、`main` にあります。公開ページは https://fuu2git.github.io/docker-k8s-textbook/ です。

- `python3 scripts/check_site.py --complete` は成功しています。24ページ、第1章から第21章です。
- ブラウザで `http://127.0.0.1:8765/` を開きました。幅 1280px と 360px で、章一覧、OSタブ、検索、進捗の保存、用語集、コマンド早見表を確認しました。コピーボタンは、ブラウザがクリップボードを許可すると「コピーしました」になり、コマンド文字列がコピーされます。
- Linux で実行したコマンドの出力は、各章の本文に貼ってあります。第13章から第21章で新しく「未確認」になったコマンドはありません。
- Windows の手順と、この環境で動かない `systemctl` は未確認です。一覧は `UNVERIFIED.md` です。対象は第1章、第2章、第7章、第8章、第12章です。
- 公式ドキュメントへのリンクは開きました。テイントの旧URLは 404 だったので、`https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/` に直しました。`https://www.gnu.org/software/coreutils/uname` は 403 のままです。記録は `DECISIONS.md` にあります。
- kind のクラスタ `memo` は、第21章の片付けで消しました。`kind get clusters` は `No kind clusters found.` でした。もう一度通すときは、第12章から作ります。
- この環境の kube-proxy は、確認のときだけ nftables に変えています。読者の手順には入れていません。理由は `DECISIONS.md` です。
- GitHub アカウント `Fuu2GIt` でログインし、`main` を https://github.com/Fuu2GIt/docker-k8s-textbook へ送りました。Pages の公開元は `main` の `/docs` です。トップ、第1章、第21章は HTTP 200 でした。

## 公開

公開ページは https://fuu2git.github.io/docker-k8s-textbook/ です。設定画面は、リポジトリの Settings、Pages です。Branch は `main`、Folder は `/docs` です。
