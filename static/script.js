// Enhanced Stock Watchlist JavaScript

class StockWatchlist {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.notifications = [];
        this.soundEnabled = true;
        this.browserNotificationsEnabled = false;
        this.stocks = new Map();
        this.alerts = new Map();
        
        this.init();
    }

    init() {
        this.connectWebSocket();
        this.requestNotificationPermission();
        this.setupEventListeners();
        this.setupForms();
        this.loadInitialData();
        this.setupAutoRefresh();
    }

    // WebSocket Connection
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = (event) => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus(true);
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.socket.onclose = (event) => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                
                // Attempt to reconnect after 5 seconds
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.connectWebSocket();
                    }
                }, 5000);
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showNotification('Connection Error', 'Failed to connect to real-time updates', 'error');
            };
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.updateConnectionStatus(false);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'stock_update':
                this.updateStockDisplay(data.data);
                break;
            case 'alert_triggered':
                this.handleAlertTriggered(data.data);
                break;
            case 'notification':
                this.showNotification(data.title, data.message, data.type);
                break;
            case 'market_summary':
                this.updateMarketSummary(data.data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = `status-indicator ${connected ? 'connected' : 'disconnected'}`;
            statusElement.innerHTML = `
                <i class="fas fa-${connected ? 'wifi' : 'wifi-slash'}"></i>
                ${connected ? 'Connected' : 'Disconnected'}
            `;
        }
    }

    // Notification System
    async requestNotificationPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            this.browserNotificationsEnabled = permission === 'granted';
        }
    }

    showNotification(title, message, type = 'info') {
        // Browser notification
        if (this.browserNotificationsEnabled && document.hidden) {
            new Notification(title, {
                body: message,
                icon: '/static/favicon.ico',
                tag: 'stock-alert'
            });
        }

        // In-app notification
        this.showInAppNotification(title, message, type);

        // Sound notification
        if (this.soundEnabled && type === 'alert') {
            this.playNotificationSound();
        }
    }

    showInAppNotification(title, message, type = 'info') {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type === 'alert' ? 'alert-notification' : ''}`;
        notification.innerHTML = `
            <div class="notification-header">
                <span class="notification-title">${title}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="notification-body">${message}</div>
        `;

        container.appendChild(notification);
        
        // Animate in
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    playNotificationSound() {
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+LvymEcCD2G0fPTgjMGGoTO8t2MQQoUYrfq7qlUFAlLoe/wrWEbCDp+y/HVhTQGHYfR8tWGNAYceM/z2Zc8BDRF2fDggUMAB0Zj6OysXBIHS5jh8LJoGwk8htDz1YU0Bh2H0fLVhjQGHHjP89mXPAQ0RdnwwIFDAAatUKjY8dOLNQYcf9bv2IoCADtFZOPrsWEaSWTk6bFhGklk5OmuXRUJTKLZ8tWGNAYYitL04Y0zBTBH2O/giTYGF3LN8N+NPwUIX7Tr1IgxBzxp0vHTgzIGJ0vY7tKEMQY3dtby0oODQQU0wnVFYOPrsWEaSWTk6bFhGklk5OmusIxDAAt/y/TWFV1tYO25V3nLYWE7bCZF2PCGNgYXctTw4Y0/BTDQwF/bv2d3DUfQ4rmfMwdV);
            audio.volume = 0.3;
            audio.play().catch(e => console.log('Could not play notification sound:', e));
        } catch (error) {
            console.log('Notification sound not supported:', error);
        }
    }

    // Event Listeners
    setupEventListeners() {
        // Flash message close buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('alert-close')) {
                e.target.closest('.alert').remove();
            }
        });

        // Modal handling
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target);
            }
        });

        // Sound toggle
        const soundToggle = document.getElementById('sound-enabled');
        if (soundToggle) {
            soundToggle.addEventListener('change', (e) => {
                this.soundEnabled = e.target.checked;
                this.updateSoundStatus();
            });
        }

        // Browser notification toggle
        const browserNotificationToggle = document.getElementById('browser-notifications');
        if (browserNotificationToggle) {
            browserNotificationToggle.addEventListener('change', (e) => {
                if (e.target.checked && !this.browserNotificationsEnabled) {
                    this.requestNotificationPermission();
                }
            });
        }
    }

    // Form Setup
    setupForms() {
        // Add stock form
        const addStockForm = document.getElementById('add-stock-form');
        if (addStockForm) {
            addStockForm.addEventListener('submit', (e) => {
                this.handleAddStock(e);
            });
        }

        // Create alert form
        const createAlertForm = document.getElementById('create-alert-form');
        if (createAlertForm) {
            createAlertForm.addEventListener('submit', (e) => {
                this.handleCreateAlert(e);
            });
        }

        // Stock symbol search
        const symbolInput = document.getElementById('symbol');
        if (symbolInput) {
            symbolInput.addEventListener('input', (e) => {
                this.handleSymbolSearch(e);
            });
        }
    }

    async handleAddStock(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const symbol = formData.get('symbol').toUpperCase();

        if (!symbol) {
            this.showNotification('Error', 'Please enter a stock symbol', 'error');
            return;
        }

        try {
            const response = await fetch('/add_stock', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Success', `Added ${symbol} to watchlist`, 'success');
                e.target.reset();
                this.refreshStockTable();
            } else {
                this.showNotification('Error', result.message || 'Failed to add stock', 'error');
            }
        } catch (error) {
            console.error('Error adding stock:', error);
            this.showNotification('Error', 'Failed to add stock', 'error');
        }
    }

    async handleCreateAlert(e) {
        e.preventDefault();
        const formData = new FormData(e.target);

        try {
            const response = await fetch('/create_alert', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Success', 'Alert created successfully', 'success');
                e.target.reset();
                this.refreshAlertsTable();
            } else {
                this.showNotification('Error', result.message || 'Failed to create alert', 'error');
            }
        } catch (error) {
            console.error('Error creating alert:', error);
            this.showNotification('Error', 'Failed to create alert', 'error');
        }
    }

    async handleSymbolSearch(e) {
        const query = e.target.value.trim();
        if (query.length < 2) {
            this.hideSuggestions();
            return;
        }

        try {
            const response = await fetch(`/search_symbols?q=${encodeURIComponent(query)}`);
            const suggestions = await response.json();
            this.showSuggestions(suggestions, e.target);
        } catch (error) {
            console.error('Error searching symbols:', error);
        }
    }

    showSuggestions(suggestions, inputElement) {
        this.hideSuggestions();

        if (!suggestions || suggestions.length === 0) return;

        const container = document.createElement('div');
        container.className = 'search-suggestions';
        container.id = 'symbol-suggestions';

        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.innerHTML = `
                <strong>${suggestion.symbol}</strong> - ${suggestion.name}
                <small style="display: block; color: #666;">${suggestion.exchange}</small>
            `;
            item.addEventListener('click', () => {
                inputElement.value = suggestion.symbol;
                this.hideSuggestions();
            });
            container.appendChild(item);
        });

        inputElement.parentElement.style.position = 'relative';
        inputElement.parentElement.appendChild(container);
    }

    hideSuggestions() {
        const existing = document.getElementById('symbol-suggestions');
        if (existing) {
            existing.remove();
        }
    }

    // Data Updates
    updateStockDisplay(stockData) {
        const row = document.querySelector(`[data-symbol="${stockData.symbol}"]`);
        if (!row) return;

        // Update price
        const priceCell = row.querySelector('.price-cell');
        if (priceCell) {
            priceCell.textContent = `$${stockData.current_price.toFixed(2)}`;
        }

        // Update change
        const changeCell = row.querySelector('.change-cell');
        const changePercentCell = row.querySelector('.change-percent-cell');
        
        if (changeCell && changePercentCell) {
            const change = stockData.price_change;
            const changePercent = stockData.price_change_percent;
            
            changeCell.textContent = `$${change.toFixed(2)}`;
            changePercentCell.textContent = `${changePercent.toFixed(2)}%`;
            
            // Update color classes
            const colorClass = change >= 0 ? 'positive' : 'negative';
            changeCell.className = `change-cell ${colorClass}`;
            changePercentCell.className = `change-percent-cell ${colorClass}`;
        }

        // Update volume
        const volumeCell = row.querySelector('.volume-cell');
        if (volumeCell && stockData.volume) {
            volumeCell.textContent = this.formatLargeNumber(stockData.volume);
        }

        // Update market cap
        const marketCapCell = row.querySelector('.market-cap-cell');
        if (marketCapCell && stockData.market_cap) {
            marketCapCell.textContent = this.formatLargeNumber(stockData.market_cap);
        }

        // Update last updated
        const lastUpdatedCell = row.querySelector('.last-updated-cell');
        if (lastUpdatedCell) {
            lastUpdatedCell.textContent = new Date().toLocaleTimeString();
        }
    }

    handleAlertTriggered(alertData) {
        const { alert, stock_data } = alertData;
        const message = `${alert.symbol}: ${alert.alert_type.replace('_', ' ')} triggered at $${stock_data.current_price.toFixed(2)}`;
        
        this.showNotification('Alert Triggered!', message, 'alert');
        
        // Update alerts table
        this.markAlertAsTriggered(alert.id);
        this.refreshTriggeredAlertsTable();
    }

    markAlertAsTriggered(alertId) {
        const row = document.querySelector(`[data-alert-id="${alertId}"]`);
        if (row) {
            row.classList.add('triggered');
            const statusCell = row.querySelector('.status-cell');
            if (statusCell) {
                statusCell.innerHTML = '<span class="text-warning">Triggered</span>';
            }
        }
    }

    updateMarketSummary(summaryData) {
        // Update summary cards
        Object.entries(summaryData).forEach(([key, value]) => {
            const element = document.getElementById(`summary-${key}`);
            if (element) {
                element.textContent = this.formatSummaryValue(key, value);
            }
        });
    }

    // Data Loading and Refresh
    async loadInitialData() {
        await this.refreshStockTable();
        await this.refreshAlertsTable();
        await this.refreshTriggeredAlertsTable();
        await this.loadMarketSummary();
    }

    async refreshStockTable() {
        try {
            const response = await fetch('/api/stocks');
            const stocks = await response.json();
            this.updateStocksTable(stocks);
        } catch (error) {
            console.error('Error refreshing stocks:', error);
        }
    }

    async refreshAlertsTable() {
        try {
            const response = await fetch('/api/alerts');
            const alerts = await response.json();
            this.updateAlertsTable(alerts);
        } catch (error) {
            console.error('Error refreshing alerts:', error);
        }
    }

    async refreshTriggeredAlertsTable() {
        try {
            const response = await fetch('/api/triggered_alerts');
            const alerts = await response.json();
            this.updateTriggeredAlertsTable(alerts);
        } catch (error) {
            console.error('Error refreshing triggered alerts:', error);
        }
    }

    async loadMarketSummary() {
        try {
            const response = await fetch('/api/market_summary');
            const summary = await response.json();
            this.updateMarketSummary(summary);
        } catch (error) {
            console.error('Error loading market summary:', error);
        }
    }

    updateStocksTable(stocks) {
        const tableBody = document.querySelector('#stocks-table tbody');
        if (!tableBody) return;

        if (stocks.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="empty-state">
                        <i class="fas fa-chart-line"></i>
                        <h3>No stocks in watchlist</h3>
                        <p>Add your first stock to get started</p>
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = stocks.map(stock => `
            <tr class="stock-row" data-symbol="${stock.symbol}">
                <td class="symbol-cell">
                    <strong>${stock.symbol}</strong>
                    <span class="exchange">${stock.exchange || 'N/A'}</span>
                </td>
                <td>${stock.name || 'N/A'}</td>
                <td class="price-cell">$${stock.current_price ? stock.current_price.toFixed(2) : 'N/A'}</td>
                <td class="change-cell ${stock.price_change >= 0 ? 'positive' : 'negative'}">
                    $${stock.price_change ? stock.price_change.toFixed(2) : 'N/A'}
                </td>
                <td class="change-percent-cell ${stock.price_change_percent >= 0 ? 'positive' : 'negative'}">
                    ${stock.price_change_percent ? stock.price_change_percent.toFixed(2) : 'N/A'}%
                </td>
                <td class="volume-cell">${stock.volume ? this.formatLargeNumber(stock.volume) : 'N/A'}</td>
                <td class="market-cap-cell">${stock.market_cap ? this.formatLargeNumber(stock.market_cap) : 'N/A'}</td>
                <td class="actions-cell">
                    <button class="btn btn-sm btn-info" onclick="stockWatchlist.showStockChart('${stock.symbol}')">
                        <i class="fas fa-chart-line"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="stockWatchlist.removeStock('${stock.symbol}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    updateAlertsTable(alerts) {
        const tableBody = document.querySelector('#alerts-table tbody');
        if (!tableBody) return;

        if (alerts.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="empty-state">
                        <i class="fas fa-bell"></i>
                        <h3>No alerts configured</h3>
                        <p>Create your first alert to get notified</p>
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = alerts.map(alert => `
            <tr class="alert-row ${alert.triggered ? 'triggered' : ''}" data-alert-id="${alert.id}">
                <td>${alert.symbol}</td>
                <td>
                    <span class="alert-type-badge alert-type-${alert.alert_type}">
                        ${alert.alert_type.replace('_', ' ')}
                    </span>
                </td>
                <td>$${alert.target_value.toFixed(2)}</td>
                <td class="status-cell">
                    <span class="${alert.triggered ? 'text-warning' : 'text-success'}">
                        ${alert.triggered ? 'Triggered' : 'Active'}
                    </span>
                </td>
                <td>${new Date(alert.created_at).toLocaleDateString()}</td>
                <td class="actions-cell">
                    <button class="btn btn-sm btn-danger" onclick="stockWatchlist.removeAlert(${alert.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    updateTriggeredAlertsTable(alerts) {
        const tableBody = document.querySelector('#triggered-alerts-table tbody');
        if (!tableBody) return;

        if (alerts.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-state">
                        <i class="fas fa-bell-slash"></i>
                        <h3>No triggered alerts</h3>
                        <p>Triggered alerts will appear here</p>
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = alerts.map(alert => `
            <tr class="alert-row">
                <td>${alert.symbol}</td>
                <td>
                    <span class="alert-type-badge alert-type-${alert.alert_type}">
                        ${alert.alert_type.replace('_', ' ')}
                    </span>
                </td>
                <td>$${alert.target_value.toFixed(2)}</td>
                <td>$${alert.triggered_price ? alert.triggered_price.toFixed(2) : 'N/A'}</td>
                <td>${alert.triggered_at ? new Date(alert.triggered_at).toLocaleString() : 'N/A'}</td>
            </tr>
        `).join('');
    }

    // Actions
    async removeStock(symbol) {
        if (!confirm(`Are you sure you want to remove ${symbol} from your watchlist?`)) {
            return;
        }

        try {
            const response = await fetch(`/remove_stock/${symbol}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Success', `Removed ${symbol} from watchlist`, 'success');
                this.refreshStockTable();
            } else {
                this.showNotification('Error', result.message || 'Failed to remove stock', 'error');
            }
        } catch (error) {
            console.error('Error removing stock:', error);
            this.showNotification('Error', 'Failed to remove stock', 'error');
        }
    }

    async removeAlert(alertId) {
        if (!confirm('Are you sure you want to remove this alert?')) {
            return;
        }

        try {
            const response = await fetch(`/remove_alert/${alertId}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Success', 'Alert removed successfully', 'success');
                this.refreshAlertsTable();
            } else {
                this.showNotification('Error', result.message || 'Failed to remove alert', 'error');
            }
        } catch (error) {
            console.error('Error removing alert:', error);
            this.showNotification('Error', 'Failed to remove alert', 'error');
        }
    }

    showStockChart(symbol) {
        // This would typically show a modal with a stock chart
        // For now, we'll show a placeholder
        this.showNotification('Chart', `Chart for ${symbol} would be displayed here`, 'info');
    }

    // Modal Management
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
        }
    }

    closeModal(modal) {
        if (typeof modal === 'string') {
            modal = document.getElementById(modal);
        }
        if (modal) {
            modal.classList.remove('show');
        }
    }

    // Utility Functions
    formatLargeNumber(num) {
        if (num >= 1e12) return (num / 1e12).toFixed(1) + 'T';
        if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
        return num.toString();
    }

    formatSummaryValue(key, value) {
        switch (key) {
            case 'total_value':
            case 'daily_change':
                return `$${value.toFixed(2)}`;
            case 'daily_change_percent':
                return `${value.toFixed(2)}%`;
            default:
                return value.toString();
        }
    }

    updateSoundStatus() {
        const statusElement = document.getElementById('sound-status');
        if (statusElement) {
            statusElement.textContent = this.soundEnabled ? 'Enabled' : 'Disabled';
            statusElement.className = `status-text ${this.soundEnabled ? 'text-success' : 'text-muted'}`;
        }
    }

    setupAutoRefresh() {
        // Refresh data every 30 seconds
        setInterval(() => {
            if (this.isConnected) {
                this.loadMarketSummary();
            } else {
                this.loadInitialData();
            }
        }, 30000);
    }
}

// Initialize the application
let stockWatchlist;

document.addEventListener('DOMContentLoaded', () => {
    stockWatchlist = new StockWatchlist();
    
    // Make it globally available for onclick handlers
    window.stockWatchlist = stockWatchlist;
});

// Handle page visibility changes for notifications
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && stockWatchlist) {
        // Page is now visible, refresh data
        stockWatchlist.loadInitialData();
    }
});
