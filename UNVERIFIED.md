# 未確認のコマンド

このファイルは `scripts/build.py` が章から作ります。手で直しても、次のビルドで上書きされます。

「未確認」は、そのコマンドをこの執筆環境で実行していない、という意味です。期待する出力の欄に、想像の結果は書いていません。

## 第1章 コンテナとは何か

- 場所: Windows

```text
Get-ComputerInfo -Property WindowsProductName
```

- 場所: Windows

```text
Get-ComputerInfo -Property OsVersion
```

- 場所: Windows

```text
Get-ComputerInfo -NotARealOption
```

## 第2章 環境を整える

- 場所: Windows

```text
wsl --version
```

- 場所: Windows

```text
wsl --install
```

- 場所: Windows

```text
wsl --update
```

- 場所: Windows

```text
wsl.exe --set-default-version 2
```

- 場所: Windows

```text
wsl.exe --list --online
```

- 場所: Windows

```text
wsl.exe --install -d Ubuntu
```

- 場所: Windows

```text
wsl.exe --set-version Ubuntu 2
```

- 場所: Windows

```text
wsl.exe --list --verbose
```

- 場所: Windows

```text
Start-Process 'Docker Desktop Installer.exe' -Wait -ArgumentList 'install', '--user'
```

- 場所: Windows

```text
wsl docker version
```

- 場所: Windows

```text
wsl docker compose version
```

- 場所: Windows

```text
wsl pwd
```

- 場所: Windows

```text
wsl docker run --rm hello-world
```

- 場所: Linux

```text
sudo systemctl is-active docker
```

- 場所: Windows

```text
wsl docker run --rm textbook-no-such-image:none
```

## 第7章 ポートとネットワーク

- 場所: Windows

```text
Invoke-WebRequest -Uri http://localhost:8000/ -UseBasicParsing
```

- 場所: Windows

```text
Invoke-WebRequest -Uri http://localhost:59999/ -UseBasicParsing
```

## 第8章 データを残す

- 場所: Windows

```text
New-Item -ItemType Directory -Force -Path "$HOME\docker-learn\ch08"
```

- 場所: Windows

```text
Set-Content -Path "$HOME\docker-learn\ch08\note.txt" -Value "ホストのファイル" -Encoding utf8
```

- 場所: Windows

```text
docker run --rm --mount "type=bind,source=$HOME\docker-learn\ch08,target=/data" busybox:1.37.0 cat /data/note.txt
```

- 場所: Windows

```text
Format-Hex -Path "$HOME\docker-learn\ch08\note.txt"
```

- 場所: Windows

```text
docker run --rm --mount "type=bind,source=$HOME\docker-learn\ch08\missing,target=/data" busybox:1.37.0 ls /data
```

- 場所: Windows

```text
Remove-Item -Recurse -Force -Path "$HOME\docker-learn\ch08"
```
