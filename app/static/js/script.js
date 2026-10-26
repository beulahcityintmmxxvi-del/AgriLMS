/* =============================================================
   Agri LMS — Platform JavaScript
   =============================================================
   File    : app/static/js/script.js
   Purpose : Supplementary platform-wide JavaScript utilities.
             Core interactivity is handled inline in base.html.
             This file provides reusable utilities, enhanced
             components, and page-specific helpers that are
             loaded on every page via the static asset pipeline.

   Sections:
       1.  Platform Configuration
       2.  DOM Utilities
       3.  Form Validation Helpers
       4.  Chart.js Preset Factories
       5.  Table Enhancements
       6.  Notification System
       7.  Progress Bar Helpers
       8.  File Handling Utilities
       9.  Date and Time Utilities
       10. Agricultural Domain Helpers
       11. Accessibility Enhancements
       12. Performance Utilities
       13. API Request Helpers
       14. Page-Specific Initializers
       15. Export Utilities
   ============================================================= */

'use strict';

/* =============================================================
   SECTION 1 — PLATFORM CONFIGURATION
   Global constants and configuration for the platform.
   ============================================================= */

const AgriLMS = {

    /* Application metadata */
    name:    'Agri Learning Platform',
    version: '1.0.0',

    /* Color palette matching CSS design tokens */
    colors: {
        green:      '#2d6a4f',
        greenDark:  '#1b4332',
        greenLight: '#52b788',
        greenPale:  '#b7ebc6',
        gold:       '#f59f00',
        goldDark:   '#e67700',
        blue:       '#1976d2',
        blueDark:   '#1565c0',
        orange:     '#f76707',
        red:        '#e03131',
        gray:       '#6c757d',
        white:      '#ffffff',
    },

    /* Chart.js color sets for consistent visualization */
    chartColors: {
        primary: [
            'rgba(45, 106, 79, 0.85)',
            'rgba(25, 118, 210, 0.85)',
            'rgba(245, 159, 0, 0.85)',
            'rgba(247, 103, 7, 0.85)',
            'rgba(224, 49, 49, 0.85)',
            'rgba(112, 72, 232, 0.85)',
            'rgba(32, 201, 151, 0.85)',
        ],
        borders: [
            '#2d6a4f', '#1976d2', '#f59f00',
            '#f76707', '#e03131', '#7048e8', '#20c997',
        ],
    },

    /* API endpoints */
    api: {
        saveNotes:   '/courses/{courseId}/modules/{moduleId}/notes',
        updateTime:  '/courses/{courseId}/modules/{moduleId}/time',
    },
};


/* =============================================================
   SECTION 2 — DOM UTILITIES
   Helper functions for DOM manipulation and querying.
   ============================================================= */

/**
 * Query selector shorthand.
 * @param {string} selector - CSS selector
 * @param {Element} [context=document] - Search context
 * @returns {Element|null}
 */
function $(selector, context) {
    return (context || document).querySelector(selector);
}

/**
 * Query selector all — returns array instead of NodeList.
 * @param {string} selector - CSS selector
 * @param {Element} [context=document] - Search context
 * @returns {Element[]}
 */
function $$(selector, context) {
    return Array.from(
        (context || document).querySelectorAll(selector)
    );
}

/**
 * Create a DOM element with optional attributes and content.
 * @param {string} tag - HTML tag name
 * @param {Object} [attrs={}] - Attribute key-value pairs
 * @param {string} [html=''] - Inner HTML content
 * @returns {Element}
 */
function createElement(tag, attrs, html) {
    const el = document.createElement(tag);
    if (attrs) {
        Object.keys(attrs).forEach(function(key) {
            el.setAttribute(key, attrs[key]);
        });
    }
    if (html) el.innerHTML = html;
    return el;
}

/**
 * Add multiple event listeners to a single element.
 * @param {Element} el - Target element
 * @param {string[]} events - Array of event names
 * @param {Function} handler - Event handler function
 */
function onEvents(el, events, handler) {
    if (!el) return;
    events.forEach(function(event) {
        el.addEventListener(event, handler);
    });
}


/* =============================================================
   SECTION 3 — FORM VALIDATION HELPERS
   Client-side validation utilities for all platform forms.
   ============================================================= */

/**
 * Validate an email address format.
 * @param {string} email - Email address to validate
 * @returns {boolean} True if valid email format
 */
function isValidEmail(email) {
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return pattern.test(email.trim());
}

