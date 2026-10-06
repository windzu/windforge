"""Build the static portfolio from versioned models and curated collections."""
from pathlib import Path
from html import escape
import argparse
import json
import shutil
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output', default='.cache/site')
args = parser.parse_args()
OUT = (ROOT / args.output).resolve()
assert OUT != ROOT and OUT != ROOT / 'models' and OUT != ROOT / 'site', 'Output must be a separate build directory'
OUT.mkdir(parents=True, exist_ok=True)
shutil.copytree(ROOT / 'site/assets', OUT / 'assets', dirs_exist_ok=True)
MODELS = [json.loads(path.read_text()) for path in sorted((ROOT / 'models').glob('*/model.json'))]
assert MODELS, 'No models in catalogue'
catalogue = json.loads((ROOT / 'collections/catalogue.json').read_text())
assert catalogue['schema_version'] == 1, 'Unsupported collection catalogue version'
COLLECTIONS = catalogue['items']
assert isinstance(COLLECTIONS, list), 'Collection items must be a list'
E = lambda value: escape(str(value), quote=True)
MARK = '<svg class="brand-mark" aria-hidden="true" viewBox="0 0 48 48"><rect width="48" height="48" rx="10" fill="#23352c"/><path d="M9 14l6 22h5l4-14 4 14h5l6-22h-6l-3 14-4-14h-4l-4 14-3-14z" fill="#d5da9b"/></svg>'

def page(title, description, prefix, content, viewer=False, active=None):
    script = f'<script type="module" src="{prefix}assets/vendor/model-viewer.min.js"></script>' if viewer else ''
    current_collection = ' aria-current="page"' if active == 'collections' else ''
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(description)}"><meta name="theme-color" content="#f4f2eb">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(description)}"><meta property="og:type" content="website">
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{prefix}assets/style.css">
{script}<script defer src="{prefix}assets/site.js"></script></head><body>
<a class="skip" href="#main">跳到正文</a><div class="wrap">
<header class="nav"><a class="brand" href="{prefix}index.html" aria-label="WindForge 首页">{MARK}WindForge<span style="font-weight:400;color:#8b937b">.</span></a>
<nav class="nav-links" aria-label="主导航"><a href="{prefix}index.html#collection">原创作品</a><a href="{prefix}collections/"{current_collection}>模型收藏</a><a href="{prefix}index.html#about">关于工坊</a><a href="https://github.com/windzu" target="_blank" rel="noopener noreferrer">GitHub ↗</a></nav></header>
<main id="main">{content}</main>
<footer class="footer"><span>© 2026 WindForge · Wind 的造物工坊</span><span>想法成形，实物验证。<span class="mono" style="margin-left:20px">DESIGNED & MADE BY WIND</span></span></footer>
</div></body></html>'''

COLLECTION_STATUSES = {'planned': '待打印', 'printed': '已打印', 'in-use': '实际使用'}

def external_url(value):
    parsed = urlsplit(value)
    assert parsed.scheme in {'http', 'https'} and parsed.netloc and not parsed.username and not parsed.password, f'Invalid external URL: {value}'
    return E(value)

def collection_card(item):
    slug = item['slug']
    assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug), 'Collection slug must use lowercase letters, numbers and hyphens'
    assert item['status'] in COLLECTION_STATUSES, 'Unknown collection status'
    for value in (item['title'], item['author']['name'], item['source']['platform'], item['purpose'], item['reason']):
        assert isinstance(value, str) and value.strip(), 'Missing collection attribution, purpose or reason'
    feedback = item.get('feedback')
    assert item['status'] == 'planned' or (isinstance(feedback, str) and feedback.strip()), 'Printed or used collections require actual feedback'
    author = E(item['author']['name'])
    if item['author'].get('url'):
        author = f'<a href="{external_url(item["author"]["url"])}" target="_blank" rel="noopener noreferrer">{author} ↗</a>'
    tags = ''.join(f'<span class="collection-tag">{E(tag)}</span>' for tag in item.get('tags', []))
    feedback_html = f'<div class="collection-feedback"><h3>打印与使用反馈</h3><p>{E(feedback)}</p></div>' if feedback else ''
    license_html = ''
    if item.get('license'):
        license_info = item['license']
        license_name = E(license_info['name'])
        if license_info.get('url'):
            license_name = f'<a href="{external_url(license_info["url"])}" target="_blank" rel="noopener noreferrer">{license_name} ↗</a>'
        checked = f' · {E(license_info["checked_date"])} 核对' if license_info.get('checked_date') else ''
        license_html = f'<p class="fine">原作许可：{license_name}{checked}</p>'
    related = []
    for model_slug in item.get('related_models', []):
        model = next((model for model in MODELS if model['slug'] == model_slug), None)
        assert model, f'Unknown related model: {model_slug}'
        related.append(f'<a href="../models/{E(model_slug)}/">{E(model["title"])} ↗</a>')
    related_html = f'<p class="collection-related">相关原创作品：{" · ".join(related)}</p>' if related else ''
    date = f'<time datetime="{E(item["collected_date"])}">{E(item["collected_date"])} 收藏</time>' if item.get('collected_date') else ''
    return f'''<article class="collection-card" id="{E(slug)}">
