// Enhanced Dashboard JS - BLACKBOXAI 2024
// Handles theme switching, particles, loading states, graph enhancements

// Theme Management
function initTheme() {
  const saved = localStorage.getItem('dashboardTheme') || 'cyberpunk';
  document.body.dataset.theme = saved;
  document.getElementById('theme-toggle')?.textContent = saved.toUpperCase();
}

function switchTheme(theme) {
  const themes = ['cyberpunk', 'neon', 'matrix'];
  const current = document.body.dataset.theme || 'cyberpunk';
  const nextIdx = (themes.indexOf(current) + 1) % themes.length;
  const nextTheme = themes[nextIdx];
  
  document.body.dataset.theme = nextTheme;
  localStorage.setItem('dashboardTheme', nextTheme);
  document.getElementById('theme-toggle')?.textContent = nextTheme.toUpperCase();
  
  // Restart particles if running
  if (window.particlesJS) {
    particlesJS('particles-canvas', getParticleConfig(nextTheme));
  }
}

// Enhanced Graph Loading with Fallback
function showGraphLoading(show = true) {
  const wrap = document.getElementById('graph-wrap');
  wrap.classList.toggle('loading', show);
  
  if (show) {
    // Add spinner
    if (!wrap.querySelector('.graph-spinner')) {
      const spinner = document.createElement('div');
      spinner.className = 'graph-spinner';
      spinner.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;gap:12px;">
          <div style="width:48px;height:48px;border:3px solid var(--line);border-top-color:var(--cyan);border-radius:50%;animation:spin 1s linear infinite;"></div>
          <div style="color:var(--cyan);text-align:center;font-size:14px;">
            Loading attack paths...
            <div style="font-size:12px;color:var(--muted);margin-top:4px;">Deploy Caldera agents for live data</div>
          </div>
          <button onclick="fetchAndRender()" style="padding:6px 12px;font-size:11px;border:1px solid var(--cyan);background:var(--glass-bg);">Refresh</button>
        </div>
      `;
      wrap.appendChild(spinner);
    }
  } else {
    const spinner = wrap.querySelector('.graph-spinner');
    if (spinner) spinner.remove();
  }
}

function showEmptyGraph() {
  const graphEl = document.getElementById('graph');
  graphEl.innerHTML = `
    <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px;color:var(--cyan);text-align:center;background:var(--glass-bg);border-radius:16px;">
      <div style="font-size:28px;margin-bottom:12px;">🌐 No Attack Paths</div>
      <div style="font-size:14px;color:var(--text);margin-bottom:20px;max-width:380px;line-height:1.6;">
        No agent activity or facts detected. Run a Caldera operation to populate the graph.
      </div>
      <div style="display:flex;gap:12px;">
        <button onclick="fetchAndRender()" style="padding:10px 20px;border:1px solid var(--cyan);background:rgba(0,255,204,0.08);border-radius:8px;cursor:pointer;font-weight:500;">🔄 Refresh Data</button>
        <a href="/docs" style="padding:10px 20px;border:1px solid var(--amber);background:rgba(247,185,85,0.08);border-radius:8px;text-decoration:none;color:var(--amber);font-weight:500;">📚 Setup Guide</a>
      </div>
    </div>
  `;
}

// Particles.js Config
function getParticleConfig(theme) {
  const base = {
    particles: {
      number: { value: 60, density: { enable: true, value_area: 800 } },
      color: { value: theme === 'matrix' ? '#00ff41' : '#00ffcc' },
      shape: { type: 'circle' },
      opacity: { value: 0.3, random: true },
      size: { value: 3, random: true },
      line_linked: { enable: true, distance: 120, color: theme === 'matrix' ? '#00ff41' : '#00ffcc', opacity: 0.2, width: 1 },
      move: { enable: true, speed: 2, direction: 'none', random: true, straight: false, out_mode: 'out' }
    },
    interactivity: {
      detect_on: 'canvas',
      events: { onhover: { enable: true, mode: 'grab' }, onclick: { enable: true, mode: 'push' }, resize: true },
      modes: { grab: { distance: 200, line_linked: { opacity: 0.5 } }, push: { particles_nb: 4 } }
    },
    retina_detect: true
  };
  return base;
}

// Init Enhanced Features
function initEnhancements() {
  // Theme init
  initTheme();
  
  // Add theme toggle if missing
  const topbar = document.querySelector('.topbar');
  if (topbar && !document.getElementById('theme-toggle')) {
    const toggle = document.createElement('button');
    toggle.id = 'theme-toggle';
    toggle.innerHTML = 'Cyberpunk';
    toggle.onclick = () => switchTheme();
    topbar.appendChild(toggle);
  }
  
  // Graph loading handler
  const graphWrap = document.getElementById('graph-wrap');
  if (graphWrap) {
    showGraphLoading(true);
  }
  
  // Particles
  if (typeof particlesJS !== 'undefined') {
    particlesJS('particles-canvas', getParticleConfig(document.body.dataset.theme || 'cyberpunk'));
  }
}

// Export for global use
window.showGraphLoading = showGraphLoading;
window.showEmptyGraph = showEmptyGraph;
window.switchTheme = switchTheme;
window.initEnhancements = initEnhancements;

// Auto-start enhancements at page load
window.addEventListener('DOMContentLoaded', () => {
  try {
    initEnhancements();
  } catch (err) {
    console.error('Init enhancements failed', err);
  }
});
