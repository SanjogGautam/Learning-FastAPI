// =============================================
//  utils.js — shared JS for the whole app
// =============================================


// ── 1. DARK MODE ──────────────────────────────
// runs immediately when the script loads
(function () {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', saved);
})();

function initThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    const label  = document.getElementById('themeLabel');
    const html   = document.documentElement;

    if (!toggle) return;

    const saved = localStorage.getItem('theme') || 'light';
    toggle.checked    = saved === 'dark';
    label.textContent = saved === 'dark' ? '☀️' : '🌙';

    toggle.addEventListener('change', function () {
        const theme = this.checked ? 'dark' : 'light';
        html.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
        label.textContent = theme === 'dark' ? '☀️' : '🌙';
    });
}


// ── 2. NEW POST MODAL ─────────────────────────
let newPostModal = null;

function initNewPostModal() {
    const el = document.getElementById('newPostModal');
    if (!el) return;
    newPostModal = new bootstrap.Modal(el);
}

function openNewPostModal() {
    document.getElementById('newTitle').value   = '';
    document.getElementById('newContent').value = '';
    document.getElementById('newUserId').value  = '';
    document.getElementById('newPostError').classList.add('d-none');
    newPostModal.show();
}

async function saveNewPost() {
    const title    = document.getElementById('newTitle').value.trim();
    const content  = document.getElementById('newContent').value.trim();
    const user_id  = parseInt(document.getElementById('newUserId').value);
    const errorDiv = document.getElementById('newPostError');

    if (!title || !content || !user_id) {
        errorDiv.textContent = 'All fields are required.';
        errorDiv.classList.remove('d-none');
        return;
    }

    const res = await fetch('/api/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content, user_id })
    });

    if (res.ok) {
        const data = await res.json();
        newPostModal.hide();
        window.location.href = `/posts/${data.id}`;
    } else {
        const data = await res.json();
        errorDiv.textContent = data.detail || 'Failed to create post.';
        errorDiv.classList.remove('d-none');
    }
}


// ── 3. EDIT POST MODAL ────────────────────────
let editModal     = null;
let currentPostId = null;

function initEditModal() {
    const el = document.getElementById('editModal');
    if (!el) return;
    editModal = new bootstrap.Modal(el);
}

function openEditModal(id, title, content) {
    currentPostId = id;
    document.getElementById('editTitle').value   = title;
    document.getElementById('editContent').value = content;
    document.getElementById('editError').classList.add('d-none');
    editModal.show();
}

async function saveEdit() {
    const title    = document.getElementById('editTitle').value.trim();
    const content  = document.getElementById('editContent').value.trim();
    const errorDiv = document.getElementById('editError');

    if (!title || !content) {
        errorDiv.textContent = 'Title and content are required.';
        errorDiv.classList.remove('d-none');
        return;
    }

    const res = await fetch(`/api/posts/${currentPostId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content })
    });

    if (res.ok) {
        editModal.hide();
        location.reload();
    } else {
        const data = await res.json();
        errorDiv.textContent = data.detail || 'Failed to save.';
        errorDiv.classList.remove('d-none');
    }
}


// ── 4. DELETE POST ────────────────────────────
async function deletePost(id) {
    if (!confirm('Delete this post?')) return;
    const res = await fetch(`/api/posts/${id}`, { method: 'DELETE' });
    if (res.ok) {
        if (window.location.pathname.startsWith('/posts/')) {
            window.location.href = '/';
        } else {
            location.reload();
        }
    } else {
        alert('Failed to delete post.');
    }
}


// ── 5. INIT EVERYTHING ON PAGE LOAD ──────────
document.addEventListener('DOMContentLoaded', function () {
    initThemeToggle();
    initNewPostModal();
    initEditModal();
});