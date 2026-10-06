# 模型收藏

精选来自其他创作者的 3D 模型，积累实用工具、结构参考和希望亲手打印的作品。每项保留来源、原作者、用途与收藏理由；实际打印和使用后补充反馈。

[浏览模型收藏](https://windzu.github.io/windforge/collections/) · [原创作品](../models/)

当前尚未加入收藏。条目由 Wind 指定或确认，不自动把浏览记录、热门榜或 AI 推荐列为 Wind 的收藏。

## 新增条目

复制 [收藏模板](../templates/collection.json) 中的对象，填写实际信息后加入 `catalogue.json` 的 `items` 数组。数组顺序就是网页展示顺序；`slug` 使用唯一的英文小写名称，以连字符分隔。

| 字段 | 内容 |
| --- | --- |
| `title`、`author`、`source` | 模型名称、原作者、平台和实际模型链接；原作者主页可选 |
| `purpose`、`reason` | 用途与 Wind 的收藏理由，不把平台宣传改写成自己的使用结论 |
| `status` | `planned` 待打印、`printed` 已打印、`in-use` 实际使用 |
| `feedback` | 实际打印或使用反馈；待打印可以为 `null`，其余状态必须有反馈 |
| `tags`、`collected_date` | 可选标签和实际收藏日期；未记录日期留 `null` |
| `license` | 可选对象，含 `name`、`url`、`checked_date`；未核实留 `null`，不沿用原创模型许可 |
| `related_models` | 可选的本仓库原创模型 slug，用于关联参考和二次设计 |

默认记录链接与心得。开展二次设计时核对原作许可，并在新模型目录记录具体参考与修改。需要保存实拍或更长反馈时，可按条目 slug 建立子目录，并从反馈中说明。

网站从 `catalogue.json` 生成独立收藏页，首页保留原创作品优先并提供收藏入口。更新后沿用现有 GitHub Pages 构建与发布流程；条目积累后再按实际需要添加筛选。