/**
 * Validate password strength and return a score.
 * @param {string} password - Password to evaluate
 * @returns {Object} {score: 0-4, label: string, color: string}
 */
function evaluatePassword(password) {
    if (!password) {
        return { score: 0, label: 'Enter a password', color: '#dee2e6' };
    }

    let score = 0;
    if (password.length >= 8)  score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^a-zA-Z0-9]/.test(password)) score++;
    score = Math.min(score, 4);

    const levels = [
        { label: 'Very weak',  color: AgriLMS.colors.red    },
        { label: 'Weak',       color: AgriLMS.colors.orange  },
        { label: 'Fair',       color: AgriLMS.colors.gold    },
        { label: 'Good',       color: AgriLMS.colors.green   },
        { label: 'Strong',     color: AgriLMS.colors.green   },
    ];

    return {
        score: score,
        label: levels[score] ? levels[score].label : 'Unknown',
        color: levels[score] ? levels[score].color : '#dee2e6',
    };
}

/**
 * Validate that a file meets size and type requirements.
 * @param {File} file - File object to validate
 * @param {string[]} allowedTypes - Array of allowed extensions
 * @param {number} maxMB - Maximum file size in megabytes
 * @returns {Object} {valid: bool, error: string|null}
 */
function validateFile(file, allowedTypes, maxMB) {
    if (!file) return { valid: true, error: null };

    const ext = file.name.split('.').pop().toLowerCase();
    const maxBytes = (maxMB || 20) * 1024 * 1024;

    if (allowedTypes && allowedTypes.length > 0) {
        if (!allowedTypes.includes(ext)) {
            return {
                valid: false,
                error: 'File type ".' + ext + '" is not allowed. ' +
                    'Allowed: ' + allowedTypes.join(', ')
            };
        }
    }

    if (file.size > maxBytes) {
        return {
            valid: false,
            error: 'File is too large (' +
                formatFileSize(file.size) +
                '). Maximum: ' + maxMB + ' MB'
        };
    }

    return { valid: true, error: null };
}

/**
 * Show a validation error message next to a form field.
 * Creates a .form-error element if one does not exist.
 * @param {Element} field - The input element
 * @param {string} message - Error message to display
 */
function showFieldError(field, message) {
    if (!field) return;

    field.classList.add('is-invalid');
    field.classList.remove('is-valid');

    let errorEl = field.parentNode.querySelector('.form-error');
    if (!errorEl) {
        errorEl = createElement('span', { class: 'form-error' });
        field.parentNode.appendChild(errorEl);
    }
    errorEl.textContent = '❌ ' + message;
}

/**
 * Clear a validation error from a form field.
 * @param {Element} field - The input element
 */
function clearFieldError(field) {
    if (!field) return;
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');

    const errorEl = field.parentNode.querySelector('.form-error');
    if (errorEl) errorEl.remove();
}

/**
 * Clear all validation states from a form.
 * @param {HTMLFormElement} form - The form element
 */
function clearFormErrors(form) {
    if (!form) return;
    $$('.is-invalid, .is-valid', form).forEach(function(el) {
        el.classList.remove('is-invalid', 'is-valid');
    });
    $$('.form-error', form).forEach(function(el) {
        el.remove();
    });
}


/* =============================================================
   SECTION 4 — CHART.JS PRESET FACTORIES
   Factory functions that create pre-configured Chart.js
   instances with the platform's visual style applied.
   ============================================================= */

/**
 * Create a line chart with the platform's green theme.
 * @param {HTMLCanvasElement} canvas - Target canvas element
 * @param {string[]} labels - X-axis labels
 * @param {number[]} data - Data points
 * @param {string} [label='Data'] - Dataset label
 * @returns {Chart} Chart.js instance
 */
function createLineChart(canvas, labels, data, label) {
    if (!canvas || typeof Chart === 'undefined') return null;

    return new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label || 'Data',
                data: data,
                borderColor:     AgriLMS.colors.green,
                backgroundColor: function(context) {
                    const chart = context.chart;
                    const { ctx, chartArea } = chart;
                    if (!chartArea) return 'rgba(45,106,79,0.1)';
                    const gradient = ctx.createLinearGradient(
                        0, chartArea.top, 0, chartArea.bottom
                    );
                    gradient.addColorStop(0,   'rgba(45,106,79,0.3)');
                    gradient.addColorStop(1,   'rgba(45,106,79,0.02)');
                    return gradient;
                },
                borderWidth:         2.5,
                pointBackgroundColor: AgriLMS.colors.green,
                pointBorderColor:     '#ffffff',
                pointBorderWidth:     2,
                pointRadius:          5,
                pointHoverRadius:     7,
                fill:    true,
                tension: 0.4,
            }]
        },
        options: {
            responsive:          true,
            maintainAspectRatio: true,
            interaction: {
                mode:      'index',
                intersect: false,
            },
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        color:     AgriLMS.colors.gray,
                    },
                    grid: { color: 'rgba(0,0,0,0.05)' },
                },
                x: {
                    ticks: {
                        color: AgriLMS.colors.gray,
                        font:  { weight: '600' },
                    },
                    grid: { display: false },
                }
            }
        }
    });
}