<div class="collection-card-top"><span class="eyebrow">{E(item['source']['platform'])} / {E(slug)}</span><span class="collection-status" data-status="{E(item['status'])}">{COLLECTION_STATUSES[item['status']]}</span></div>
<h2>{E(item['title'])}</h2><p class="collection-author">原作者 · {author}</p><div class="collection-tags">{tags}</div>
<dl class="collection-notes"><div><dt>用途</dt><dd>{E(item['purpose'])}</dd></div><div><dt>收藏理由</dt><dd>{E(item['reason'])}</dd></div></dl>{feedback_html}{related_html}{license_html}
<div class="collection-card-bottom"><a class="text-link" href="{external_url(item['source']['url'])}" target="_blank" rel="noopener noreferrer">查看原作 <span aria-hidden="true">↗</span></a>{date}</div></article>'''

def collection_content(items):
    slugs = [item['slug'] for item in items]
    assert len(slugs) == len(set(slugs)), 'Collection slugs must be unique'
    cards = ''.join(collection_card(item) for item in items)
    empty = '''<section class="collection-empty" aria-labelledby="collection-empty-title"><div class="collection-empty-copy"><svg class="bookmark-mark" aria-hidden="true" viewBox="0 0 64 64" fill="none"><path d="M19 12h26v41L32 44 19 53V12Z" stroke="currentColor" stroke-width="2"/><path d="M26 24h12M26 31h12" stroke="currentColor" stroke-width="2"/></svg><span class="eyebrow">THE FIRST FIND</span><h2 id="collection-empty-title">第一件收藏，还在挑选。</h2><p>实用的工具、巧妙的结构，或让人想亲手打印的作品。<br>选好之后，把来源与值得留下的理由写在这里。</p><a class="text-link" href="https://makerworld.com/en" target="_blank" rel="noopener noreferrer">去 MakerWorld 看看 <span aria-hidden="true">↗</span></a></div><div class="collection-status-guide"><h3>让收藏积累成经验。</h3><dl><div><dt>01 <span>待打印</span></dt><dd>记录用途、来源和收藏理由。</dd></div><div><dt>02 <span>已打印</span></dt><dd>补上真实打印结果与遇到的问题。</dd></div><div><dt>03 <span>实际使用</span></dt><dd>记录使用体验、局限和可以借鉴的细节。</dd></div></dl></div></section>'''
    return f'''<a class="back" href="../index.html#collection">← 回到原创作品</a>
