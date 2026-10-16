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