/**
 * Create a bar chart with the platform's color palette.
 * @param {HTMLCanvasElement} canvas - Target canvas element
 * @param {string[]} labels - X-axis labels
 * @param {number[]} data - Data values
 * @param {string} [color] - Bar color (defaults to green)
 * @param {string} [label='Data'] - Dataset label
 * @returns {Chart} Chart.js instance
 */
function createBarChart(canvas, labels, data, color, label) {
    if (!canvas || typeof Chart === 'undefined') return null;

    const barColor = color || AgriLMS.colors.green;

    return new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label || 'Data',
                data: data,
                backgroundColor: barColor.replace(')', ', 0.8)').replace('rgb', 'rgba'),
                borderColor:     barColor,
                borderWidth:     2,
                borderRadius:    6,
                borderSkipped:   false,
            }]
        },
        options: {
            responsive:          true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        color:     AgriLMS.colors.gray,
                    },
                    grid: { color: 'rgba(0,0,0,0.05)' },
                },
                x: {
                    ticks: { color: AgriLMS.colors.gray },
                    grid:  { display: false },
                }
            }
        }
    });
}

/**
 * Create a doughnut chart with center text label.
 * @param {HTMLCanvasElement} canvas - Target canvas element
 * @param {string[]} labels - Segment labels
 * @param {number[]} data - Segment values
 * @param {string} centerText - Text to display in center
 * @param {string} centerSub - Sub-text below center text
 * @returns {Chart} Chart.js instance
 */
function createDoughnutChart(canvas, labels, data, centerText, centerSub) {
    if (!canvas || typeof Chart === 'undefined') return null;

    return new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: AgriLMS.chartColors.primary.slice(0, data.length),
                borderColor:     AgriLMS.chartColors.borders.slice(0, data.length),
                borderWidth:     2,
                borderRadius:    4,
                hoverOffset:     6,
            }]
        },
        options: {
            responsive:          true,
            maintainAspectRatio: true,
            cutout:              '68%',
            plugins: {
                legend: {
                    display:  true,
                    position: 'bottom',
                    labels: {
                        padding:        16,
                        usePointStyle:  true,
                        pointStyleWidth: 10,
                    }
                }
            }
        },
        plugins: [{
            id: 'centerText',
            afterDraw: function(chart) {
                if (!centerText) return;
                const { ctx, chartArea } = chart;
                if (!chartArea) return;

                const cx = (chartArea.left + chartArea.right) / 2;
                const cy = (chartArea.top + chartArea.bottom) / 2;

                ctx.save();
                ctx.font         = 'bold 20px Segoe UI, sans-serif';
                ctx.fillStyle    = AgriLMS.colors.greenDark;
                ctx.textAlign    = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(centerText, cx, cy - (centerSub ? 8 : 0));

                if (centerSub) {
                    ctx.font      = '11px Segoe UI, sans-serif';
                    ctx.fillStyle = AgriLMS.colors.gray;
                    ctx.fillText(centerSub, cx, cy + 12);
                }

                ctx.restore();
            }
        }]
    });
}


/* =============================================================
   SECTION 5 — TABLE ENHANCEMENTS
   Enhanced sorting, filtering, and export for data tables.
   ============================================================= */

/**
 * Initialize sortable column headers on a table.
 * Clicking a column header sorts the table by that column.
 * Clicking again reverses the sort order.
 * @param {HTMLTableElement} table - The table to make sortable
 */