<header class="collections-heading"><div><span class="eyebrow">SELECTED FROM OTHER MAKERS</span><h1>模型收藏</h1><p>实用的工具，值得研究的结构，以及想亲手打印的作品。</p></div><span class="collections-count"><strong>{len(items):02d}</strong> 件精选</span></header>
<p class="collections-intro">来自其他创作者的好设计。每项标明原作者与来源，收藏理由和打印、使用反馈由 Wind 记录。</p>
<div class="collection-grid">{cards}</div>{empty if not items else ''}'''

collection_folder = OUT / 'collections'
collection_folder.mkdir(parents=True, exist_ok=True)
(collection_folder / 'index.html').write_text(page('模型收藏 · WindForge', 'Wind 精选的 3D 模型、实用工具与结构参考，保留原作者、收藏理由和打印使用反馈。', '../', collection_content(COLLECTIONS), active='collections'))

rows = []
for model in MODELS:
    slug = model['slug']
    release = model['release']
    if release['published']:
        assert release['makerworld_url'] and release['version'] and release['license'] and release['publication_authorized'], 'Published models require actual URL, version, chosen license and authorization'
    status_text = (('已发布 · 有装配瑕疵' if model.get('known_issues') else '已发布') if release['version'] == model['version'] else f"{release['version']} 已发布 · {model['version']} {model['status']}") if release['published'] else model['status']
    assert slug == Path(slug).name and '..' not in slug
    source = ROOT / 'models' / slug
    target = OUT / 'assets/models' / slug
    target.mkdir(parents=True, exist_ok=True)
    photos = model['images'].get('photos', [])
    for image in dict.fromkeys([model['images']['hero'], model['images']['parts'], 'images/display.glb'] + [photo['path'] for photo in photos]):
        file = source / image
        assert file.is_file(), f'Missing asset: {file}'
        shutil.copy2(file, target / file.name)
    hero = f"assets/models/{slug}/{Path(model['images']['hero']).name}"
    parts = f"assets/models/{slug}/{Path(model['images']['parts']).name}"
    rows.append(f'''<article class="project-row" data-project data-published="{str(release['published']).lower()}">
