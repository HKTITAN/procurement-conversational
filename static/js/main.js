/**
 * Main JavaScript for Procurement Platform
 * Handles real-time updates, forms, modals, and API interactions
 */

// Fallback app object if main class fails to initialize
window.app = window.app || {
    apiBase: '/api',
    openModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    },
    closeModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    },
    showToast: function(message, type = 'info') {
        console.log(`${type.toUpperCase()}: ${message}`);
        // Simple fallback toast
        alert(message);
    },
    showLoading: function(show) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            if (show) {
                overlay.classList.remove('hidden');
            } else {
                overlay.classList.add('hidden');
            }
        }
    }
};

class ProcurementApp {
    constructor() {
        this.apiBase = '/api';
        this.refreshInterval = 30000; // 30 seconds
        this.updateTimer = null;
        this.websocket = null;
        this.charts = {};
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeModals();
        this.initializeFAB();
        this.setupRealTimeUpdates();
        this.loadInitialData();
    }
    
    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }
        
        // Alert close buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('alert-close')) {
                e.target.closest('.alert').style.display = 'none';
            }
        });
        
        // Modal close buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-close')) {
                const modal = e.target.closest('.modal');
                this.closeModal(modal.id);
            }
        });
        
        // Form submissions
        document.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmit(e.target);
        });
        
        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('auto-refresh');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }
    }
    
    initializeModals() {
        // Close modal when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });
        
        // ESC key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.modal.active');
                if (activeModal) {
                    this.closeModal(activeModal.id);
                }
            }
        });
    }
    
    initializeFAB() {
        const mainFab = document.getElementById('main-fab');
        const fabMenu = document.getElementById('fab-menu');
        
        if (mainFab && fabMenu) {
            mainFab.addEventListener('click', () => {
                fabMenu.classList.toggle('active');
            });
            
            // Close FAB menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.fab-container')) {
                    fabMenu.classList.remove('active');
                }
            });
        }
    }
    
    setupRealTimeUpdates() {
        // Socket.IO will be initialized in the dashboard template
        // This method is kept for compatibility but actual setup happens in template
        console.log('Real-time updates ready for Socket.IO initialization');
        
        // Fallback to polling if Socket.IO not available
        if (typeof io === 'undefined') {
            console.warn('Socket.IO not available, using polling');
            this.startAutoRefresh();
        }
    }
    
    handleRealtimeUpdate(data) {
        switch (data.type) {
            case 'stats_update':
                this.updateStats(data.payload);
                break;
            case 'new_conversation':
                this.handleNewConversation(data.payload);
                break;
            case 'inventory_update':
                this.updateInventoryStatus(data.payload);
                break;
            case 'alert':
                this.showAlert(data.payload.message, data.payload.type);
                break;
            default:
                console.log('Unknown update type:', data.type);
        }
    }
    
    updateConnectionStatus(isConnected) {
        const indicator = document.getElementById('connection-status');
        const text = document.getElementById('connection-text');
        
        if (indicator) {
            indicator.style.backgroundColor = isConnected ? '#27ae60' : '#f39c12';
        }
        
        if (text) {
            text.textContent = isConnected ? 'Connected' : 'Disconnected';
        }
    }
    
    async loadInitialData() {
        try {
            this.showLoading(true);
            
            // Load companies for form dropdowns
            await this.loadCompaniesForForms();
            
            // Load dashboard data if on dashboard page
            if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
                await this.loadDashboardData();
            }
            
            this.showLoading(false);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showToast('Error loading data', 'error');
            this.showLoading(false);
        }
    }
    
    async loadCompaniesForForms() {
        try {
            const response = await fetch(`${this.apiBase}/companies`);
            const companies = await response.json();
            
            const companySelects = document.querySelectorAll('#company-select');
            companySelects.forEach(select => {
                select.innerHTML = '<option value="">Select Company</option>';
                companies.forEach(company => {
                    const option = document.createElement('option');
                    option.value = company.company_id;
                    option.textContent = company.name;
                    select.appendChild(option);
                });
            });
        } catch (error) {
            console.error('Error loading companies:', error);
        }
    }
    
    async loadDashboardData() {
        try {
            const [statsResponse, alertsResponse] = await Promise.all([
                fetch(`${this.apiBase}/stats`),
                fetch(`${this.apiBase}/alerts`)
            ]);
            
            if (statsResponse.ok) {
                const stats = await statsResponse.json();
                this.updateStats(stats);
            }
            
            if (alertsResponse.ok) {
                const alerts = await alertsResponse.json();
                this.updateAlerts(alerts);
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }
    
    updateStats(stats) {
        // Update stat cards
        const statElements = {
            'total-companies': stats.total_companies,
            'total-vendors': stats.total_vendors,
            'active-conversations': stats.active_conversations,
            'total-savings': `₹${(stats.total_savings || 0).toLocaleString()}`
        };
        
        Object.entries(statElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
        
        // Update charts if they exist
        this.updateCharts(stats);
    }
    
    updateCharts(stats) {
        // Budget utilization chart
        const budgetChartCanvas = document.getElementById('budget-chart');
        if (budgetChartCanvas && stats.budget_utilization) {
            this.renderBudgetChart(budgetChartCanvas, stats.budget_utilization);
        }
        
        // Procurement trends chart
        const trendsChartCanvas = document.getElementById('trends-chart');
        if (trendsChartCanvas && stats.procurement_trends) {
            this.renderTrendsChart(trendsChartCanvas, stats.procurement_trends);
        }
    }
    
    renderBudgetChart(canvas, data) {
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded, skipping chart rendering');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts.budgetChart) {
            this.charts.budgetChart.destroy();
        }
        
        this.charts.budgetChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.company_name),
                datasets: [{
                    data: data.map(d => d.usage_percentage),
                    backgroundColor: [
                        '#3498db',
                        '#27ae60',
                        '#f39c12',
                        '#e74c3c',
                        '#9b59b6'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.parsed}%`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    renderTrendsChart(canvas, data) {
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded, skipping chart rendering');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts.trendsChart) {
            this.charts.trendsChart.destroy();
        }
        
        this.charts.trendsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Procurement Value',
                    data: data.values,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    updateAlerts(alerts) {
        const alertsContainer = document.querySelector('.alerts-section');
        if (!alertsContainer || !alerts.length) return;
        
        alertsContainer.innerHTML = '';
        alerts.forEach(alert => {
            const alertElement = document.createElement('div');
            alertElement.className = `alert alert-${alert.type}`;
            alertElement.innerHTML = `
                <i class="fas fa-${alert.icon}"></i>
                <span>${alert.message}</span>
                <button class="alert-close">&times;</button>
            `;
            alertsContainer.appendChild(alertElement);
        });
    }
    
    handleFormSubmit(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        switch (form.id) {
            case 'call-form':
                this.handleCallForm(data);
                break;
            case 'whatsapp-form':
                this.handleWhatsAppForm(data);
                break;
            default:
                console.log('Unknown form:', form.id);
        }
    }
    
    async handleCallForm(data) {
        try {
            console.log('🔧 DEBUG: Call form handler started');
            console.log('🔧 DEBUG: Form data received:', data);
            
            this.showLoading(true);
            
            // Validate required fields with detailed logging
            const companyId = data['company-select'] || data.companySelect;
            const phoneNumber = data['phone-number'] || data.phoneNumber;
            const priority = data['call-priority'] || data.callPriority || 'normal';
            
            console.log('🔧 DEBUG: Extracted values:', { companyId, phoneNumber, priority });
            
            if (!companyId) {
                console.error('🔧 DEBUG: Missing company ID');
                this.showToast('Please select a company', 'error');
                return;
            }
            
            if (!phoneNumber) {
                console.error('🔧 DEBUG: Missing phone number');
                this.showToast('Please enter a phone number', 'error');
                return;
            }
            
            console.log('🔧 DEBUG: Making API call with:', { companyId, phoneNumber, priority });
            
            const requestBody = {
                company_id: companyId,
                phone_number: phoneNumber,
                priority: priority
            };
            
            console.log('🔧 DEBUG: Request body:', JSON.stringify(requestBody));
            
            const response = await fetch(`${this.apiBase}/calls/initiate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            console.log('🔧 DEBUG: Response status:', response.status);
            console.log('🔧 DEBUG: Response headers:', Object.fromEntries(response.headers.entries()));
            
            const result = await response.json();
            console.log('🔧 DEBUG: API response:', result);
            
            if (response.ok) {
                console.log('🔧 DEBUG: Call successful, showing success message');
                this.showToast('Call initiated successfully!', 'success');
                this.closeModal('call-modal');
                
                // Show call tracking modal
                this.showCallTracking(result.call_sid);
            } else {
                console.error('🔧 DEBUG: Call failed with response:', result);
                this.showToast(result.error || 'Failed to initiate call', 'error');
            }
        } catch (error) {
            console.error('🔧 DEBUG: Exception in handleCallForm:', error);
            console.error('🔧 DEBUG: Error stack:', error.stack);
            this.showToast('Error initiating call: ' + error.message, 'error');
        } finally {
            console.log('🔧 DEBUG: Call form handler completed');
            this.showLoading(false);
        }
    }
    
    async handleWhatsAppForm(data) {
        try {
            console.log('Handling WhatsApp form submission:', data);
            this.showLoading(true);
            
            // Get form field values with multiple possible names
            const phoneNumber = data['whatsapp-phone'] || data.whatsappPhone;
            const message = data['whatsapp-message'] || data.whatsappMessage;
            
            if (!phoneNumber) {
                this.showToast('Please enter a phone number', 'error');
                return;
            }
            
            const response = await fetch(`${this.apiBase}/whatsapp/send`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    phone_number: phoneNumber,
                    message: message || null
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showToast('WhatsApp message sent successfully!', 'success');
                this.closeModal('whatsapp-modal');
            } else {
                this.showToast(result.error || 'Failed to send WhatsApp message', 'error');
            }
        } catch (error) {
            console.error('Error sending WhatsApp:', error);
            this.showToast('Error sending WhatsApp message: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    showCallTracking(callSid) {
        // Create and show call tracking modal
        const modal = document.createElement('div');
        modal.id = 'call-tracking-modal';
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-phone-alt"></i> Call Tracking</h3>
                    <button class="modal-close" onclick="app.closeModal('call-tracking-modal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="call-status">
                        <p><strong>Call SID:</strong> ${callSid}</p>
                        <p><strong>Status:</strong> <span id="call-status">Initiating...</span></p>
                        <div class="progress">
                            <div class="progress-bar" id="call-progress" style="width: 10%"></div>
                        </div>
                        <div id="call-details"></div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="app.closeModal('call-tracking-modal')">Close</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Start polling for call status
        this.pollCallStatus(callSid);
    }
    
    async pollCallStatus(callSid) {
        const statusElement = document.getElementById('call-status');
        const progressElement = document.getElementById('call-progress');
        const detailsElement = document.getElementById('call-details');
        
        const poll = async () => {
            try {
                const response = await fetch(`${this.apiBase}/calls/${callSid}/status`);
                const status = await response.json();
                
                if (statusElement) statusElement.textContent = status.status;
                
                // Update progress
                const progressMap = {
                    'initiated': 20,
                    'ringing': 40,
                    'answered': 60,
                    'in-progress': 80,
                    'completed': 100,
                    'failed': 100,
                    'no-answer': 100,
                    'busy': 100
                };
                
                const progress = progressMap[status.status] || 10;
                if (progressElement) progressElement.style.width = `${progress}%`;
                
                // Show details
                if (detailsElement && status.details) {
                    detailsElement.innerHTML = `
                        <p><strong>Duration:</strong> ${status.duration || 'N/A'}</p>
                        <p><strong>WhatsApp Fallback:</strong> ${status.whatsapp_fallback ? 'Yes' : 'No'}</p>
                    `;
                }
                
                // Continue polling if call is still active
                if (!['completed', 'failed', 'no-answer', 'busy'].includes(status.status)) {
                    setTimeout(poll, 2000);
                }
            } catch (error) {
                console.error('Error polling call status:', error);
                if (statusElement) statusElement.textContent = 'Error';
            }
        };
        
        // Start initial poll
        poll();
    }
    
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
            
            // Remove dynamically created modals
            if (modalId === 'call-tracking-modal') {
                setTimeout(() => {
                    if (modal.parentNode) {
                        modal.parentNode.removeChild(modal);
                    }
                }, 300);
            }
        }
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            if (show) {
                overlay.classList.remove('hidden');
            } else {
                overlay.classList.add('hidden');
            }
        }
    }
    
    showToast(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toast-container') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const iconMap = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        toast.innerHTML = `
            <i class="fas fa-${iconMap[type] || 'info-circle'}"></i>
            <span>${message}</span>
            <button class="toast-close">&times;</button>
        `;
        
        container.appendChild(toast);
        
        // Show with animation
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
        
        // Manual close
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        });
    }
    
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    }
    
    showAlert(message, type = 'info') {
        const alertsContainer = document.getElementById('alerts-container');
        if (!alertsContainer) return;
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        
        const iconMap = {
            success: 'check-circle',
            error: 'exclamation-circle', 
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        alert.innerHTML = `
            <i class="fas fa-${iconMap[type] || 'info-circle'}"></i>
            <span>${message}</span>
            <button class="alert-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        alertsContainer.appendChild(alert);
        
        // Auto-remove after 10 seconds for non-error alerts
        if (type !== 'error') {
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 10000);
        }
    }
    
    async refreshData() {
        try {
            this.showLoading(true);
            
            if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
                await this.loadDashboardData();
            }
            
            this.showToast('Data refreshed successfully', 'success');
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showToast('Error refreshing data', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    startAutoRefresh() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        
        this.updateTimer = setInterval(() => {
            this.refreshData();
        }, this.refreshInterval);
        
        console.log('Auto-refresh started');
    }
    
    stopAutoRefresh() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
        
        console.log('Auto-refresh stopped');
    }
    
    async runProcurementAnalysis() {
        try {
            this.showLoading(true);
            
            const response = await fetch(`${this.apiBase}/procurement/analyze`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showToast('Procurement analysis completed', 'success');
                
                // Redirect to procurement page to see results
                setTimeout(() => {
                    window.location.href = '/procurement';
                }, 1000);
            } else {
                this.showToast(result.error || 'Analysis failed', 'error');
            }
        } catch (error) {
            console.error('Error running analysis:', error);
            this.showToast('Error running analysis', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    handleNewConversation(conversation) {
        // Update conversation counters
        const activeCallsElement = document.getElementById('active-calls');
        if (activeCallsElement) {
            const current = parseInt(activeCallsElement.textContent) || 0;
            activeCallsElement.textContent = current + 1;
        }
        
        // Show notification
        this.showToast(`New conversation started with ${conversation.phone_number}`, 'info');
    }
    
    updateInventoryStatus(update) {
        // Find and update inventory displays
        const companyRows = document.querySelectorAll(`[data-company-id="${update.company_id}"]`);
        companyRows.forEach(row => {
            const statusCell = row.querySelector('.inventory-status');
            if (statusCell) {
                statusCell.innerHTML = `<span class="badge badge-${update.status}">${update.message}</span>`;
            }
        });
        
        // Show alert if critical
        if (update.status === 'critical') {
            this.showAlert(update.message, 'warning');
        }
    }
    
    toggleTheme() {
        document.body.classList.toggle('dark-theme');
        localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
    }
    
    toggleNav() {
        const navMenu = document.getElementById('nav-menu');
        if (navMenu) {
            navMenu.classList.toggle('active');
        }
    }
    
    showHelp() {
        alert('Help documentation coming soon!');
    }
    
    showAbout() {
        alert('Likwid.AI Smart Procurement Platform v1.0');
    }
}

// Global helper functions
function initiateCall() {
    if (typeof app !== 'undefined' && app.openModal) {
        app.openModal('call-modal');
    }
}

function sendWhatsApp() {
    if (typeof app !== 'undefined' && app.openModal) {
        app.openModal('whatsapp-modal');
    }
}

function runAnalysis() {
    if (typeof app !== 'undefined' && app.runProcurementAnalysis) {
        app.runProcurementAnalysis();
    }
}

function makeCall() {
    initiateCall();
}

function sendWhatsAppMessage() {
    sendWhatsApp();
}

function closeModal(modalId) {
    if (typeof app !== 'undefined' && app.closeModal) {
        app.closeModal(modalId);
    }
}

function refreshData() {
    if (typeof app !== 'undefined' && app.refreshData) {
        app.refreshData();
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Create global app instance
        window.app = new ProcurementApp();
        
        // Load saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
        }
        
        console.log('ProcurementApp initialized successfully');
    } catch (error) {
        console.error('Error initializing ProcurementApp:', error);
        
        // Ensure fallback app object is available
        if (!window.app) {
            console.log('Using fallback app object');
        }
    }
});

// Utility functions
function formatCurrency(amount) {
    return '₹' + (amount || 0).toLocaleString('en-IN');
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-IN');
}

function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('en-IN');
}

function getUrgencyColor(urgency) {
    const colors = {
        critical: '#e74c3c',
        urgent: '#f39c12',
        normal: '#27ae60'
    };
    return colors[urgency] || '#95a5a6';
}

function getStatusIcon(status) {
    const icons = {
        active: 'check-circle',
        inactive: 'pause-circle',
        error: 'exclamation-circle',
        pending: 'clock'
    };
    return icons[status] || 'question-circle';
}

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProcurementApp;
} 