function initSortableTable(table) {
    if (!table) return;

    const headers = $$('thead th.sortable', table);

    headers.forEach(function(th, colIndex) {
        th.style.cursor = 'pointer';
        th.setAttribute('role', 'button');
        th.setAttribute('tabindex', '0');

        let ascending = true;

        function sort() {
            const tbody = table.querySelector('tbody');
            if (!tbody) return;

            const rows = Array.from(tbody.querySelectorAll('tr'));

            rows.sort(function(a, b) {
                const aText = (a.cells[colIndex] || {}).textContent || '';
                const bText = (b.cells[colIndex] || {}).textContent || '';

                /* Try numeric sort first */
                const aNum = parseFloat(aText.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bText.replace(/[^0-9.-]/g, ''));

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return ascending ? aNum - bNum : bNum - aNum;
                }

                /* Fall back to string sort */
                return ascending
                    ? aText.localeCompare(bText)
                    : bText.localeCompare(aText);
            });

            /* Clear sort indicators */
            headers.forEach(function(h) {
                h.classList.remove('sort-asc', 'sort-desc');
            });

            /* Apply sort indicator */
            th.classList.add(ascending ? 'sort-asc' : 'sort-desc');
            ascending = !ascending;

            /* Re-append sorted rows */
            rows.forEach(function(row) {
                tbody.appendChild(row);
            });
        }

        th.addEventListener('click', sort);
        th.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                sort();
            }
        });
    });
}

/**
 * Export a table's data as a CSV file download.
 * @param {HTMLTableElement} table - The table to export
 * @param {string} [filename='export.csv'] - Download filename
 */
function exportTableToCSV(table, filename) {
    if (!table) return;

    const rows  = $$('tr', table);
    const lines = rows.map(function(row) {
        return $$('th, td', row).map(function(cell) {
            /* Clean cell text and wrap in quotes */
            const text = cell.textContent.trim()
                .replace(/"/g, '""')
                .replace(/\n/g, ' ');
            return '"' + text + '"';
        }).join(',');
    });

    const csvContent = lines.join('\n');
    const blob       = new Blob([csvContent], { type: 'text/csv' });
    const url        = URL.createObjectURL(blob);
    const link       = createElement('a', {
        href:     url,
        download: filename || 'export.csv',
    });

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}


/* =============================================================
   SECTION 6 — NOTIFICATION SYSTEM
   Enhanced toast notification management.
   ============================================================= */

/**
 * Display a toast notification with optional action button.
 * Extends the base showToast() defined in base.html.
 *
 * @param {string} message - Notification message
 * @param {string} [type='info'] - Type: success|info|warning|danger
 * @param {number} [duration=5000] - Auto-dismiss delay in ms
 * @param {Object} [action] - Optional action button
 * @param {string} action.label - Button text
 * @param {Function} action.onClick - Button click handler
 */
function notify(message, type, duration, action) {
    type     = type     || 'info';
    duration = duration || 5000;

    const icons = {
        success: '✅',
        info:    'ℹ️',
        warning: '⚠️',
        danger:  '❌',
    };

    const container = document.getElementById('flashContainer');
    if (!container) return;

    const toast = createElement('div', {
        class:              'alert alert-' + type + ' flash-message',
        role:               'alert',
        'data-auto-dismiss': String(duration),
    });

    let actionHTML = '';
    if (action && action.label) {
        actionHTML =
            '<button type="button" ' +
            'class="btn btn-sm btn-light" ' +
            'id="toastActionBtn" ' +
            'style="margin-left:0.5rem;flex-shrink:0;">' +
            action.label +
            '</button>';
    }

    toast.innerHTML =
        '<span class="alert-icon" aria-hidden="true">' +
            (icons[type] || 'ℹ️') +
        '</span>' +
        '<div class="alert-content" style="flex:1;">' +
            '<p class="alert-text" style="margin:0;">' +
                message +
            '</p>' +
        '</div>' +
        actionHTML +
        '<button class="alert-close" ' +
                'aria-label="Close" ' +
                'onclick="dismissFlash(this.closest(\'.flash-message\'))">' +
            '✕' +
        '</button>';

    /* Attach action handler if provided */
    if (action && action.onClick) {
        const btn = toast.querySelector('#toastActionBtn');
        if (btn) {
            btn.addEventListener('click', function() {
                action.onClick();
                dismissFlash(toast);
            });
        }
    }

    container.appendChild(toast);

    /* Auto-dismiss */
    setTimeout(function() {
        if (typeof dismissFlash === 'function') {
            dismissFlash(toast);
        }
    }, duration);

    return toast;
}

/**
 * Show a success notification.
 * @param {string} message - Success message
 */
function notifySuccess(message) {
    notify(message, 'success', 5000);
}

/**
 * Show an error notification.
 * @param {string} message - Error message
 */
function notifyError(message) {
    notify(message, 'danger', 8000);
}

/**
 * Show a warning notification.
 * @param {string} message - Warning message
 */
function notifyWarning(message) {
    notify(message, 'warning', 6000);
}


/* =============================================================
   SECTION 7 — PROGRESS BAR HELPERS
   Utilities for animating and updating progress bars.
   ============================================================= */

/**
 * Animate a progress bar to a target percentage value.
 * @param {Element} barEl - The .progress-bar element
 * @param {number} targetPercent - Target width percentage (0-100)
 * @param {number} [duration=800] - Animation duration in ms
 */
function animateProgressBar(barEl, targetPercent, duration) {
    if (!barEl) return;

    duration = duration || 800;
    const clamped = Math.min(Math.max(targetPercent || 0, 0), 100);

    barEl.style.transition = 'width ' + duration + 'ms ease';
    barEl.style.width      = clamped + '%';

    /* Auto-color based on value */
    if (barEl.classList.contains('bar-auto-color')) {
        if (clamped >= 70) {
            barEl.style.background = AgriLMS.colors.green;
        } else if (clamped >= 40) {
            barEl.style.background = AgriLMS.colors.gold;
        } else {
            barEl.style.background = AgriLMS.colors.red;
        }
    }
}

/**
 * Update all progress bars on the page that have
 * a data-value attribute, animating them from 0
 * to their target values with staggered timing.
 */
function animateAllProgressBars() {
    $$('.progress-bar[data-value]').forEach(function(bar, index) {
        const value = parseFloat(bar.dataset.value) || 0;
        bar.style.width = '0%';

        setTimeout(function() {
            animateProgressBar(bar, value);
        }, 100 + (index * 50));
    });
}


/* =============================================================
   SECTION 8 — FILE HANDLING UTILITIES
   Client-side file validation and preview generation.
   ============================================================= */

/**
 * Format a byte count as a human-readable file size string.
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted size string
 */
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k     = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i     = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) +
           ' ' + sizes[i];
}