<a class="project-image" href="models/{slug}/" aria-label="查看 {E(model['title'])}"><img src="{hero}" alt="{E(model['title'])} · {E(model['images']['type'])}" width="1200" height="1400" loading="lazy"></a>
<div class="project-copy"><span class="eyebrow">OBJECT {E(model['number'])} / {E(model['category'])}</span><h3>{E(model['title'])}</h3><p>{E(model['summary'])}</p>
<div class="project-meta"><span>{E(model['version'])}</span><span>{E(model['part_count'])} 个零件</span><span>{E(model['dimensions'])}</span></div>
<span class="pill">{E(status_text)}</span><a class="text-link" style="margin-top:24px" href="models/{slug}/">走近这个作品 <span aria-hidden="true">↗</span></a></div></article>''')
    prefix = '../../'
    specifications = [('适配', model['compatibility']), ('主体尺寸', model['body_dimensions']), ('整体尺寸', model['dimensions']), ('制造零件', f"{model['part_count']} 件"), ('材料', model['material']), ('额外物料', model['hardware'])]
    spec = ''.join(f'<div><dt>{E(key)}</dt><dd>{E(value)}</dd></div>' for key,value in specifications)
    features = ''.join(f'<article><span class="eyebrow">0{index}</span><h3>{E(feature["title"])}</h3><p>{E(feature["text"])}</p></article>' for index,feature in enumerate(model['features'],1))
    steps = ''.join(f'<li>{E(step)}</li>' for step in model['assembly_steps'])
    p = model['printing']
    print_spec = ''.join(f'<div><dt>{E(key)}</dt><dd>{E(value)}</dd></div>' for key,value in [('打印机 / 喷嘴', f"{p['printer']} / {p['nozzle']}"), ('层高',p['layer_height']), ('墙层', f"{p['walls']} 道"), ('填充',p['infill']), ('预计时间',p['estimated_time']), ('预计耗材',p['estimated_filament'])])
    validation_titles = {'geometry':'几何完整性','fit_tests':'配合试件','white_plate':'白色盘打印','black_plate':'黑色盘打印','assembly':'整机装配','controls':'按键与操作','charging':'充电','magnetic_closure':'磁吸合壳','side_button':'侧键安装与保持'}
    validations = ''.join(f'<li><span class="indicator {"pending" if any(word in text for word in ("待", "瑕疵", "外露", "掉落")) else ""}" aria-hidden="true"></span><span>{E(validation_titles[key])}<small>{E(text)}</small></span></li>' for key,text in model['validation'].items())
    release_caption = {'submission-unconfirmed':'提交结果待核实','under-review':'审核中','appeal-pending':'等待人工复核'}.get(release.get('status'), '发布准备中')
    makerworld = f'<a class="action" href="{E(release["makerworld_url"])}" target="_blank" rel="noopener noreferrer">在 MakerWorld 查看 {E(release["version"] or "")} <span aria-hidden="true">↗</span></a>' if release['makerworld_url'] else f'<p class="release-pending">MakerWorld · {E(release_caption)}</p>'
    files = ''
    download_dir = target / 'downloads'
    if release['license'] and release['publication_authorized']:
        download_dir.mkdir(exist_ok=True)
        for file in sorted((source / 'exports' / model['version']).glob('*')):
            if file.suffix in {'.stl','.3mf'}:
                shutil.copy2(file, download_dir / file.name)
                files += f'<a class="file" href="{prefix}assets/models/{slug}/downloads/{file.name}" download><span>{E(file.name)}<small>{E(file.suffix[1:].upper())} · {file.stat().st_size/1024:.0f} KB</small></span><span aria-hidden="true">↓</span></a>'
        step = source / 'src' / model['version'] / 'retro_remote_assembly.step'
        shutil.copy2(step, download_dir / step.name)
        files += f'<a class="file" href="{prefix}assets/models/{slug}/downloads/{step.name}" download><span>STEP 装配源文件<small>编辑用 · 装配坐标</small></span><span aria-hidden="true">↓</span></a>'
        shutil.copy2(source / 'LICENSE.md', download_dir / 'LICENSE.md')
        license_note = f'<p class="fine">作品许可：<a href="{E(release["license_url"])}" target="_blank" rel="noopener noreferrer">{E(release["license"])}</a> · 署名、允许修改、禁止商用。打印 STL 使用 mm 单位；装配 STEP 与网页模型用于编辑和查看。</p>'
    else:
        # Clear stale downloads when publication authorization is not recorded.
        if download_dir.exists(): shutil.rmtree(download_dir)
        files = '<p class="body-copy">模型文件已整理，下载将在发布信息与许可确认后开放。</p>'
        license_note = '<p class="fine">现有文件：五个打印方向 STL、黑白两盘通用 3MF、STEP 装配与配合试件。</p>'
    versions = ''.join(f'<article class="version-entry"><div class="version-label"><span class="pill">{E(v["version"])}{" · 当前展示" if v["version"] == model["version"] else " · 历史版本"}</span><time>{E(v["date"])}</time></div><h3>{E(v["title"])}</h3><p>{E(v["changes"])}</p><p class="fine">{E(v["validation"])}</p><a class="text-link" href="https://github.com/windzu/windforge/tree/main/models/{E(slug)}/{E(v["files"])}" target="_blank" rel="noopener noreferrer">查看这版工程 ↗</a></article>' for v in model.get('versions', []))
    lessons = ''.join(f'<article><h3>{E(lesson["title"])}</h3><p>{E(lesson["text"])}</p></article>' for lesson in model.get('lessons', []))
    photo_items = ''.join(f'<figure><a href="{prefix}assets/models/{slug}/{E(Path(photo["path"]).name)}" target="_blank" rel="noopener noreferrer"><img src="{prefix}assets/models/{slug}/{E(Path(photo["path"]).name)}" alt="{E(photo["caption"])}" loading="lazy" width="{photo["width"]}" height="{photo["height"]}"></a><figcaption>{E(photo["caption"])}</figcaption></figure>' for photo in photos)
    photo_gallery = f'<section class="photo-section" aria-label="实物照片"><span class="eyebrow">PRINTED OBJECT / {E(model["version"])}</span><h2>打印出来的样子。</h2><div class="photo-gallery">{photo_items}</div><p class="fine">实拍照片。{E(model["images"].get("photo_note", ""))}</p></section>' if photos else ''
    issues = model.get('known_issues', [])
    issue_items = ''.join(f'<article><h3>{E(issue["title"])}</h3><p>{E(issue["effect"])}</p><p class="fine">后续计划：{E(issue["next"])}</p></article>' for issue in issues)
    issue_notice = f'<section class="issue-notice" aria-label="已知装配问题"><span class="eyebrow">KNOWN ISSUES / {E(model["version"])}</span><h2>这版有 {len(issues)} 处装配问题。</h2><div class="issue-grid">{issue_items}</div><p class="fine">实物与功能已验证，下载仍为当前 {E(model["version"])}；后续优化尚未建模或打印。</p></section>' if issues else ''
    body = f'''
