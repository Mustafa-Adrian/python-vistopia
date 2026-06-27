# python-vistopia 中文使用指南

`python-vistopia` 是一个命令行工具，用来访问看理想 Vistopia 的节目 API，并把已授权可访问的音频或文稿保存到本地。


## 注意事项
- 本项目不负责提供 token，token只能通过注册官方账号获得；付费内容需要付费订阅相关内容才能获得授权。
- 请只下载你自己有权访问的内容。
- 请勿传播下载后的音频、文稿或 API token。
- 某些公开节目可能不需要 token，但大多数已购或会员内容都需要 token。

## 安装

在项目根目录执行：

```powershell
pip install .
```

如果你直接在项目根目录用 `python -m vistopia.main ...` 运行，改完代码后通常不需要重新安装。只有使用安装后的命令入口，或在其他目录调用包时，才需要重新 `pip install .`。

## Quickstart

### 1. 查看命令帮助

```powershell
python -m vistopia.main --help
```

查看 `save-show` 的详细参数：

```powershell
python -m vistopia.main save-show --help
```

### 2. 搜索节目

```powershell
python -m vistopia.main --token [token] search --keyword [keyword]
```

输出中会包含节目 ID。后续下载需要用到这个 ID。

### 3. 查看节目目录

```powershell
python -m vistopia.main --token [token] show-content --id [id]
```

这会显示节目标题、作者和章节列表。

### 4. 下载单个节目

```powershell
python -m vistopia.main --token [token] save-show --id [id]
```

下载完成后，当前目录下会出现一个以节目标题命名的文件夹，例如：

```text
我是占位符/
```

里面会包含音频文件，以及：

- `playlist.m3u8`：播放列表，适合交给播放器按节目顺序播放。
- `catalog.tsv`：人看的目录表，方便对照播放顺序、标题、文件名和 API 原始排序号。

### 5. 网络中断后继续下载

推荐使用：

```powershell
python -m vistopia.main --token [token] save-show --id [id] --skip-existing
```

`--skip-existing` 会跳过已经存在且非空的 `.mp3` 文件，继续下载缺失内容。

下载时会先写入 `.mp3.part` 临时文件，成功后再改名为 `.mp3`。这样可以减少中断时留下“看起来存在但其实没下载完”的文件。

### 6. 只生成目录和播放列表

如果节目已经下载过，只想补一个目录或播放列表：

```powershell
python -m vistopia.main --token [token] save-show --id [id] --playlist-only
```

这个命令只生成或刷新 `playlist.m3u8` 和 `catalog.tsv`，不会下载音频，也不会写 ID3 标签。

### 7. 批量处理多个节目

```powershell
python -m vistopia.main --token [token] save-show --id-list 1-3,8,10 --skip-existing
```

`--id-list` 支持和 `--episode-id` 类似的范围写法：

```text
1-3,8,10
```

表示节目 ID：`1, 2, 3, 8, 10`。

## 常用命令

### 列出已订阅节目

```powershell
python -m vistopia.main --token [token] subscriptions
```

### 搜索节目

```powershell
python -m vistopia.main --token [token] search --keyword [keyword]
```

### 查看节目内容

```powershell
python -m vistopia.main --token [token] show-content --id [id]
```

### 下载节目音频

```powershell
python -m vistopia.main --token [token] save-show --id [id]
```

### 下载部分章节

```powershell
python -m vistopia.main --token [token] save-show --id [id] --episode-id 1-3,8,10
```

注意：`--episode-id` 只能和单个 `--id` 一起使用，不能和 `--id-list` 一起使用。

### 下载文稿

```powershell
python -m vistopia.main --token [token] save-transcript --id [id]
```

### 下载部分文稿

```powershell
python -m vistopia.main --token [token] save-transcript --id [id] --episode-id 1-3,8,10
```

## save-show 参数详解

`save-show` 是最常用的下载音频命令。

基本格式：

```powershell
python -m vistopia.main --token [token] save-show [options]
```

### `--id`

下载单个节目。

```powershell
python -m vistopia.main --token [token] save-show --id [id]
```

### `--id-list`

批量下载多个节目。

```powershell
python -m vistopia.main --token [token] save-show --id-list 1-3,8,10
```

`--id` 和 `--id-list` 必须二选一，不能同时使用。

### `--episode-id`

只下载某个节目中的部分章节。

```powershell
python -m vistopia.main --token [token] save-show --id [id] --episode-id 1-3,8,10
```

`--episode-id` 只能搭配 `--id` 使用，不能搭配 `--id-list`。因为不同节目的 episode 编号含义不同，混在一起容易产生歧义。

### `--skip-existing`

跳过已经存在且非空的 `.mp3` 文件。

```powershell
python -m vistopia.main --token [token] save-show --id [id] --skip-existing
```

这是网络中断后继续下载时最推荐的参数。

### `--skip-first`

跳过前 N 个匹配到的条目。

```powershell
python -m vistopia.main --token [token] save-show --id [id] --skip-first 200
```

这个参数适合你明确知道前 N 个条目已经处理完的情况。多数情况下，续跑更推荐用 `--skip-existing`。

### `--playlist-only`

只生成或刷新目录文件，不下载、不打标签。