/**
 * Get the appropriate emoji icon for a file type.
 * @param {string} filename - The filename with extension
 * @returns {string} Emoji icon character
 */
function getFileIcon(filename) {
    if (!filename) return '📁';
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        pdf:  '📄',
        doc:  '📝', docx: '📝',
        ppt:  '📊', pptx: '📊',
        xls:  '📈', xlsx: '📈',
        mp4:  '🎬', webm: '🎬', mkv: '🎬',
        png:  '🖼️', jpg:  '🖼️', jpeg: '🖼️', gif: '🖼️',
        zip:  '📦', rar:  '📦',
        txt:  '📋',
        py:   '🐍',
        csv:  '📊',
    };
    return icons[ext] || '📁';
}

/**
 * Generate an HTML preview card for a selected file.
 * @param {File} file - The File object
 * @returns {string} HTML string for the preview card
 */
function generateFilePreviewHTML(file) {
    const icon    = getFileIcon(file.name);
    const sizeStr = formatFileSize(file.size);

    return (
        '<div class="file-preview">' +
            '<span class="file-preview-icon">' + icon + '</span>' +
            '<div class="file-preview-info">' +
                '<div class="file-preview-name" title="' + file.name + '">' +
                    file.name +
                '</div>' +
                '<div class="file-preview-size">' + sizeStr + '</div>' +
            '</div>' +
            '<button type="button" class="file-preview-remove" ' +
                    'onclick="clearFileInput(this)" ' +
                    'aria-label="Remove file">✕</button>' +
        '</div>'
    );
}


/* =============================================================
   SECTION 9 — DATE AND TIME UTILITIES
   Helper functions for date formatting and calculation.
   ============================================================= */

/**
 * Format a Date object as a human-readable relative string.
 * @param {Date} date - The date to format
 * @returns {string} Relative time string
 * @example
 *   relativeTime(new Date()) → 'Just now'
 *   relativeTime(yesterday)  → '1 day ago'
 */
function relativeTime(date) {
    if (!date) return 'Unknown';

    const now   = new Date();
    const delta = Math.floor((now - date) / 1000); /* seconds */

    if (delta < 60)     return 'Just now';
    if (delta < 3600)   return Math.floor(delta / 60) + ' min ago';
    if (delta < 86400)  return Math.floor(delta / 3600) + ' hr ago';
    if (delta < 604800) return Math.floor(delta / 86400) + ' day' +
                               (Math.floor(delta / 86400) !== 1 ? 's' : '') + ' ago';

    return date.toLocaleDateString('en-GB', {
        day:   '2-digit',
        month: 'short',
        year:  'numeric',
    });
}

