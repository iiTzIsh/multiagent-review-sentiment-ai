/**
 * Simplified Dashboard JavaScript
 * Basic functionality without complex dependencies
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeBasicComponents();
});

/**
 * Initialize basic UI components
 */
function initializeBasicComponents() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Setup search form
    const searchForm = document.getElementById('globalSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleGlobalSearch);
    }
    
    // Setup process reviews button
    const processBtn = document.querySelector('[onclick="processAllReviews()"]');
    if (processBtn) {
        processBtn.addEventListener('click', function(e) {
            e.preventDefault();
            processAllReviews();
        });
        processBtn.removeAttribute('onclick'); // Remove inline onclick
    }
}

/**
 * Handle global search
 */
function handleGlobalSearch(e) {
    e.preventDefault();
    const query = document.getElementById('globalSearchInput')?.value;
    if (query && query.trim()) {
        // Show modal if it exists
        const modal = document.getElementById('searchResultsModal');
        if (modal && typeof bootstrap !== 'undefined') {
            const searchModal = new bootstrap.Modal(modal);
            searchModal.show();
            performSearch(query);
        } else {
            // Fallback - simple alert
            alert('Search functionality will be implemented soon. Query: ' + query);
        }
    }
}

/**
 * Perform search
 */
function performSearch(query) {
    const resultsBody = document.getElementById('searchResultsBody');
    if (!resultsBody) return;
    
    resultsBody.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Searching...</span></div></div>';
    
    // Simple mock search - in production this would call the API
    setTimeout(() => {
        resultsBody.innerHTML = '<div class="alert alert-info">Search functionality is being implemented. Your query: <strong>' + query + '</strong></div>';
    }, 1000);
}

/**
 * Process all reviews
 */
function processAllReviews() {
    if (confirm('This will process all unprocessed reviews using AI agents. Continue?')) {
        const button = event.target;
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
        button.disabled = true;
        
        // Mock processing
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
            alert('Review processing started. Check the analytics page for updates.');
        }, 2000);
    }
}

/**
 * Utility function to get CSRF token
 */
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

// Auto-refresh status every 30 seconds (optional)
setInterval(function() {
    console.log('Dashboard status check...');
}, 30000);
