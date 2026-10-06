document.querySelectorAll('[data-filter]').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('[data-filter]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    const publishedOnly = button.dataset.filter === 'published';
    const projects = [...document.querySelectorAll('[data-project]')];
    projects.forEach(project => { project.hidden = publishedOnly && project.dataset.published !== 'true'; });
    const empty = document.querySelector('[data-empty]');
    if (empty) empty.hidden = projects.some(project => !project.hidden);
  });
});
const viewer = document.querySelector('model-viewer');
const parts = document.querySelector('[data-parts-art]');
const fallback = document.querySelector('[data-fallback-art]');
const hint = document.querySelector('[data-stage-hint]');
let failed = false;
function showView(view) {
  const exploded = view === 'parts';
  if (viewer) viewer.hidden = exploded || failed;
  if (fallback) fallback.hidden = exploded || !failed;
  if (parts) parts.hidden = !exploded;
  if (hint) hint.textContent = exploded ? '拆件渲染 · 仅展示装配关系' : failed ? '模型渲染图' : '拖动旋转 · 双指或滚轮缩放';
  document.querySelectorAll('[data-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === view)));
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => showView(button.dataset.view)));
if (viewer) viewer.addEventListener('error', () => { failed = true; showView(document.querySelector('[data-view][aria-pressed="true"]')?.dataset.view || 'assembly'); });