/**
 * Format seconds as a MM:SS or HH:MM:SS duration string.
 * @param {number} totalSeconds - Duration in seconds
 * @returns {string} Formatted duration string
 */
function formatDuration(totalSeconds) {
    if (!totalSeconds || totalSeconds < 0) return '0:00';

    const hours   = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (hours > 0) {
        return hours + ':' +
            String(minutes).padStart(2, '0') + ':' +
            String(seconds).padStart(2, '0');
    }
    return minutes + ':' + String(seconds).padStart(2, '0');
}

/**
 * Calculate the number of days between two dates.
 * @param {Date} dateA - Start date
 * @param {Date} dateB - End date (defaults to today)
 * @returns {number} Absolute number of days difference
 */
function daysBetween(dateA, dateB) {
    const a    = new Date(dateA);
    const b    = dateB ? new Date(dateB) : new Date();
    const diff = Math.abs(b - a);
    return Math.floor(diff / (1000 * 60 * 60 * 24));
}


/* =============================================================
   SECTION 10 — AGRICULTURAL DOMAIN HELPERS
   Domain-specific utilities for agricultural content.
   ============================================================= */

/**
 * Map a crop name to its display emoji icon.
 * @param {string} cropName - Name of the crop
 * @returns {string} Emoji icon
 */
function getCropIcon(cropName) {
    if (!cropName) return '🌾';

    const lower = cropName.toLowerCase();
    const icons = {
        'maize':     '🌽', 'corn':       '🌽',
        'cassava':   '🍠', 'yam':        '🍠',
        'rice':      '🌾', 'wheat':      '🌾',
        'sorghum':   '🌾', 'millet':     '🌾',
        'tomato':    '🍅', 'pepper':     '🫑',
        'onion':     '🧅', 'garlic':     '🧄',
        'potato':    '🥔', 'sweet potato':'🍠',
        'banana':    '🍌', 'plantain':   '🍌',
        'mango':     '🥭', 'orange':     '🍊',
        'pineapple': '🍍', 'watermelon': '🍉',
        'cowpea':    '🫘', 'soybean':    '🫘',
        'groundnut': '🥜', 'peanut':     '🥜',
        'cocoa':     '🍫', 'coffee':     '☕',
        'cotton':    '🌸', 'sunflower':  '🌻',
    };

    for (const key in icons) {
        if (lower.includes(key)) return icons[key];
    }
    return '🌾';
}

/**
 * Map a livestock/animal type to its display emoji.
 * @param {string} animalType - Type of animal
 * @returns {string} Emoji icon
 */
function getLivestockIcon(animalType) {
    if (!animalType) return '🐾';

    const lower = animalType.toLowerCase();
    const icons = {
        'cattle': '🐄', 'cow': '🐄', 'bull': '🐄',
        'goat':   '🐐',
        'sheep':  '🐑',
        'pig':    '🐖', 'swine': '🐖',
        'poultry':'🐔', 'chicken': '🐔', 'hen': '🐔',
        'duck':   '🦆',
        'turkey': '🦃',
        'fish':   '🐟', 'tilapia': '🐟', 'catfish': '🐟',
        'rabbit': '🐇',
        'horse':  '🐴', 'donkey': '🐴',
    };

    for (const key in icons) {
        if (lower.includes(key)) return icons[key];
    }
    return '🐾';
}

/**
 * Return a human-readable label for a Nigerian growing season.
 * @param {number} month - Month number (1-12)
 * @returns {Object} {season: string, label: string, icon: string}
 */
function getGrowingSeason(month) {
    /* Nigeria growing seasons */
    if (month >= 3 && month <= 7) {
        return {
            season: 'wet_1',
            label:  'First Rainy Season (Mar–Jul)',
            icon:   '🌧️'
        };
    } else if (month >= 8 && month <= 11) {
        return {
            season: 'wet_2',
            label:  'Second Rainy Season (Aug–Nov)',
            icon:   '🌦️'
        };
    } else {
        return {
            season: 'dry',
            label:  'Dry Season (Nov–Feb)',
            icon:   '☀️'
        };
    }
}


/* =============================================================
   SECTION 11 — ACCESSIBILITY ENHANCEMENTS
   Keyboard navigation and screen reader improvements.
   ============================================================= */

