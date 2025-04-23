class StockCard {
    static create(stock) {
        return `
            <div class="stock-card" data-code="${stock.code}">
                <div class="market-tag ${stock.market.toLowerCase()}">${stock.market}</div>
                <div class="stock-info">
                    <h3>${stock.name} (${stock.code})</h3>
                    <div class="stock-metrics">
                        <span>市值: ${formatNumber(stock.marketCap)}</span>
                        <span>PE: ${stock.pe?.toFixed(2) || '-'}</span>
                        <span>PB: ${stock.pb?.toFixed(2) || '-'}</span>
                    </div>
                </div>
                <button class="analyze-btn">分析</button>
            </div>
        `;
    }
}

class ProgressBar {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.progress = 0;
    }

    show() {
        this.container.style.display = 'block';
        this.update(0, '准备搜索...');
    }

    hide() {
        this.container.style.display = 'none';
    }

    update(progress, message) {
        this.progress = Math.min(100, progress);
        this.container.innerHTML = `
            <div class="progress-wrapper">
                <div class="progress-bar" style="width: ${this.progress}%"></div>
                <div class="progress-text">${message}</div>
            </div>
        `;
    }
}

class ParamValidator {
    static validateGrowthRate(value) {
        if (value > 5) {
            return {
                valid: false,
                message: '警告：永续增长率超过5%可能不合理'
            };
        }
        return { valid: true };
    }

    static validateDiscountRate(value) {
        if (value < 5) {
            return {
                valid: false,
                message: '警告：折现率过低可能高估企业价值'
            };
        }
        return { valid: true };
    }
}