<a class="back" href="{prefix}index.html#collection">← 返回作品集</a>
<div class="product-heading"><div><span class="eyebrow">OBJECT {E(model['number'])} / {E(model['english_title'])}</span><h1>{E(model['title'])}</h1><p>{E(model['subtitle'])}</p></div><span class="pill">{E(status_text)}</span></div>
<section class="product-stage" aria-label="模型展示与规格"><div class="stage-art"><div class="stage-bar"><div class="view-tabs" aria-label="模型视图"><button data-view="assembly" aria-pressed="true">装配视图</button><button data-view="parts" aria-pressed="false">拆件图</button></div><span class="mono">{E(model['version'].upper())} · 3D PREVIEW</span></div>
<model-viewer src="{prefix}assets/models/{slug}/display.glb" alt="{E(model['title'])}的可旋转 3D 模型，遥控器仅为适配展示" camera-controls touch-action="pan-y" camera-orbit="-150deg 72deg auto" shadow-intensity="0.8" exposure="1" interaction-prompt="none" poster="{prefix}{hero}"><img class="model-poster" slot="poster" src="{prefix}{hero}" alt="模型渲染预览"></model-viewer>
<img class="fallback-art" data-fallback-art src="{prefix}{hero}" alt="模型渲染预览" hidden><img class="parts-art" data-parts-art src="{prefix}{parts}" alt="后壳、前框、独立面板的拆件渲染图" hidden><p class="stage-hint" data-stage-hint>拖动旋转 · 双指或滚轮缩放</p></div>
<div class="stage-info"><span class="eyebrow" style="margin-bottom:12px">THE OBJECT</span><h2>复古轮廓，<br>日常用途。</h2><dl class="spec">{spec}</dl><p class="status-note">{E(model['images']['type'])}与 3D 预览。遥控器为适配参考，不属于打印零件。</p>{makerworld}<a class="release-link text-link" href="#printing">查看打印与装配说明 <span aria-hidden="true">↓</span></a></div></section>
{issue_notice}
{photo_gallery}
<div class="detail-body"><nav class="detail-nav" aria-label="作品内容"><a href="#design">01 · 关于这件作品</a><a href="#validation">02 · 验证记录</a><a href="#printing">03 · 打印建议</a><a href="#assembly">04 · 装配</a><a href="#files">05 · 模型文件</a><a href="#iterations">06 · 版本与经验</a></nav><div>
<section class="detail-section" id="design"><span class="eyebrow">01 / DESIGN NOTES</span><h2>细节，要经得起拿在手里。</h2><div class="features">{features}</div></section>
<section class="detail-section" id="validation"><span class="eyebrow">02 / VALIDATION</span><h2>每一步验证，都留下记录。</h2><p class="body-copy">几何检查、局部试件、整机装配分别记录。下列状态对应本页的 {E(model['version'])} 版本。</p><ul class="validation-list">{validations}</ul></section>
<section class="detail-section" id="printing"><span class="eyebrow">03 / PRINTING</span><h2>黑白两盘，分别打印。</h2><dl class="spec spec-grid">{print_spec}</dl><p class="body-copy" style="margin-top:24px">{E(p['support'])}。后壳内腔朝上，白前框接合侧朝下，黑面板背面朝下。</p><p class="fine">{E(p['note'])}</p></section>
<section class="detail-section" id="assembly"><span class="eyebrow">04 / ASSEMBLY</span><h2>先试合，再固定。</h2><ol class="steps">{steps}</ol><p class="fine">面板固定方式为定位柱加胶；磁铁安装前确认极性。不要把装配坐标下的零件当作打印排版。</p></section>
<section class="detail-section" id="files"><span class="eyebrow">05 / FILES & LICENSE</span><h2>从展示，到你手里的实物。</h2><div class="files">{files}</div>{license_note}<p class="fine">参考来源：{E(release['reference_source'])}</p></section>
<section class="detail-section" id="iterations"><span class="eyebrow">06 / ITERATIONS</span><h2>版本留下来，经验接着用。</h2><p class="body-copy">默认展示与下载 {E(model['version'])}。历史工程保留在仓库中，验证结果分别对应各自版本。</p><div class="version-history">{versions}</div><div class="lessons">{lessons}</div></section>
</div></div>'''
    folder = OUT / 'models' / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'index.html').write_text(page(f"{model['title']} · WindForge",model['summary'],prefix,body,viewer=True))

featured = MODELS[0]
home_hero = f"assets/models/{featured['slug']}/{Path(featured['images']['hero']).name}"
home = f'''
<section class="hero"><div class="hero-copy"><span class="eyebrow">A PERSONAL OBJECT WORKSHOP / EST. 2026</span><h1>把想法，<br>拿在手里。</h1><p>这里是 Wind 的造物工坊。<br>从日常灵感出发，和 AI 一起把想法做成模型，<br>再通过打印、使用与改进，让它成为实物。</p><a class="action" href="#collection">探索作品 <span aria-hidden="true">↓</span></a></div>
<figure class="hero-art" style="margin:0"><a href="models/{featured['slug']}/" aria-label="查看{E(featured['title'])}"><img src="{home_hero}" alt="{E(featured['title'])} · {E(featured['images']['type'])}" width="1200" height="1400" fetchpriority="high"></a><figcaption class="image-caption"><span>{E(featured['number'])} / {E(featured['title'])}</span><span>{E(featured['images']['type'])} · {E(featured['version'])}</span></figcaption></figure></section>
<section id="collection" aria-labelledby="collection-title"><div class="section-head"><div><span class="eyebrow">ORIGINAL OBJECTS</span><h2 id="collection-title">工坊里的原创作品 <span class="mono" style="font-size:13px;color:#7c866e;vertical-align:super;margin-left:8px">{len(MODELS):02d}</span></h2></div><div class="filters" aria-label="作品状态筛选"><button data-filter="all" aria-pressed="true">全部作品</button><button data-filter="published" aria-pressed="false">已发布</button></div></div>{''.join(rows)}<p class="empty" data-empty hidden>目前还没有已发布的作品。完成发布后，会在这里展示。</p></section>
<section class="collections-teaser" aria-labelledby="collections-teaser-title"><div><span class="eyebrow">SELECTED FROM OTHER MAKERS</span><h2 id="collections-teaser-title">模型收藏 <span class="mono">{len(COLLECTIONS):02d}</span></h2></div><div><p>实用工具、结构参考与想要打印的好设计。<br>记录原作者、收藏理由，以及真实打印和使用反馈。</p>{'<p class="fine">首批收藏待加入。</p>' if not COLLECTIONS else ''}<a class="text-link" href="collections/">浏览模型收藏 <span aria-hidden="true">↗</span></a></div></section>
<section class="about" id="about"><div><span class="eyebrow" style="display:block;margin-bottom:18px">ABOUT THE WORKSHOP</span><h2>Wind 的造物工坊。</h2></div><div><p>一个个人 3D 模型设计与打印项目。作品从具体需求和生活中的兴趣出发，留下可编辑的模型、设计取舍和实物反馈。</p><p>这里也精选来自其他创作者的模型，积累实用工具和结构参考，记录来源与自己的使用经验。</p><p>这个网站展示作品和制作记录；MakerWorld 承接模型发布与打印分享。每件原创作品都标明自己的版本与验证范围。</p></div></section>'''
(OUT / 'index.html').write_text(page('WindForge · Wind 的造物工坊','把想法设计成模型，再把模型打印成实物。探索 Wind 的 3D 作品、制作记录与 MakerWorld 发布。','',home))
(OUT / '.nojekyll').touch()
print(f'Built {len(MODELS)} model page(s), {len(COLLECTIONS)} collection item(s) and portfolio: {OUT}')