/**
 * Trap keyboard focus inside a modal or dialog element.
 * Ensures Tab and Shift+Tab cycle only within the element.
 * @param {Element} container - The modal or dialog container
 * @returns {Function} Cleanup function to remove the trap
 */
function trapFocus(container) {
    if (!container) return function() {};

    const focusableSelectors = [
        'a[href]',
        'button:not([disabled])',
        'input:not([disabled])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    function getFocusable() {
        return Array.from(container.querySelectorAll(focusableSelectors))
            .filter(function(el) {
                return !el.closest('[hidden]') &&
                       window.getComputedStyle(el).display !== 'none';
            });
    }

    function handler(e) {
        if (e.key !== 'Tab') return;

        const focusable = getFocusable();
        if (!focusable.length) return;

        const first = focusable[0];
        const last  = focusable[focusable.length - 1];

        if (e.shiftKey) {
            if (document.activeElement === first) {
                e.preventDefault();
                last.focus();
            }
        } else {
            if (document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        }
    }

    container.addEventListener('keydown', handler);

    /* Return cleanup function */
    return function() {
        container.removeEventListener('keydown', handler);
    };
}

/**
 * Announce a message to screen readers using an ARIA
 * live region. The message is removed after 3 seconds.
 * @param {string} message - The message to announce
 * @param {string} [politeness='polite'] - 'polite' or 'assertive'
 */
function announceToScreenReader(message, politeness) {
    const live = createElement('div', {
        'aria-live':   politeness || 'polite',
        'aria-atomic': 'true',
        style: 'position:absolute;width:1px;height:1px;' +
               'padding:0;margin:-1px;overflow:hidden;' +
               'clip:rect(0,0,0,0);border:0;',
    });

    live.textContent = message;
    document.body.appendChild(live);

    setTimeout(function() {
        if (live.parentNode) live.parentNode.removeChild(live);
    }, 3000);
}


/* =============================================================
   SECTION 12 — PERFORMANCE UTILITIES
   Optimization helpers for smooth UI interactions.
   ============================================================= */

/**
 * Debounce a function — delays execution until after
 * the specified wait time has passed since the last call.
 * @param {Function} func - Function to debounce
 * @param {number} [wait=300] - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function debounced() {
        const ctx  = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function() {
            func.apply(ctx, args);
        }, wait || 300);
    };
}

/**
 * Throttle a function — limits execution to at most
 * once per specified time interval.
 * @param {Function} func - Function to throttle
 * @param {number} [limit=100] - Minimum interval in ms
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let lastCall = 0;
    return function throttled() {
        const now = Date.now();
        if (now - lastCall >= (limit || 100)) {
            lastCall = now;
            func.apply(this, arguments);
        }
    };
}

/**
 * Use IntersectionObserver to lazily initialize a component
 * only when it enters the viewport.
 * @param {Element} el - Element to observe
 * @param {Function} callback - Initialization function
 * @param {number} [threshold=0.1] - Intersection threshold
 */
function lazyInit(el, callback, threshold) {
    if (!el) return;

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(
            function(entries, obs) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        callback(entry.target);
                        obs.unobserve(entry.target);
                    }
                });
            },
            { threshold: threshold || 0.1 }
        );
        observer.observe(el);
    } else {
        /* Fallback for browsers without IntersectionObserver */
        callback(el);
    }
}


/* =============================================================
   SECTION 13 — API REQUEST HELPERS
   Lightweight fetch wrappers for AJAX interactions.
   ============================================================= */

/**
 * Get the CSRF token from a hidden input on the page.
 * @returns {string} CSRF token value
 */
function getCsrfToken() {
    const input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : '';
}

/**
 * Make a POST request with form data and CSRF token.
 * @param {string} url - Request URL
 * @param {Object} data - Key-value data to send
 * @returns {Promise<Object>} Parsed JSON response
 */
function postData(url, data) {
    const formData = new FormData();

    /* Add CSRF token */
    formData.append('csrf_token', getCsrfToken());

    /* Add provided data */
    if (data) {
        Object.keys(data).forEach(function(key) {
            formData.append(key, data[key]);
        });
    }

    return fetch(url, {
        method:  'POST',
        body:    formData,
    })
    .then(function(response) {
        if (!response.ok) {
            throw new Error('Request failed: ' + response.status);
        }
        return response.json();
    });
}

/**
 * Make a GET request and return parsed JSON.
 * @param {string} url - Request URL
 * @returns {Promise<Object>} Parsed JSON response
 */
