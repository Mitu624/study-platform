/**
 * Modern Minimalist JavaScript for Study Platform
 * Clean, smooth, and sophisticated interactions
 */

// ==================== DOCUMENT READY ====================
$(document).ready(function() {
    // Initialize all components
    initSmoothScrolling();
    initParallaxEffects();
    initLazyLoading();
    initTooltips();
    initFormValidation();
    initFileUploads();
    initSearch();
    
    // Auto-dismiss alerts
    setTimeout(() => {
        $('.alert').fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
});

// ==================== SMOOTH SCROLLING ====================
function initSmoothScrolling() {
    $('a[href^="#"]').on('click', function(e) {
        e.preventDefault();
        const target = $(this.hash);
        if (target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 80
            }, 800, 'easeInOutCubic');
        }
    });
}

// Add easing function
$.easing.easeInOutCubic = function(x, t, b, c, d) {
    if ((t /= d / 2) < 1) return c / 2 * t * t * t + b;
    return c / 2 * ((t -= 2) * t * t + 2) + b;
};

// ==================== PARALLAX EFFECTS ====================
function initParallaxEffects() {
    $(window).on('scroll', function() {
        const scrolled = $(window).scrollTop();
        
        $('.parallax').each(function() {
            const speed = $(this).data('speed') || 0.5;
            $(this).css('transform', `translateY(${scrolled * speed}px)`);
        });
    });
}

// ==================== LAZY LOADING ====================
function initLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.add('fade-in');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    } else {
        // Fallback
        document.querySelectorAll('img[data-src]').forEach(img => {
            img.src = img.dataset.src;
        });
    }
}

// ==================== TOOLTIPS ====================
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            animation: true,
            delay: { show: 200, hide: 100 }
        });
    });
}

// ==================== FORM VALIDATION ====================
function initFormValidation() {
    // Real-time validation
    $('input[required], textarea[required], select[required]').on('input change', function() {
        validateField($(this));
    });

    // Form submit validation
    $('form').on('submit', function(e) {
        let isValid = true;
        const form = $(this);
        
        form.find('input[required], textarea[required], select[required]').each(function() {
            if (!validateField($(this))) {
                isValid = false;
            }
        });

        if (!isValid) {
            e.preventDefault();
            showNotification('Please fill in all required fields', 'error');
        }
    });
}

function validateField($field) {
    const value = $field.val().trim();
    const isValid = value.length > 0;
    
    if (isValid) {
        $field.removeClass('is-invalid').addClass('is-valid');
    } else {
        $field.removeClass('is-valid').addClass('is-invalid');
    }
    
    return isValid;
}

// Add validation styles
$('<style>')
    .prop('type', 'text/css')
    .html(`
        .is-valid {
            border-color: var(--success) !important;
        }
        
        .is-invalid {
            border-color: var(--danger) !important;
        }
        
        .is-invalid:focus {
            box-shadow: 0 0 0 3px rgba(255, 118, 117, 0.1) !important;
        }
    `)
    .appendTo('head');

// ==================== FILE UPLOADS ====================
function initFileUploads() {
    $('.drop-zone').each(function() {
        const dropZone = $(this);
        const input = dropZone.find('input[type="file"]');
        const preview = dropZone.find('.file-preview');
        
        // Click to browse
        dropZone.on('click', function(e) {
            if (!$(e.target).is('button')) {
                input.click();
            }
        });

        // Drag & drop
        dropZone.on('dragover', function(e) {
            e.preventDefault();
            dropZone.addClass('dragover');
        });

        dropZone.on('dragleave', function(e) {
            e.preventDefault();
            dropZone.removeClass('dragover');
        });

        dropZone.on('drop', function(e) {
            e.preventDefault();
            dropZone.removeClass('dragover');
            
            const files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                input.prop('files', files);
                handleFileSelect(files[0], dropZone);
            }
        });

        // File selection
        input.on('change', function() {
            if (this.files.length > 0) {
                handleFileSelect(this.files[0], dropZone);
            }
        });
    });
}

