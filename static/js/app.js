/* ═══════════════════════════════════════════════════
   SOCIALFEED MADAGASCAR — app.js
   ═══════════════════════════════════════════════════ */

// ── THEME TOGGLE ───────────────────────────────────
const themeBtn = document.getElementById('themeToggle');
if (themeBtn) {
  themeBtn.addEventListener('click', async () => {
    const resp = await fetch('/theme/toggle', { method: 'POST' });
    const data = await resp.json();
    document.documentElement.setAttribute('data-theme', data.theme);
  });
}

// ── AUTO-DISMISS FLASH ─────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach(f => {
    setTimeout(() => {
      f.style.transition = 'opacity .5s, transform .5s';
      f.style.opacity = '0';
      f.style.transform = 'translateY(-6px)';
      setTimeout(() => f.remove(), 500);
    }, 4000);
  });

  // Init all AJAX cart forms
  document.querySelectorAll('.ajax-cart-form').forEach(attachCartForm);

  // Close sidebar on overlay click (mobile)
  document.addEventListener('click', e => {
    const sidebar = document.getElementById('sidebar');
    if (sidebar && sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) && !e.target.classList.contains('burger')) {
      sidebar.classList.remove('open');
    }
  });
});

// ── COMPOSER ───────────────────────────────────────
function openComposer() {
  const form = document.getElementById('composerForm');
  const toggle = document.getElementById('composerToggle');
  const quickBtns = document.getElementById('composerQuickBtns');
  if (form) form.style.display = 'block';
  if (toggle) toggle.style.display = 'none';
  if (quickBtns) quickBtns.style.display = 'none';
  const ta = document.getElementById('postContent');
  if (ta) ta.focus();
}

function closeComposer() {
  const form = document.getElementById('composerForm');
  const toggle = document.getElementById('composerToggle');
  const quickBtns = document.getElementById('composerQuickBtns');
  if (form) form.style.display = 'none';
  if (toggle) toggle.style.display = 'flex';
  if (quickBtns) quickBtns.style.display = 'flex';
  clearMediaPreview();
  const urlRow = document.getElementById('urlInputRow');
  if (urlRow) urlRow.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
  const placeholder = document.getElementById('composerToggle');
  if (placeholder) placeholder.addEventListener('click', openComposer);
});

// Open file picker with specific accept type
function openFileInput(accept) {
  openComposer();
  const input = document.getElementById('mainFileInput');
  if (!input) return;
  input.accept = accept;
  input.click();
}

function toggleUrlInput() {
  openComposer();
  const row = document.getElementById('urlInputRow');
  if (row) row.style.display = row.style.display === 'none' ? 'block' : 'none';
}

// ── MEDIA PREVIEW IN COMPOSER ──────────────────────
function previewMedia(input) {
  const file = input.files[0];
  if (!file) return;
  const preview = document.getElementById('mediaPreview');
  if (!preview) return;
  preview.innerHTML = '';
  preview.style.display = 'block';

  const closeBtn = document.createElement('button');
  closeBtn.className = 'media-preview-close';
  closeBtn.innerHTML = '✕';
  closeBtn.type = 'button';
  closeBtn.onclick = () => { clearMediaPreview(); input.value = ''; };
  preview.appendChild(closeBtn);

  const url = URL.createObjectURL(file);
  const type = file.type.split('/')[0]; // image, video, audio

  if (type === 'image') {
    const img = document.createElement('img');
    img.src = url;
    img.style.cssText = 'border-radius:10px;width:100%;max-height:280px;object-fit:cover';
    preview.appendChild(img);
  } else if (type === 'video') {
    const vid = document.createElement('video');
    vid.src = url; vid.controls = true; vid.preload = 'metadata';
    vid.style.cssText = 'width:100%;border-radius:10px;max-height:280px;background:#000';
    preview.appendChild(vid);
  } else if (type === 'audio') {
    const wrap = document.createElement('div');
    wrap.style.cssText = 'display:flex;align-items:center;gap:12px;padding:14px;background:var(--bg3);border-radius:10px';
    wrap.innerHTML = `<span style="font-size:1.5rem">🎵</span><div style="flex:1"><div style="font-weight:600;margin-bottom:6px;font-size:.88rem">${file.name}</div><audio controls style="width:100%"><source src="${url}"></audio></div>`;
    preview.appendChild(wrap);
  }
}

function clearMediaPreview() {
  const p = document.getElementById('mediaPreview');
  if (p) { p.innerHTML = ''; p.style.display = 'none'; }
}

