# 作品展示与发布

仓库存放版本化工程与迭代证据，GitHub Pages 展示最新版本，MakerWorld 承接模型社区发布。展示上线和模型正式发布分别记录。

## 更新展示站

每个作品的 `model.json` 是网站数据入口，`version` 指定默认展示及下载版本；`versions` 与 `lessons` 保存迭代和经验。几何、局部试件、整机装配与发布状态分开填写。

`tools/build_site.py` 使用 Python 标准库生成静态网站，默认输出到 `.cache/site/`；指定 `--output dist` 为部署产物。源码在 `site/assets/`。推送 main 后 GitHub Actions 构建并部署到 https://windzu.github.io/windforge/ 。

网页 GLB 来自真实 Blender 工程，含非制造遥控器参考；下载则使用对应版本的制造 STL、通用 3MF 与编辑 STEP。通用 3MF 需要重新切片，不能冒充一键打印配置。网站支持已发布筛选，未发布作品明确展示准备状态。

第三方模型收藏的数据入口为 `collections/catalogue.json`，生成 `/collections/` 独立页面。首页优先展示原创作品并保留收藏入口；收藏更新也触发 Pages 部署。空清单展示真实空状态，已有条目展示原作者、来源、用途、收藏理由和实际打印使用反馈。新增方式见 [收藏说明](../collections/README.md)。

3D 预览组件为官方 `@google/model-viewer` 4.3.1，随站点保存以避免运行时 CDN 依赖，保留 Apache 2.0 许可。来源：https://modelviewer.dev/ 。

## MakerWorld 发布

1. 准备对应版本的制造文件、实拍与渲染、标题、描述、装配和实际验证范围。
2. 由 Wind 选择许可并授权发布；登录和新的平台协议确认由 Wind 完成。
3. 默认全球站优先，准备中英描述；登录后核对账号中国站同步范围，不擅自改变全账号同步设置。
4. 上传模型与材料。如创建打印配置，使用含打印机与切片参数的 Bambu 工程，记录验证范围；几何 3MF 只作为模型文件。
5. 保存草稿后，从账号草稿卡片提供的实际编辑入口继续完整向导。提交后核对审核列表、草稿数和公开作品页；审核中使用 `release.status=under-review`，公开确认前 `published=false`。
   若自动实拍识别失败，先阅读具体原因与平台官方说明，再整理保留打印纹理和拍摄环境的证据；私人屏幕内容需遮挡。申诉提交后以实际成功回执为准，使用 `release.status=appeal-pending`，保留失败原因、证据文件、申诉文本和回复期限。不同日期的平台规则可能变化，不反复盲目重传或创建重复模型。
6. 成功发布后回填 `release.makerworld_url`、`published_date`、发布版本和平台状态；核实公开页面后才置 `published=true`。推送后网站出现实际 MakerWorld 按钮。
7. 后续设计版本与既有发布版本分别保留，避免旧版实测结论自动套用到新版。

官方说明支持全球站向中国站同步符合条件的模型和打印配置，由账号设置控制范围；两站下载 / 打印统计分别记录。中国站实际镜像链接核实后再记录，不假设即时双向同步。

依据：[官方同步公告与答复](https://forum.bambulab.com/t/new-makerworld-cn/80853)、[官方统计答复](https://forum.bambulab.com/t/new-makerworld-cn/80853/23)、[打印配置 FAQ](https://makerworld.com/en/faq#Print-Profile)。2026-10-06 核对；具体账号设置以上传时页面为准。