function handleFileSelect(file, dropZone) {
    const maxSize = 100 * 1024 * 1024; // 100MB
    
    if (file.size > maxSize) {
        showNotification('File size exceeds 100MB limit', 'error');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        let previewHtml = '';
        
        if (file.type.startsWith('image/')) {
            previewHtml = `
                <div class="file-preview">
                    <img src="${e.target.result}" class="preview-image" style="max-width: 100%; max-height: 200px; border-radius: var(--radius-md);">
                    <div class="file-name">${escapeHtml(file.name)}</div>
                    <div class="file-size">${formatFileSize(file.size)}</div>
                </div>
            `;
        } else {
            const icon = getFileIcon(file.name);
            previewHtml = `
                <div class="file-preview">
                    <i class="fas ${icon} file-icon"></i>
                    <div class="file-name">${escapeHtml(file.name)}</div>
                    <div class="file-size">${formatFileSize(file.size)}</div>
                </div>
            `;
        }
        
        dropZone.find('.preview-container').html(previewHtml);
    };
    
    reader.readAsDataURL(file);
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': 'fa-file-pdf pdf',
        'ppt': 'fa-file-powerpoint ppt',
        'pptx': 'fa-file-powerpoint ppt',
        'csv': 'fa-file-csv csv',
        'txt': 'fa-file-alt text',
        'md': 'fa-file-alt text',
        'png': 'fa-image image',
        'jpg': 'fa-image image',
        'jpeg': 'fa-image image',
        'gif': 'fa-image image',
        'webp': 'fa-image image'
    };
    return icons[ext] || 'fa-file';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// ==================== SEARCH ====================
function initSearch() {
    const searchInput = $('#globalSearch');
    const searchResults = $('#searchResults');
    
    let searchTimeout;
    
    searchInput.on('input', function() {
        clearTimeout(searchTimeout);
        const query = $(this).val().trim();
        
        if (query.length < 2) {
            searchResults.fadeOut();
            return;
        }
        
        searchTimeout = setTimeout(() => {
            performSearch(query);
        }, 300);
    });
    
    $(document).on('click', function(e) {
        if (!searchResults.is(e.target) && searchResults.has(e.target).length === 0) {
            searchResults.fadeOut();
        }
    });
}

function performSearch(query) {
    showLoading();
    
    $.ajax({
        url: '/api/search',
        data: { q: query },
        method: 'GET',
        success: function(data) {
            displaySearchResults(data.results || []);
        },
        error: function() {
            showNotification('Search failed', 'error');
        },
        complete: function() {
            hideLoading();
        }
    });
}

function displaySearchResults(results) {
    const container = $('#searchResults');
    container.empty();
    
    if (!results.length) {
        container.html('<div class="search-empty">No results found</div>');
        container.fadeIn();
        return;
    }
    
    let html = '';
    results.forEach(result => {
        html += createSearchResultItem(result);
    });
    
    container.html(html);
    container.fadeIn();
}

function createSearchResultItem(item) {
    const typeIcon = {
        material: 'fa-file-alt',
        task: 'fa-tasks',
        category: 'fa-folder'
    }[item.type] || 'fa-file';
    
    return `
        <a href="${item.url}" class="search-result-item">
            <div class="search-result-icon">
                <i class="fas ${typeIcon}"></i>
            </div>
            <div class="search-result-content">
                <div class="search-result-title">${escapeHtml(item.title)}</div>
                <div class="search-result-meta">
                    <span class="search-result-type">${item.type}</span>
                    ${item.created_at ? `<span>${item.created_at}</span>` : ''}
                </div>
            </div>
        </a>
    `;
}

