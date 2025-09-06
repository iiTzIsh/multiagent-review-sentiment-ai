// Enhanced Dashboard JavaScript for Hotel Review Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize smooth animations
    initializeAnimations();
    
    // Initialize dashboard functionality
    initializeDashboard();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize chart themes
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    Chart.defaults.font.size = 12;
});

// Initialize Bootstrap tooltips and popovers
function initializeTooltips() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover focus'
        });
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Initialize smooth animations and interactions
function initializeAnimations() {
    // Add smooth hover effects to cards
    const cards = document.querySelectorAll('.card, .metric-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Add staggered animation to grid items
    const gridItems = document.querySelectorAll('.fade-in');
    gridItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.1}s`;
    });
}

// Initialize main dashboard functionality
function initializeDashboard() {
    // Process Reviews button
    const processBtn = document.getElementById('process-reviews-btn');
    if (processBtn) {
        processBtn.addEventListener('click', function() {
            handleProcessReviews();
        });
    }
    
    // Refresh button
    const refreshBtn = document.querySelector('.btn[data-bs-toggle="tooltip"][title*="Refresh"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            handleRefreshDashboard();
        });
    }
    
    // Auto-refresh data every 5 minutes
    setInterval(function() {
        refreshDashboardData();
    }, 300000); // 5 minutes
}

// Initialize search functionality
function initializeSearch() {
    const searchForm = document.getElementById('globalSearchForm');
    const searchInput = document.getElementById('globalSearchInput');
    
    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleGlobalSearch(searchInput.value.trim());
        });
        
        // Add debounced search suggestions
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.trim().length > 2) {
                    fetchSearchSuggestions(this.value.trim());
                }
            }, 500);
        });
    }
}

// Handle processing reviews
function handleProcessReviews() {
    const btn = document.getElementById('process-reviews-btn');
    const originalText = btn.innerHTML;
    
    // Show loading state
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
    
    // Show loading overlay
    showLoadingOverlay('Processing reviews with AI agents...');
    
    fetch('/api/process-reviews/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Reviews processing started successfully!', 'success', 'Processing Started');
            // Poll for status updates
            pollProcessingStatus();
        } else {
            showToast(data.message || 'Failed to start processing', 'error', 'Processing Error');
        }
    })
    .catch(error => {
        console.error('Processing error:', error);
        showToast('An error occurred while starting processing', 'error', 'Error');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = originalText;
        hideLoadingOverlay();
    });
}

// Handle dashboard refresh
function handleRefreshDashboard() {
    showLoadingOverlay('Refreshing dashboard data...');
    
    // Refresh all dashboard components
    Promise.all([
        refreshStatistics(),
        refreshCharts(),
        refreshRecentActivity()
    ])
    .then(() => {
        showToast('Dashboard data refreshed successfully!', 'success', 'Data Refreshed');
    })
    .catch(error => {
        console.error('Refresh error:', error);
        showToast('Failed to refresh dashboard data', 'error', 'Refresh Error');
    })
    .finally(() => {
        hideLoadingOverlay();
    });
}

// Handle global search
function handleGlobalSearch(query) {
    if (!query) {
        showToast('Please enter a search term', 'warning', 'Search');
        return;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('searchResultsModal'));
    const modalBody = document.getElementById('searchResultsBody');
    
    // Show modal with loading state
    modalBody.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Searching...</span>
            </div>
            <p class="mt-3 text-muted">Searching through reviews...</p>
        </div>
    `;
    modal.show();
    
    // Perform search
    fetch(`/api/search/?q=${encodeURIComponent(query)}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displaySearchResults(data.results);
        } else {
            modalBody.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-exclamation-triangle text-warning fa-3x mb-3"></i>
                    <p class="text-muted">No results found for "${query}"</p>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Search error:', error);
        modalBody.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-times-circle text-danger fa-3x mb-3"></i>
                <p class="text-muted">An error occurred while searching</p>
            </div>
        `;
    });
}

// Display search results in modal
function displaySearchResults(results) {
    const modalBody = document.getElementById('searchResultsBody');
    
    if (!results || results.length === 0) {
        modalBody.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <p class="text-muted">No results found</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="search-results">';
    results.forEach(result => {
        const sentimentClass = result.sentiment?.toLowerCase() || 'neutral';
        html += `
            <div class="search-result-item sentiment-${sentimentClass}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-1">${escapeHtml(result.hotel_name || 'Unknown Hotel')}</h6>
                    <span class="badge badge-${sentimentClass}">${result.sentiment || 'Neutral'}</span>
                </div>
                <p class="text-muted mb-2">${escapeHtml(result.content?.substring(0, 200) + '...' || 'No content')}</p>
                <div class="meta">
                    <span><i class="fas fa-star text-warning me-1"></i>${result.rating || 'N/A'}</span>
                    <span><i class="fas fa-calendar me-1"></i>${formatDate(result.date)}</span>
                    <span><i class="fas fa-user me-1"></i>${escapeHtml(result.reviewer || 'Anonymous')}</span>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    modalBody.innerHTML = html;
}

// Utility functions
function showLoadingOverlay(message = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        const messageEl = overlay.querySelector('p');
        if (messageEl) {
            messageEl.textContent = message;
        }
        overlay.classList.remove('d-none');
    }
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('d-none');
    }
}

function showToast(message, type = 'info', title = 'Notification') {
    // Create toast element
    const toastContainer = document.querySelector('.toast-container');
    const toastId = 'toast-' + Date.now();
    
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="fas ${getToastIcon(type)} me-2"></i>
                <strong class="me-auto">${title}</strong>
                <small class="text-muted">now</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
    
    // Remove from DOM after hiding
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

function getToastIcon(type) {
    switch(type) {
        case 'success': return 'fa-check-circle text-success';
        case 'error': return 'fa-exclamation-triangle text-danger';
        case 'warning': return 'fa-exclamation-circle text-warning';
        default: return 'fa-info-circle text-info';
    }
}

function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Chart enhancement functions
function createEnhancedChart(ctx, type, data, options = {}) {
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    padding: 20,
                    usePointStyle: true
                }
            }
        },
        elements: {
            arc: {
                borderWidth: 2
            },
            bar: {
                borderRadius: 4
            },
            line: {
                tension: 0.4
            }
        }
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    return new Chart(ctx, {
        type: type,
        data: data,
        options: mergedOptions
    });
}

// Export functions for use in other scripts
window.dashboardUtils = {
    showToast,
    showLoadingOverlay,
    hideLoadingOverlay,
    createEnhancedChart,
    getCsrfToken
};
