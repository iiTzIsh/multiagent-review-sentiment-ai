/**
 * Hotel Review Insight Platform - Dashboard JavaScript
 * Handles interactive features and AJAX communications
 */

// Global variables
let globalSearchModal;
let processingSocket;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeComponents();
    setupEventListeners();
    startPeriodicUpdates();
});

/**
 * Initialize UI components
 */
function initializeComponents() {
    // Initialize modals
    const searchModalElement = document.getElementById('searchResultsModal');
    if (searchModalElement) {
        globalSearchModal = new bootstrap.Modal(searchModalElement);
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Global search form
    const searchForm = document.getElementById('globalSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleGlobalSearch);
    }
    
    // File upload drag and drop
    setupFileUploadHandlers();
    
    // Chart interactions
    setupChartInteractions();
    
    // Real-time updates
    setupWebSocketConnection();
}

/**
 * Handle global search functionality
 */
function handleGlobalSearch(event) {
    event.preventDefault();
    
    const searchInput = document.getElementById('globalSearchInput');
    const query = searchInput.value.trim();
    
    if (!query) {
        showAlert('Please enter a search query', 'warning');
        return;
    }
    
    performSearch(query, 'semantic');
}

/**
 * Perform search operation
 */
async function performSearch(query, searchType = 'semantic') {
    try {
        // Show loading modal
        if (globalSearchModal) {
            globalSearchModal.show();
            showSearchLoading();
        }
        
        const response = await fetch('/dashboard/search/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                query: query,
                type: searchType
            })
        });
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            displaySearchResults(data.results, query);
        } else {
            throw new Error(data.error || 'Search failed');
        }
        
    } catch (error) {
        console.error('Search error:', error);
        showSearchError(error.message);
    }
}

/**
 * Display search results in modal
 */
function displaySearchResults(results, query) {
    const container = document.getElementById('searchResultsBody');
    
    if (!results || results.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No results found for "${query}"
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="mb-3">
            <h6>Found ${results.length} result(s) for "${query}"</h6>
        </div>
        <div class="list-group">
    `;
    
    results.forEach(result => {
        const sentimentClass = getSentimentClass(result.sentiment);
        const scoreWidth = (result.score / 5) * 100;
        
        html += `
            <div class="list-group-item search-result-item sentiment-${result.sentiment}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <p class="mb-2">${highlightSearchTerms(result.text, query)}</p>
                        <div class="d-flex gap-2 align-items-center">
                            <span class="badge bg-${sentimentClass}">${result.sentiment}</span>
                            <span class="text-muted">Score: ${result.score}</span>
                            ${result.similarity ? `<span class="text-muted">Match: ${(result.similarity * 100).toFixed(1)}%</span>` : ''}
                            ${result.hotel ? `<span class="text-muted">Hotel: ${result.hotel}</span>` : ''}
                        </div>
                    </div>
                    <div class="ms-3">
                        <div class="progress" style="width: 60px; height: 8px;">
                            <div class="progress-bar bg-${sentimentClass}" 
                                 style="width: ${scoreWidth}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Show search loading state
 */
function showSearchLoading() {
    const container = document.getElementById('searchResultsBody');
    container.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Searching...</span>
            </div>
            <p class="mt-2 text-muted">Analyzing reviews with AI agents...</p>
        </div>
    `;
}

/**
 * Show search error
 */
function showSearchError(errorMessage) {
    const container = document.getElementById('searchResultsBody');
    container.innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle me-2"></i>
            Search failed: ${errorMessage}
        </div>
    `;
}

/**
 * Setup file upload drag and drop handlers
 */
function setupFileUploadHandlers() {
    const uploadZone = document.querySelector('.upload-zone');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadZone && fileInput) {
        // Drag and drop events
        uploadZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });
        
        uploadZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
        });
        
        uploadZone.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelection(files[0]);
            }
        });
        
        // File input change
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                handleFileSelection(e.target.files[0]);
            }
        });
    }
}

/**
 * Handle file selection and validation
 */
function handleFileSelection(file) {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = ['.csv', '.xlsx', '.xls'];
    
    // Validate file size
    if (file.size > maxSize) {
        showAlert('File size must be less than 10MB', 'danger');
        return false;
    }
    
    // Validate file type
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(fileExtension)) {
        showAlert('Only CSV and Excel files are supported', 'danger');
        return false;
    }
    
    // Show file info
    showFileInfo(file);
    return true;
}