// ── COMMENTS TOGGLE ────────────────────────────────
function toggleComments(postId) {
  const el = document.getElementById('comments-' + postId);
  if (!el) return;
  el.style.display = el.style.display === 'none' ? 'flex' : 'none';
  if (el.style.display === 'flex') el.style.flexDirection = 'column';
}

// ── AJAX LIKE ──────────────────────────────────────
async function likePost(postId, btn) {
  try {
    const resp = await fetch(`/post/${postId}/like`, {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest',
                 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    const data = await resp.json();
    btn.classList.toggle('liked', data.liked);
    const svg = btn.querySelector('svg');
    if (svg) svg.setAttribute('fill', data.liked ? 'currentColor' : 'none');

    // Update stats display
    const card = btn.closest('.post-card');
    if (card) {
      const stats = card.querySelector('.post-stats');
      if (stats) {
        const likeSpan = stats.querySelector('span:first-child');
        if (likeSpan) likeSpan.textContent = `${data.likes} j'aime`;
      }
    }
  } catch (e) {
    // Fallback: submit form normally
    btn.closest('form') && btn.closest('form').submit();
  }
}

// ── AJAX CART ──────────────────────────────────────
function attachCartForm(form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const fd = new FormData(form);
      const resp = await fetch(form.action, {
        method: 'POST',
        body: fd,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      const data = await resp.json();
      if (data.ok) {
        showCartToast(`🛒 "${data.name}" ajouté au panier !`);
        updateCartBadges(data.count);
      }
    } catch (e) {
      form.submit();
    }
  });
}

function showCartToast(msg) {
  let toast = document.getElementById('cartToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'cartToast';
    toast.className = 'cart-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.display = 'block';
  toast.style.animation = 'none';
  setTimeout(() => { toast.style.animation = 'slideUpFade .3s ease'; }, 10);
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => { toast.style.display = 'none'; }, 3500);
}

function updateCartBadges(count) {
  document.querySelectorAll('.cart-badge-count').forEach(b => {
    b.textContent = count;
    b.style.display = count > 0 ? 'flex' : 'none';
  });
  // Update all badge-count near cart link
  document.querySelectorAll('[href*="/cart"] .badge-count').forEach(b => {
    b.textContent = count;
  });
}

// ── AJAX CART QUANTITY (cart page) ─────────────────
async function updateCart(itemId, action) {
  try {
    const fd = new FormData();
    fd.append('action', action);
    const resp = await fetch(`/cart/update/${itemId}`, {
      method: 'POST', body: fd,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    const data = await resp.json();
    if (data.removed) {
      const row = document.getElementById('cart-item-' + itemId);
      if (row) { row.style.opacity='0'; row.style.transition='opacity .3s'; setTimeout(()=>row.remove(), 300); }
      updateCartBadges(data.count);
      updateTotals();
      return;
    }
    const qtyEl = document.getElementById('qty-' + itemId);
    if (qtyEl) qtyEl.textContent = data.quantity;
    const priceEl = document.getElementById('price-' + itemId);
    if (priceEl) priceEl.textContent = formatAriary(data.total_item);
    const totalEl = document.getElementById('cartTotal');
    const totalFinalEl = document.getElementById('cartTotalFinal');
    const formatted = formatAriary(data.total);
    if (totalEl) totalEl.textContent = formatted;
    if (totalFinalEl) totalFinalEl.textContent = formatted;
    updateCartBadges(data.count);
  } catch(e) { location.reload(); }
}

function formatAriary(amount) {
  return 'Ar ' + Math.round(amount).toLocaleString('fr-FR').replace(/\s/g, ' ');
}

// ── PROFILE PHOTO PREVIEW ──────────────────────────
function previewFile(input, targetId) {
  if (!input.files[0]) return;
  const url = URL.createObjectURL(input.files[0]);
  const target = document.getElementById(targetId);
  if (target) target.src = url;
}

function previewCover(input) {
  if (!input.files[0]) return;
  const url = URL.createObjectURL(input.files[0]);
  const target = document.getElementById('coverPreview');
  if (target) {
    target.style.backgroundImage = `url('${url}')`;
    target.style.backgroundSize = 'cover';
    target.style.backgroundPosition = 'center';
  }
}

// ── PASSWORD TOGGLE ────────────────────────────────
function togglePass(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = '🙈';
  } else {
    input.type = 'password';
    btn.textContent = '👁';
  }
}
