/**
 * Interactive helper for likes, alerts, and dynamic UX.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Like button AJAX toggle
    const likeButton = document.querySelector('[data-action="like-btn"]');
    if (likeButton) {
        likeButton.addEventListener('click', async (e) => {
            e.preventDefault();
            const likeUrl = likeButton.getAttribute('data-like-url');
            const csrfToken = getCookie('csrftoken');

            if (!likeUrl) return;

            try {
                const response = await fetch(likeUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json',
                    },
                });

                if (response.status === 401 || response.status === 403 || response.redirected) {
                    // Redirect to login if user isn't authenticated
                    window.location.href = `/accounts/login/?next=${encodeURIComponent(window.location.pathname)}`;
                    return;
                }

                if (response.ok) {
                    const data = await response.json();
                    const countEl = document.getElementById('like-count');
                    const iconEl = document.getElementById('like-icon');
                    const textEl = document.getElementById('like-text');

                    if (countEl) countEl.textContent = data.count;

                    if (data.liked) {
                        likeButton.classList.remove('bg-rose-50', 'text-rose-600', 'border-rose-200', 'hover:bg-rose-100');
                        likeButton.classList.add('bg-rose-600', 'text-white', 'border-rose-600', 'hover:bg-rose-700', 'shadow-sm');
                        if (iconEl) {
                            iconEl.setAttribute('fill', 'currentColor');
                        }
                        if (textEl) textEl.textContent = 'Liked';
                    } else {
                        likeButton.classList.remove('bg-rose-600', 'text-white', 'border-rose-600', 'hover:bg-rose-700', 'shadow-sm');
                        likeButton.classList.add('bg-rose-50', 'text-rose-600', 'border-rose-200', 'hover:bg-rose-100');
                        if (iconEl) {
                            iconEl.setAttribute('fill', 'none');
                        }
                        if (textEl) textEl.textContent = 'Like';
                    }
                }
            } catch (err) {
                console.error('Error toggling like:', err);
            }
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-auto-dismiss');
    alerts.forEach((alert) => {
        setTimeout(() => {
            alert.classList.add('opacity-0', 'transition-opacity', 'duration-500');
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
});

// Helper function to read CSRF cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