// Add search styles
$('<style>')
    .prop('type', 'text/css')
    .html(`
        #searchResults {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: var(--bg-secondary);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-xl);
            margin-top: 0.5rem;
            max-height: 400px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        }
        
        .search-result-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            border-bottom: 1px solid var(--border-light);
            transition: all var(--transition-fast);
            text-decoration: none;
            color: var(--text-primary);
        }
        
        .search-result-item:last-child {
            border-bottom: none;
        }
        
        .search-result-item:hover {
            background: rgba(108, 92, 231, 0.1);
            transform: translateX(4px);
        }
        
        .search-result-icon {
            width: 40px;
            height: 40px;
            border-radius: var(--radius-full);
            background: rgba(108, 92, 231, 0.15);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--primary);
        }
        
        .search-result-content {
            flex: 1;
        }
        
        .search-result-title {
            font-weight: 500;
            margin-bottom: 0.25rem;
        }
        
        .search-result-meta {
            font-size: 0.75rem;
            color: var(--text-tertiary);
            display: flex;
            gap: 1rem;
        }
        
        .search-result-type {
            background: var(--bg-tertiary);
            padding: 0.15rem 0.5rem;
            border-radius: var(--radius-full);
            text-transform: uppercase;
        }
        
        .search-empty {
            padding: 2rem;
            text-align: center;
            color: var(--text-tertiary);
        }
    `)
    .appendTo('head');

// ==================== NOTIFICATIONS ====================
function showNotification(message, type = 'info') {
    const id = 'notification-' + Date.now();
    const types = {
        success: { icon: 'fa-check-circle', color: 'var(--success)' },
        error: { icon: 'fa-exclamation-circle', color: 'var(--danger)' },
        warning: { icon: 'fa-exclamation-triangle', color: 'var(--warning)' },
        info: { icon: 'fa-info-circle', color: 'var(--info)' }
    };
    
    const { icon, color } = types[type] || types.info;
    
    const notification = `
        <div id="${id}" class="notification slide-in-left" style="border-left-color: ${color}">
            <i class="fas ${icon}" style="color: ${color}"></i>
            <span>${message}</span>
        </div>
    `;
    
    $('.notification-container').append(notification);
    
    setTimeout(() => {
        $(`#${id}`).fadeOut(300, function() {
            $(this).remove();
        });
    }, 5000);
}

// Add notification styles
$('<style>')
    .prop('type', 'text/css')
    .html(`
        .notification-container {
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 9999;
        }
        
        .notification {
            background: var(--bg-secondary);
            border-left: 4px solid;
            border-radius: var(--radius-md);
            padding: 1rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: var(--shadow-lg);
            display: flex;
            align-items: center;
            gap: 1rem;
            min-width: 300px;
            border: 1px solid var(--border-light);
            animation: slideInRight 0.3s ease;
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `)
    .appendTo('head');

// Add notification container
$('body').append('<div class="notification-container"></div>');

// ==================== LOADING STATES ====================
function showLoading() {
    if (!$('#loading-spinner').length) {
        $('body').append(`
            <div id="loading-spinner" class="scale-in">
                <div class="spinner"></div>
                <p>Loading...</p>
            </div>
        `);
    }
}

function hideLoading() {
    $('#loading-spinner').fadeOut(300, function() {
        $(this).remove();
    });
}

// ==================== INFINITE SCROLL ====================
function initInfiniteScroll(container, url, itemTemplate) {
    let page = 1;
    let loading = false;
    let hasMore = true;
    
    $(window).on('scroll', debounce(function() {
        if (!hasMore || loading) return;
        
        const scrollPosition = $(window).scrollTop() + $(window).height();
        const containerBottom = $(container).offset().top + $(container).height();
        
        if (scrollPosition > containerBottom - 200) {
            loading = true;
            showLoading();
            
            page++;
            
            $.ajax({
                url: url,
                data: { page: page },
                method: 'GET',
                success: function(data) {
                    if (data.items && data.items.length > 0) {
                        data.items.forEach(item => {
                            $(container).append(itemTemplate(item));
                        });
                        hasMore = data.hasMore;
                    } else {
                        hasMore = false;
                    }
                },
                error: function() {
                    hasMore = false;
                },
                complete: function() {
                    loading = false;
                    hideLoading();
                }
            });
        }
    }, 200));
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==================== EXPOSE GLOBALLY ====================
window.showNotification = showNotification;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.formatFileSize = formatFileSize;
window.getFileIcon = getFileIcon;