```powershell
python -m vistopia.main --token [token] save-show --id [id] --playlist-only
```

也可以批量生成目录：

```powershell
python -m vistopia.main --token [token] save-show --id-list 1-3,8,10 --playlist-only
```

### `--no-tag`

不写入 ID3 标签。

```powershell
python -m vistopia.main --token [token] save-show --id [id] --no-tag
```

默认情况下，工具会尝试写入标题、专辑、作者、曲目编号等 ID3 信息。

## 下载日志怎么看

下载时会输出 show 级别和 episode 级别的日志。示例：

```text
Show 2/3 started: id=101
Wrote playlist: demo-show\playlist.m3u8
Wrote catalog: demo-show\catalog.tsv
Show 2/3 catalog ready: id=101, title=demo-show, episodes=2
Show 2/3 episode 1/2 skipped existing: api_sort_number=04, file=demo-show\04. lesson.mp3
Show 2/3 episode 2/2 downloading: api_sort_number=06, title=05. lesson
Show 2/3 episode 2/2 saved: file=demo-show\05. lesson.mp3
Show 2/3 completed: id=101, title=demo-show
```

如果网络卡住，通常看最后一条 `downloading` 日志即可判断：

- 当前处理第几个节目。
- 当前节目 ID 是多少。
- 当前节目标题是什么。
- 当前卡在哪个 episode。
- 卡住的 episode 标题是什么。

## 输出文件说明

### 音频文件

音频文件名来自 API 返回的标题，但会经过 `sanitize_filename()` 处理，以便在 Windows、macOS、Linux 上作为合法文件名使用。

例如标题里如果有 `:`、`?`、`/` 等特殊字符，最终文件名可能会被简化或替换。

### `playlist.m3u8`

播放器使用的播放列表，按 API 返回的节目顺序写入。

示例：

```text
#EXTM3U
#EXTINF:-1,04. lesson
04. lesson.mp3
#EXTINF:-1,05. lesson
05. lesson.mp3
```

多数播放器可以直接打开这个文件，按节目顺序播放。

### `catalog.tsv`

给人看的目录表，使用 tab 分隔。当前列为：

```text
index	title	api_sort_number	filename
```

含义：

- `index`：本地连续序号，更适合人阅读和播放顺序判断。
- `title`：API 返回的原始标题。
- `api_sort_number`：API 返回的原始排序号，可能跳号。
- `filename`：实际保存到本地的文件名。

`api_sort_number` 有时会跳号，这通常不代表播放顺序错了。它更像平台内部排序号，可能包含隐藏、下架、番外、试听或其他非正课条目的影响。判断播放顺序时优先看 `index` 和 `playlist.m3u8`。

## save-transcript 参数详解

### 保存普通文稿

```powershell
python -m vistopia.main --token [token] save-transcript --id [id]
```

### 保存部分文稿

```powershell
python -m vistopia.main --token [token] save-transcript --id [id] --episode-id 1-3,8,10
```

### 使用 SingleFile 保存完整网页

如果你想保存更完整的网页内容，可以使用 SingleFile CLI。

1. 下载 SingleFile CLI。
2. 在浏览器登录看理想网页版，并导出 cookie 文件。
3. 执行：

```powershell
python -m vistopia.main --token [token] save-transcript --id [id] `
    --single-file-exec-path C:\path\to\single-file `
    --cookie-file-path C:\path\to\vistopia.cookie
```

## token 的使用方式

可以直接传入：

```powershell
python -m vistopia.main --token [token] subscriptions
```

也可以通过环境变量设置：

```powershell
$env:VISTOPIA_API_TOKEN="[token]"
python -m vistopia.main subscriptions
```

如果命令行参数和环境变量都提供了 token，命令行参数优先。

## 常见问题

### 我改了代码，需要重新安装吗？

如果你在项目根目录使用：

```powershell
python -m vistopia.main ...
```

通常不需要。

如果你使用安装后的命令入口，或在其他目录调用这个包，则需要重新执行：

```powershell
pip install .
```

### 下载到一半断了怎么办？

重新运行：

```powershell
python -m vistopia.main --token [token] save-show --id [id] --skip-existing
```

它会跳过已经存在且非空的文件，继续下载缺失文件。

### 文件名排序和播放顺序不一致怎么办？

使用节目目录里的 `playlist.m3u8` 播放，或者查看 `catalog.tsv` 中的 `index` 列。

文件名通常来自标题，文件管理器会按字典序排序，不一定等于节目播放顺序。

### `api_sort_number` 为什么会跳号？

这是 API 返回的原始排序号，不一定等于人类理解的“第几讲”或“第几集”。平台内部可能存在隐藏、下架、番外、试听或插入条目，因此它可能跳号。

本地播放顺序以 `catalog.tsv` 的 `index` 和 `playlist.m3u8` 为准。

### 可以同时指定 `--id-list` 和 `--episode-id` 吗？

不可以。

`--episode-id` 只适用于单个节目：

```powershell
python -m vistopia.main --token [token] save-show --id [id] --episode-id 1-3
```

如果要对多个节目分别指定不同 episode，请拆成多条命令执行。

## 开源许可

本项目基于原 python-vistopia 项目修改，原项目采用 MIT License。详见 `LICENSE`。