function getData(url) {
    return fetch(url, {
        method:  'GET',
        headers: { 'Accept': 'application/json' },
    })
    .then(function(response) {
        if (!response.ok) {
            throw new Error('Request failed: ' + response.status);
        }
        return response.json();
    });
}


/* =============================================================
   SECTION 14 — PAGE-SPECIFIC INITIALIZERS
   Automatic initialization of enhanced features
   based on page content detection.
   ============================================================= */

document.addEventListener('DOMContentLoaded', function() {

    /* ── Animate all progress bars ───────────────────────── */
    animateAllProgressBars();

    /* ── Initialize sortable tables ─────────────────────── */
    $$('table.table-sortable').forEach(function(table) {
        initSortableTable(table);
    });

    /* ── CSV export buttons ───────────────────────────────── */
    $$('[data-export-table]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const tableId = this.dataset.exportTable;
            const table   = document.getElementById(tableId);
            const filename = this.dataset.filename || 'export.csv';
            exportTableToCSV(table, filename);
        });
    });

    /* ── Lazy-load charts ─────────────────────────────────── */
    $$('[data-lazy-chart]').forEach(function(canvas) {
        lazyInit(canvas, function(el) {
            const chartType = el.dataset.lazyChart;
            const labels    = JSON.parse(el.dataset.labels || '[]');
            const data      = JSON.parse(el.dataset.values || '[]');
            const label     = el.dataset.label || 'Data';

            if (chartType === 'line') {
                createLineChart(el, labels, data, label);
            } else if (chartType === 'bar') {
                createBarChart(el, labels, data, null, label);
            }
        });
    });

    /* ── Smooth scroll for all anchor links ──────────────── */
    $$('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            const target = document.querySelector(
                this.getAttribute('href')
            );
            if (!target) return;
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    /* ── Tooltip enhancement for data-tooltip elements ───── */
    $$('[data-tooltip]').forEach(function(el) {
        if (!el.getAttribute('title')) {
            el.setAttribute('title', el.dataset.tooltip);
        }
    });

    /* ── Auto-resize textareas ───────────────────────────── */
    $$('textarea[data-autoresize]').forEach(function(textarea) {
        function resize() {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        }
        textarea.addEventListener('input', resize);
        resize();
    });

    /* ── Back to top button ───────────────────────────────── */
    const backToTop = document.getElementById('backToTop');
    if (backToTop) {
        window.addEventListener('scroll', throttle(function() {
            backToTop.style.display =
                window.scrollY > 400 ? 'flex' : 'none';
        }, 100));

        backToTop.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    /* ── Input group prefix click focuses the input ──────── */
    $$('.input-group-prefix, .input-group-suffix').forEach(function(el) {
        el.addEventListener('click', function() {
            const input = this.parentNode.querySelector(
                'input, textarea, select'
            );
            if (input) input.focus();
        });
    });

});


/* =============================================================
   SECTION 15 — EXPORT UTILITIES
   Make utility functions globally accessible for use
   in inline scripts within page templates.
   ============================================================= */

/* Expose functions to the global window scope */
window.AgriLMS          = AgriLMS;
window.createLineChart  = createLineChart;
window.createBarChart   = createBarChart;
window.createDoughnutChart = createDoughnutChart;
window.formatFileSize   = formatFileSize;
window.formatDuration   = formatDuration;
window.relativeTime     = relativeTime;
window.daysBetween      = daysBetween;
window.getCropIcon      = getCropIcon;
window.getLivestockIcon = getLivestockIcon;
window.getGrowingSeason = getGrowingSeason;
window.isValidEmail     = isValidEmail;
window.evaluatePassword = evaluatePassword;
window.validateFile     = validateFile;
window.showFieldError   = showFieldError;
window.clearFieldError  = clearFieldError;
window.notify           = notify;
window.notifySuccess    = notifySuccess;
window.notifyError      = notifyError;
window.notifyWarning    = notifyWarning;
window.trapFocus        = trapFocus;
window.announceToScreenReader = announceToScreenReader;
window.debounce         = debounce;
window.throttle         = throttle;
window.lazyInit         = lazyInit;
window.postData         = postData;
window.getData          = getData;
window.getCsrfToken     = getCsrfToken;
window.exportTableToCSV = exportTableToCSV;
window.initSortableTable = initSortableTable;
window.animateProgressBar = animateProgressBar;
window.generateFilePreviewHTML = generateFilePreviewHTML;
window.getFileIcon      = getFileIcon;