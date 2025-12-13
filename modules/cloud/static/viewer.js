// SeenSlide Viewer JavaScript

class SlideViewer {
    constructor() {
        this.sessionId = null;
        this.session = null;
        this.slides = [];
        this.currentSlideIndex = 0;
        this.isAuthenticated = false;

        this.init();
    }

    init() {
        // Parse session ID from URL
        this.sessionId = this.getSessionIdFromURL();

        if (!this.sessionId) {
            this.showError('Invalid URL', 'No session ID provided');
            return;
        }

        // Set up event listeners
        this.setupEventListeners();

        // Load session
        this.loadSession();
    }

    getSessionIdFromURL() {
        // Extract session ID from path (e.g., /ABC-1234)
        const path = window.location.pathname;
        const match = path.match(/\/([A-Z]{3}-\d{4})/);
        return match ? match[1] : null;
    }

    setupEventListeners() {
        // Password form
        const passwordForm = document.getElementById('passwordForm');
        if (passwordForm) {
            passwordForm.addEventListener('submit', (e) => this.handlePasswordSubmit(e));
        }

        // Navigation buttons
        document.getElementById('prevBtn')?.addEventListener('click', () => this.previousSlide());
        document.getElementById('nextBtn')?.addEventListener('click', () => this.nextSlide());

        // Fullscreen button
        document.getElementById('fullscreenBtn')?.addEventListener('click', () => this.toggleFullscreen());

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
    }

    async loadSession() {
        try {
            const response = await fetch(`/api/cloud/session/${this.sessionId}`);

            if (response.status === 404) {
                this.showNotFound();
                return;
            }

            if (!response.ok) {
                throw new Error('Failed to load session');
            }

            this.session = await response.json();

            // Check if password is required
            if (this.session.access_type === 'password_protected') {
                this.showPasswordModal();
            } else if (this.session.access_type === 'public') {
                this.isAuthenticated = true;
                this.showViewer();
                this.loadSlides();
            } else {
                this.showError('Access Denied', 'This session is private');
            }
        } catch (error) {
            console.error('Error loading session:', error);
            this.showError('Error', 'Failed to load session');
        }
    }

    async handlePasswordSubmit(e) {
        e.preventDefault();

        const passwordInput = document.getElementById('passwordInput');
        const password = passwordInput.value;
        const errorDiv = document.getElementById('passwordError');

        try {
            const response = await fetch(`/api/cloud/session/${this.sessionId}/verify-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ password })
            });

            const result = await response.json();

            if (result.valid) {
                this.isAuthenticated = true;
                this.hidePasswordModal();
                this.showViewer();
                this.loadSlides();
            } else {
                errorDiv.textContent = result.message || 'Incorrect password';
                errorDiv.style.display = 'block';
                passwordInput.value = '';
                passwordInput.focus();
            }
        } catch (error) {
            console.error('Error verifying password:', error);
            errorDiv.textContent = 'Error verifying password';
            errorDiv.style.display = 'block';
        }
    }

    async loadSlides() {
        try {
            // TODO: Replace with actual API endpoint when implemented
            // For now, show placeholder
            this.updateSessionInfo();

            // Check if there are slides
            if (this.session.total_slides === 0) {
                this.showNoSlides();
            } else {
                // This will be implemented when we add the slides API
                console.log('Slides will be loaded from API');
            }
        } catch (error) {
            console.error('Error loading slides:', error);
        }
    }

    updateSessionInfo() {
        document.getElementById('sessionTitle').textContent = this.session.presenter_name || 'Presentation';
        document.getElementById('sessionPresenter').textContent = this.session.presenter_name;
        document.getElementById('sessionStatus').textContent = this.session.status;
        this.updateSlideCounter();
    }

    updateSlideCounter() {
        const counter = document.getElementById('slideCounter');
        if (this.slides.length === 0) {
            counter.textContent = '0 / 0';
        } else {
            counter.textContent = `${this.currentSlideIndex + 1} / ${this.slides.length}`;
        }
    }

    showSlide(index) {
        if (index < 0 || index >= this.slides.length) return;

        this.currentSlideIndex = index;

        const slideImg = document.getElementById('currentSlide');
        const noSlidesMsg = document.getElementById('noSlidesMessage');

        if (this.slides.length > 0) {
            slideImg.src = this.slides[index].url;
            slideImg.style.display = 'block';
            noSlidesMsg.style.display = 'none';
        }

        this.updateSlideCounter();
        this.updateNavigationButtons();
        this.highlightThumbnail(index);
    }

    previousSlide() {
        if (this.currentSlideIndex > 0) {
            this.showSlide(this.currentSlideIndex - 1);
        }
    }

    nextSlide() {
        if (this.currentSlideIndex < this.slides.length - 1) {
            this.showSlide(this.currentSlideIndex + 1);
        }
    }

    updateNavigationButtons() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');

        if (prevBtn) prevBtn.disabled = this.currentSlideIndex === 0;
        if (nextBtn) nextBtn.disabled = this.currentSlideIndex === this.slides.length - 1;
    }

    highlightThumbnail(index) {
        document.querySelectorAll('.thumbnail').forEach((thumb, i) => {
            thumb.classList.toggle('active', i === index);
        });
    }

    handleKeyPress(e) {
        if (!this.isAuthenticated) return;

        switch(e.key) {
            case 'ArrowLeft':
            case 'PageUp':
                this.previousSlide();
                break;
            case 'ArrowRight':
            case 'PageDown':
            case ' ':
                e.preventDefault();
                this.nextSlide();
                break;
            case 'Home':
                this.showSlide(0);
                break;
            case 'End':
                this.showSlide(this.slides.length - 1);
                break;
            case 'f':
            case 'F':
                this.toggleFullscreen();
                break;
        }
    }

    toggleFullscreen() {
        const container = document.getElementById('viewerContainer');

        if (!document.fullscreenElement) {
            container.requestFullscreen?.() ||
            container.webkitRequestFullscreen?.() ||
            container.mozRequestFullScreen?.();
        } else {
            document.exitFullscreen?.() ||
            document.webkitExitFullscreen?.() ||
            document.mozCancelFullScreen?.();
        }
    }

    showPasswordModal() {
        document.getElementById('loadingScreen').style.display = 'none';
        document.getElementById('passwordModal').style.display = 'flex';
        document.getElementById('passwordInput').focus();
    }

    hidePasswordModal() {
        document.getElementById('passwordModal').style.display = 'none';
    }

    showViewer() {
        document.getElementById('loadingScreen').style.display = 'none';
        document.getElementById('viewerContainer').style.display = 'grid';
    }

    showNoSlides() {
        document.getElementById('currentSlide').style.display = 'none';
        document.getElementById('noSlidesMessage').style.display = 'block';
    }

    showNotFound() {
        document.getElementById('loadingScreen').style.display = 'none';
        document.getElementById('notFoundScreen').style.display = 'flex';
    }

    showError(title, message) {
        document.getElementById('loadingScreen').style.display = 'none';
        const errorScreen = document.getElementById('notFoundScreen');
        errorScreen.querySelector('h2').textContent = title;
        errorScreen.querySelector('p').textContent = message;
        errorScreen.style.display = 'flex';
    }
}

// Initialize viewer when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new SlideViewer());
} else {
    new SlideViewer();
}
