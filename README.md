# Hitode v0.2.9：iPhone XR／iOS 14.8 云构建包

这个仓库通过 GitHub Actions 的 Apple 芯片 macOS runner，为 Hitode v0.2.9 应用实验性 iOS 14 补丁，并生成 TrollStore IPA。**Windows 不需要安装 Xcode，也不需要 Apple 开发者账号。**

> 这是非官方、实验性移植。构建包完成不代表云端已经编译通过；编译通过也不代表 iOS 14.8 实机上的 JIT、内存映射和每个游戏都可用。

## 补丁内容

- 启动器最低系统版本从 16.2 调整为 14.0，因此覆盖 iOS 14.8。
- 静态 FFmpeg 的编译目标从 16.2 调整为 14.0。
- iOS 16 及以上保留新的横屏接口；iOS 14／15 改用 `attemptRotationToDeviceOrientation`，避免调用旧系统不存在的接口。
- 构建后自动检查主程序及 JIT 扩展的最低系统版本、Mach-O 版本和 TrollStore 所需权限。

## 使用条件

- iPhone XR 或其他 A12 及以上设备。
- iOS 14.8，已安装 TrollStore 2.0.12 或更新版本。
- 一个 GitHub 账号。公开仓库和私有仓库的 Actions 额度及计费规则以 GitHub 账户页面为准。

## Windows 操作步骤

### 1. 创建构建仓库

1. 在 GitHub 新建一个仓库，例如 `hitode-ios14-builder`。
2. 把本包**根目录内的全部内容**上传到仓库根目录，包括：
   - `.github/workflows/build-ios14.yml`
   - `patches/hitode-v0.2.9-ios14.patch`
   - `scripts/verify_ipa.py`
   - `README.md`
3. 不要只上传 `README.md`；隐藏的 `.github` 目录也必须上传。

### 2. 启动云编译

1. 打开仓库的 **Actions** 页面，按提示启用工作流。
2. 选择 **Build Hitode v0.2.9 for iOS 14.8 (TrollStore)**。
3. 点击 **Run workflow**。
4. 工作流会从 `hitode-project/hitode` 的 `v0.2.9` 标签拉取源码，应用补丁，再拉取上游固定版本的 Wine 并编译。
5. 只有所有步骤成功后，页面底部才会出现 `hitode-ios14.8-trollstore` Artifact。失败时打开红色步骤查看完整日志，不要把日志里的本地路径、令牌或其他隐私信息公开发送。

### 3. 下载与安装

1. 下载 Artifact 并解压，取得 `Hitode-0.2.9-ios14.8-trollstore.ipa`；`verification.json` 是静态检查结果。
2. 用数据线、LocalSend 等你信任的方式把 IPA 传到 XR。
3. 在 TrollStore 中导入并安装 IPA。
4. **每次彻底退出后，都在 TrollStore 的应用列表中点 Hitode，选择 Open with JIT。**不要直接从桌面图标启动。
5. 等 Hitode 设置页显示 JIT 已启用，再启动游戏。

这条路线不需要 Apple ID 自签、每 7 天续签、LocalDevVPN 或 `pairingFile.plist`。

## 可能遇到的问题

- **工作流在补丁步骤失败**：上游文件发生变化，或下载的补丁不完整。确认使用的是本包原始文件和上游 `v0.2.9`。
- **工作流在 Rust／Xcode 编译步骤失败**：说明还有其他依赖的最低系统版本或 API 需要移植。保留失败步骤的完整日志，再继续修改；这不等于已经得到可安装 IPA。
- **提示地址空间不足**：不要只反复重启。保留 Hitode 的报告和 `verification.json`，需要进一步检查 iOS 14.8 的地址空间布局。
- **游戏很慢或设置页显示 JIT 未启用**：彻底退出 Hitode，再从 TrollStore 使用 Open with JIT；在 JIT 就绪前启动的游戏，本次运行不会自动切换到 JIT。
- **启动或横屏时闪退**：记录发生步骤和游戏名称。旧系统仍可能存在本次源码审查未覆盖的 API 或内存差异。
- **游戏本身不兼容**：Hitode 上游仍是实验项目，移植成功不代表所有游戏都能运行。

## 验证范围

工作流验证的是源码补丁应用、云端编译、IPA 静态版本和权限。以下项目必须在你的 XR 上另行验证：安装、启动、Open with JIT、横屏、游戏导入、存档、Metal 渲染、音视频及长时间运行。

## 文件说明

- `patches/hitode-v0.2.9-ios14.patch`：应用到上游 v0.2.9 的源码补丁。
- `.github/workflows/build-ios14.yml`：云编译、签名、静态检查和 Artifact 上传流程。
- `scripts/verify_ipa.py`：IPA 静态检查脚本，在 macOS runner 上使用 `otool` 和 `ldid`。