/**
 * Show file information
 */
function showFileInfo(file) {
    const fileSize = (file.size / 1024 / 1024).toFixed(2);
    const info = `
        <div class="alert alert-success">
            <i class="fas fa-file me-2"></i>
            <strong>${file.name}</strong> (${fileSize} MB) selected
        </div>
    `;
    
    // Insert after file input
    const fileInput = document.getElementById('fileInput');
    const existingInfo = fileInput.parentNode.querySelector('.file-info');
    if (existingInfo) {
        existingInfo.remove();
    }
    
    const infoDiv = document.createElement('div');
    infoDiv.className = 'file-info mt-2';
    infoDiv.innerHTML = info;
    fileInput.parentNode.insertBefore(infoDiv, fileInput.nextSibling);
}

/**
 * Setup chart interactions
 */
function setupChartInteractions() {
    // Add click handlers to charts for drilling down
    const charts = document.querySelectorAll('canvas[id$="Chart"]');
    
    charts.forEach(chart => {
        chart.addEventListener('click', function(event) {
            const chartInstance = Chart.getChart(chart);
            if (chartInstance) {
                const points = chartInstance.getElementsAtEventForMode(event, 'nearest', { intersect: true }, true);
                
                if (points.length) {
                    const firstPoint = points[0];
                    const label = chartInstance.data.labels[firstPoint.index];
                    const value = chartInstance.data.datasets[firstPoint.datasetIndex].data[firstPoint.index];
                    
                    // Handle chart click (e.g., filter by clicked segment)
                    handleChartClick(chart.id, label, value);
                }
            }
        });
    });
}

/**
 * Handle chart click events
 */
function handleChartClick(chartId, label, value) {
    if (chartId === 'sentimentChart') {
        // Filter reviews by sentiment
        window.location.href = `/dashboard/reviews/?sentiment=${label.toLowerCase()}`;
    } else if (chartId === 'scoreChart') {
        // Filter reviews by score range
        const [min, max] = label.split('-').map(parseFloat);
        window.location.href = `/dashboard/reviews/?min_score=${min}&max_score=${max}`;
    }
}

/**
 * Setup WebSocket connection for real-time updates
 */
function setupWebSocketConnection() {
    // In production, this would establish WebSocket connection
    // For now, we'll use polling
    console.log('WebSocket connection would be established here');
}

/**
 * Start periodic updates
 */
function startPeriodicUpdates() {
    // Update processing status every 30 seconds
    setInterval(updateProcessingStatus, 30000);
    
    // Update charts every 60 seconds
    setInterval(updateCharts, 60000);
}

/**
 * Update processing status indicator
 */
async function updateProcessingStatus() {
    try {
        const response = await fetch('/api/v1/agents/status/');
        const data = await response.json();
        
        const statusElement = document.getElementById('processingStatus');
        if (statusElement) {
            if (data.all_operational) {
                statusElement.className = 'badge bg-success';
                statusElement.innerHTML = '<i class="fas fa-check-circle me-1"></i>All Systems Operational';
            } else {
                statusElement.className = 'badge bg-warning';
                statusElement.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Some Issues Detected';
            }
        }
        
    } catch (error) {
        console.error('Failed to update processing status:', error);
    }
}

/**
 * Update charts with latest data
 */
async function updateCharts() {
    try {
        // This would fetch updated chart data from the server
        console.log('Updating charts with latest data...');
        
    } catch (error) {
        console.error('Failed to update charts:', error);
    }
}

/**
 * Process all unprocessed reviews
 */
async function processAllReviews() {
    if (!confirm('This will process all unprocessed reviews using AI agents. This may take several minutes. Continue?')) {
        return;
    }
    
    try {
        const button = event.target;
        const originalHTML = button.innerHTML;
        
        // Show loading state
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
        button.disabled = true;
        
        const response = await fetch('/api/v1/process/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                process_all: true
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Review processing started successfully. You will see updates in real-time.', 'success');
            
            // Start monitoring progress
            monitorProcessingProgress(data.task_id);
        } else {
            throw new Error(data.error || 'Processing failed');
        }
        
    } catch (error) {
        console.error('Processing error:', error);
        showAlert(`Processing failed: ${error.message}`, 'danger');
    } finally {
        // Reset button
        setTimeout(() => {
            const button = document.querySelector('button[onclick="processAllReviews()"]');
            if (button) {
                button.innerHTML = '<i class="fas fa-cogs me-1"></i>Process All Reviews';
                button.disabled = false;
            }
        }, 1000);
    }
}

