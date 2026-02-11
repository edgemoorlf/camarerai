/**
 * Performance Monitor - Frontend
 * Tracks and displays response time metrics for ASR, LLM, and TTS
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = [];
        this.currentRequest = {};
        this.maxHistory = 50;
        this.isVisible = false;

        this.initUI();
    }

    initUI() {
        // Create performance panel
        const panel = document.createElement('div');
        panel.id = 'performance-panel';
        panel.className = 'performance-panel hidden';
        panel.innerHTML = `
            <div class="perf-header">
                <h3>⚡ Performance</h3>
                <button id="perf-close" class="perf-close">×</button>
            </div>
            <div class="perf-content">
                <div class="perf-section">
                    <h4>Current Request</h4>
                    <div id="perf-current" class="perf-metrics">
                        <div class="perf-metric">
                            <span class="perf-label">ASR:</span>
                            <span id="perf-asr" class="perf-value">-</span>
                        </div>
                        <div class="perf-metric">
                            <span class="perf-label">LLM First Token:</span>
                            <span id="perf-llm-first" class="perf-value">-</span>
                        </div>
                        <div class="perf-metric">
                            <span class="perf-label">TTS First Audio:</span>
                            <span id="perf-tts-first" class="perf-value">-</span>
                        </div>
                        <div class="perf-metric perf-total">
                            <span class="perf-label">Total:</span>
                            <span id="perf-total" class="perf-value">-</span>
                        </div>
                    </div>
                </div>
                <div class="perf-section">
                    <h4>Statistics (Last ${this.maxHistory} requests)</h4>
                    <div id="perf-stats" class="perf-stats">
                        <div class="perf-stat-row">
                            <span class="perf-stat-label">Avg Total:</span>
                            <span id="perf-stat-avg" class="perf-stat-value">-</span>
                        </div>
                        <div class="perf-stat-row">
                            <span class="perf-stat-label">Min:</span>
                            <span id="perf-stat-min" class="perf-stat-value">-</span>
                        </div>
                        <div class="perf-stat-row">
                            <span class="perf-stat-label">Max:</span>
                            <span id="perf-stat-max" class="perf-stat-value">-</span>
                        </div>
                        <div class="perf-stat-row">
                            <span class="perf-stat-label">Requests:</span>
                            <span id="perf-stat-count" class="perf-stat-value">0</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(panel);

        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'perf-toggle';
        toggleBtn.className = 'perf-toggle-btn';
        toggleBtn.innerHTML = '⚡';
        toggleBtn.title = 'Show Performance Metrics';
        document.body.appendChild(toggleBtn);

        // Event listeners
        toggleBtn.addEventListener('click', () => this.toggle());
        document.getElementById('perf-close').addEventListener('click', () => this.hide());
    }

    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }

    show() {
        document.getElementById('performance-panel').classList.remove('hidden');
        this.isVisible = true;
    }

    hide() {
        document.getElementById('performance-panel').classList.add('hidden');
        this.isVisible = false;
    }

    updateCurrent(metrics) {
        if (!metrics || !metrics.current) return;

        const current = metrics.current;

        // Update current metrics
        this.updateMetric('perf-asr', current.asr);
        this.updateMetric('perf-llm-first', current.llm_first_token);
        this.updateMetric('perf-tts-first', current.tts_first_audio);
        this.updateMetric('perf-total', current.total, true);

        // Update statistics
        if (metrics.statistics && metrics.statistics.total_response_time) {
            const stats = metrics.statistics.total_response_time;
            document.getElementById('perf-stat-avg').textContent = this.formatMs(stats.avg);
            document.getElementById('perf-stat-min').textContent = this.formatMs(stats.min);
            document.getElementById('perf-stat-max').textContent = this.formatMs(stats.max);
        }

        if (metrics.request_count !== undefined) {
            document.getElementById('perf-stat-count').textContent = metrics.request_count;
        }
    }

    updateMetric(elementId, value, isTotal = false) {
        const element = document.getElementById(elementId);
        if (!element) return;

        if (value === null || value === undefined) {
            element.textContent = '-';
            element.className = 'perf-value';
            return;
        }

        element.textContent = this.formatMs(value);

        // Color code based on performance
        if (isTotal) {
            if (value < 2000) {
                element.className = 'perf-value perf-excellent';
            } else if (value < 3000) {
                element.className = 'perf-value perf-good';
            } else {
                element.className = 'perf-value perf-slow';
            }
        } else {
            if (value < 1000) {
                element.className = 'perf-value perf-excellent';
            } else if (value < 2000) {
                element.className = 'perf-value perf-good';
            } else {
                element.className = 'perf-value perf-slow';
            }
        }
    }

    formatMs(ms) {
        if (ms === null || ms === undefined) return '-';
        return `${Math.round(ms)}ms`;
    }

    recordMetrics(metrics) {
        this.metrics.push(metrics);
        if (this.metrics.length > this.maxHistory) {
            this.metrics.shift();
        }
    }
}

// Make available globally
window.PerformanceMonitor = PerformanceMonitor;
