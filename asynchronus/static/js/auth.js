// =============================================
//  auth.js — login state, token, logout
// =============================================


// ── TOKEN HELPERS ──────────────────────────────
function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function clearToken() {
    localStorage.removeItem('token');
}

function isLoggedIn() {
    return !!getToken();
}

// returns headers with Authorization if logged in
function authHeaders() {
    const token = getToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
}


// ── LOGOUT ──────────────────────────────────────
function logout() {
    clearToken();
    window.location.href = '/';
}


// ── NAVBAR LOGIN STATE ─────────────────────────
// Replaces the "Login" button with the username + Logout
// if a valid token exists. Runs on every page via DOMContentLoaded.
async function initAuthArea() {
    const authArea = document.getElementById('authArea');
    if (!authArea) return;

    const token = getToken();
    if (!token) return; // not logged in — Login button stays as-is (default HTML)

    try {
        const res = await fetch('/api/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) {
            clearToken(); // token invalid/expired
            return;
        }

        const user = await res.json();

        authArea.innerHTML = `
            <a href="/users/${user.id}/posts" class="text-white-50 small text-decoration-none">
                ${user.username}
            </a>
            <button class="btn btn-sm btn-outline-light" onclick="logout()">Logout</button>
        `;
    } catch (err) {
        console.error('Failed to fetch current user', err);
    }
}


// ── INIT ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    initAuthArea();
});