/**
 * Monitor processing progress
 */
async function monitorProcessingProgress(taskId) {
    const progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/v1/agents/tasks/${taskId}/`);
            const data = await response.json();
            
            if (data.status === 'completed' || data.status === 'failed') {
                clearInterval(progressInterval);
                
                if (data.status === 'completed') {
                    showAlert('All reviews processed successfully!', 'success');
                    // Refresh page to show updated data
                    setTimeout(() => window.location.reload(), 2000);
                } else {
                    showAlert('Processing failed. Please check the logs.', 'danger');
                }
            }
            
        } catch (error) {
            console.error('Progress monitoring error:', error);
            clearInterval(progressInterval);
        }
    }, 5000); // Check every 5 seconds
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
    alertContainer.innerHTML = `
        <i class="fas fa-${getAlertIcon(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of main content
    const main = document.querySelector('main');
    if (main) {
        main.insertBefore(alertContainer, main.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertContainer.parentNode) {
                alertContainer.remove();
            }
        }, 5000);
    }
}

/**
 * Get appropriate icon for alert type
 */
function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Get sentiment class for styling
 */
function getSentimentClass(sentiment) {
    const classes = {
        'positive': 'success',
        'negative': 'danger',
        'neutral': 'warning'
    };
    return classes[sentiment] || 'secondary';
}

/**
 * Highlight search terms in text
 */
function highlightSearchTerms(text, searchQuery) {
    if (!searchQuery) return text;
    
    const regex = new RegExp(`(${searchQuery})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

/**
 * Get CSRF token from cookies
 */
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return decodeURIComponent(value);
        }
    }
    return '';
}

/**
 * Format number with appropriate suffix
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showAlert('Copied to clipboard!', 'success');
    } catch (error) {
        console.error('Copy failed:', error);
        showAlert('Failed to copy to clipboard', 'danger');
    }
}

/**
 * Download data as file
 */
function downloadData(data, filename, type = 'application/json') {
    const blob = new Blob([data], { type: type });
    const url = window.URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

/**
 * Refresh specific component
 */
async function refreshComponent(componentId) {
    const component = document.getElementById(componentId);
    if (!component) return;
    
    // Add loading state
    component.style.opacity = '0.5';
    
    try {
        // Simulate refresh (would make actual API call in production)
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Reset opacity
        component.style.opacity = '1';
        
        showAlert('Component refreshed successfully', 'success');
        
    } catch (error) {
        component.style.opacity = '1';
        showAlert('Failed to refresh component', 'danger');
    }
}

/**
 * Export current view data
 */
function exportCurrentView(format = 'csv') {
    const currentUrl = new URL(window.location.href);
    currentUrl.pathname = '/dashboard/export/';
    currentUrl.searchParams.set('format', format);
    
    // Add current filters to export
    const urlParams = new URLSearchParams(window.location.search);
    for (const [key, value] of urlParams.entries()) {
        currentUrl.searchParams.set(key, value);
    }
    
    window.open(currentUrl.toString(), '_blank');
}

/**
 * Toggle full screen mode for charts
 */
function toggleChartFullscreen(chartId) {
    const chart = document.getElementById(chartId);
    const container = chart.closest('.card');
    
    if (container.classList.contains('fullscreen-chart')) {
        container.classList.remove('fullscreen-chart');
        document.body.style.overflow = 'auto';
    } else {
        container.classList.add('fullscreen-chart');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Add fullscreen chart styles
 */
const style = document.createElement('style');
style.textContent = `
    .fullscreen-chart {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: 9999;
        background: white;
        margin: 0;
    }
    
    .fullscreen-chart .card-body {
        height: calc(100vh - 120px);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .fullscreen-chart canvas {
        max-width: 90vw;
        max-height: 80vh;
    }
`;
document.head.appendChild(style);

// Global functions for template access
window.performSearch = performSearch;
window.processAllReviews = processAllReviews;
window.exportCurrentView = exportCurrentView;
window.refreshComponent = refreshComponent;
window.toggleChartFullscreen = toggleChartFullscreen;
