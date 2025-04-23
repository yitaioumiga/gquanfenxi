document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // 初始化搜索功能
    const searchInput = document.getElementById('stockSearch');
    const searchBtn = document.getElementById('searchBtn');
    
    // 初始化参数监听
    const discountRate = document.getElementById('discountRate');
    const growthRate = document.getElementById('growthRate');
    const forecastPeriod = document.getElementById('forecastPeriod');
    
    // 初始化参数显示值
    updateParamDisplay('discountRate', discountRate.value);
    updateParamDisplay('growthRate', growthRate.value);
    
    // 绑定事件监听器
    searchBtn.addEventListener('click', () => handleSearch(searchInput.value));
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch(searchInput.value);
        }
    });
    
    // 参数变化监听
    discountRate.addEventListener('input', (e) => handleParamChange('discountRate', e.target.value));
    growthRate.addEventListener('input', (e) => handleParamChange('growthRate', e.target.value));
    forecastPeriod.addEventListener('change', (e) => handleParamChange('forecastPeriod', e.target.value));
}

// 搜索处理
let currentPage = 1;
let currentKeyword = '';

async function loadMoreResults() {
    currentPage += 1;
    await handleSearch(currentKeyword, currentPage);
}

async function handleSearch(keyword, page = 1) {
    if (!keyword) {
        showError('请输入搜索关键词');
        return;
    }
    
    currentKeyword = keyword;
    const progressBar = new ProgressBar('searchProgress');
    const searchBtn = document.getElementById('searchBtn');
    const container = document.getElementById('searchResults');
    
    // 如果是第一页，清空容器
    if (page === 1) {
        container.innerHTML = '';
    }
    
    try {
        progressBar.show();
        searchBtn.disabled = true;
        
        const response = await StockAPI.searchStock(keyword, page);
        
        if (response.success) {
            if (response.data && response.data.length > 0) {
                // 显示结果
                if (page === 1) {
                    displaySearchResults(response.data, response.total);
                } else {
                    appendSearchResults(response.data, response.total);
                }
                progressBar.update(100, `找到 ${response.total} 个结果`);
            } else {
                if (page === 1) {
                    container.innerHTML = '<div class="no-results">未找到匹配的股票</div>';
                }
            }
        } else {
            throw new Error(response.message);
        }
    } catch (error) {
        console.error('搜索失败:', error);
        if (page === 1) {
            container.innerHTML = '<div class="search-error">搜索失败，请稍后重试</div>';
        }
    } finally {
        searchBtn.disabled = false;
        setTimeout(() => progressBar.hide(), 1500);
    }
}

function appendSearchResults(results, total) {
    const container = document.getElementById('searchResults');
    
    // 移除旧的加载更多按钮
    const oldLoadMore = container.querySelector('.load-more-btn');
    if (oldLoadMore) {
        oldLoadMore.remove();
    }
    
    // 添加新结果
    results.forEach(stock => {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.innerHTML = `
            <div class="stock-card" data-code="${stock.code}">
                <div class="market-tag ${getMarketClass(stock.market)}">${stock.market}</div>
                <div class="stock-info">
                    <h3>${stock.name} (${stock.code})</h3>
                </div>
                <button class="analyze-btn" onclick="analyzeStock('${stock.code}')">分析</button>
            </div>
        `;
        container.appendChild(item);
    });
    
    // 如果还有更多结果，添加加载更多按钮
    const displayedCount = document.querySelectorAll('.search-result-item').length;
    if (displayedCount < total) {
        const loadMore = document.createElement('button');
        loadMore.className = 'load-more-btn';
        loadMore.textContent = '加载更多';
        loadMore.onclick = loadMoreResults;
        container.appendChild(loadMore);
    }
}

// 参数变化处理
function handleParamChange(paramName, value) {
    updateParamDisplay(paramName, value);
    validateParams();
    recalculate();
}

// 更新参数显示
function updateParamDisplay(paramName, value) {
    const displayElement = document.getElementById(`${paramName}Value`);
    if (displayElement) {
        displayElement.textContent = `${value}%`;
    }
}

// 显示搜索结果
function displaySearchResults(results, total) {
    const container = document.getElementById('searchResults');
    container.innerHTML = '';
    
    // 添加结果统计
    if (total > results.length) {
        const summary = document.createElement('div');
        summary.className = 'search-summary';
        summary.innerHTML = `找到 ${total} 个结果，显示前 ${results.length} 条`;
        container.appendChild(summary);
    }
    
    // 显示结果列表
    results.forEach(stock => {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.innerHTML = `
            <div class="stock-card" data-code="${stock.code}">
                <div class="market-tag ${getMarketClass(stock.market)}">${stock.market}</div>
                <div class="stock-info">
                    <h3>${stock.name} (${stock.code})</h3>
                </div>
                <button class="analyze-btn" onclick="analyzeStock('${stock.code}')">分析</button>
            </div>
        `;
        container.appendChild(item);
    });
    
    // 如果结果超过显示数量，添加加载更多按钮
    if (total > results.length) {
        const loadMore = document.createElement('button');
        loadMore.className = 'load-more-btn';
        loadMore.textContent = '加载更多';
        loadMore.onclick = () => loadMoreResults();
        container.appendChild(loadMore);
    }
}

// 获取市场标签样式
function getMarketClass(market) {
    const marketMap = {
        '上证': 'sh',
        '深证': 'sz',
        '创业板': 'cyb'
    };
    return marketMap[market] || 'other';
}

// 显示错误信息
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 3000);
}

// 分析股票
async function analyzeStock(stockCode) {
    const progressBar = new ProgressBar('searchProgress');
    progressBar.show();
    
    try {
        // 清空之前的结果
        clearResults();
        
        progressBar.update(30, '正在获取数据...');
        const params = {
            discountRate: parseFloat(document.getElementById('discountRate').value) / 100,
            growthRate: parseFloat(document.getElementById('growthRate').value) / 100,
            forecastPeriod: parseInt(document.getElementById('forecastPeriod').value)
        };
        
        const response = await StockAPI.getStockAnalysis(stockCode, params);
        progressBar.update(60, '正在分析...');
        
        if (response.success && response.data) {
            progressBar.update(90, '更新结果...');
            const result = response.data;
            
            // 更新估值结果
            document.getElementById('enterpriseValue').textContent = formatNumber(result.enterprise_value);
            document.getElementById('equityValue').textContent = formatNumber(result.equity_value);
            document.getElementById('perShareValue').textContent = formatNumber(result.per_share_value);
            
            // 更新验证指标
            const validation = result.validation;
            if (validation) {
                document.getElementById('peRatio').textContent = 
                    `${validation.peRatio?.toFixed(2) || '-'}x`;
                document.getElementById('pbRatio').textContent = 
                    `${validation.pbRatio?.toFixed(2) || '-'}x`;
                document.getElementById('evFcfRatio').textContent = 
                    `${validation.evFcfRatio?.toFixed(2) || '-'}x`;
            }
            
            progressBar.update(100, '分析完成');
        } else {
            throw new Error(response.message || '分析失败');
        }
    } catch (error) {
        console.error('分析失败:', error);
        showError(error.message || '分析请求失败，请稍后重试');
        markResultsAsError();
    } finally {
        setTimeout(() => progressBar.hide(), 1500);
    }
}

function clearResults() {
    const elements = ['enterpriseValue', 'equityValue', 'perShareValue', 'peRatio', 'pbRatio', 'evFcfRatio'];
    elements.forEach(id => {
        document.getElementById(id).textContent = '-';
        document.getElementById(id).className = '';
    });
}

function markResultsAsError() {
    const elements = ['enterpriseValue', 'equityValue', 'perShareValue'];
    elements.forEach(id => {
        document.getElementById(id).textContent = '分析失败';
        document.getElementById(id).className = 'error-value';
    });
}

// 格式化数字显示
function formatNumber(value) {
    if (!value && value !== 0) return '-';
    
    try {
        if (Math.abs(value) >= 100000000) {
            return `${(value / 100000000).toFixed(2)}亿`;
        } else if (Math.abs(value) >= 10000) {
            return `${(value / 10000).toFixed(2)}万`;
        } else {
            return value.toFixed(2);
        }
    } catch (e) {
        console.error('数字格式化失败:', e);
        return '-';
    }
}

// 格式化数字
function formatCurrency(number) {
    return new Intl.NumberFormat('zh-CN', {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(number);
}

// 验证参数合理性
function validateParams() {
    const growthRate = parseFloat(document.getElementById('growthRate').value);
    if (growthRate > 5) {
        showWarning('永续增长率过高可能导致不准确的估值结果');
    }
}

// 更新估值结果
function updateResults(results) {
    document.getElementById('enterpriseValue').textContent = formatCurrency(results.enterpriseValue);
    document.getElementById('equityValue').textContent = formatCurrency(results.equityValue);
    document.getElementById('perShareValue').textContent = formatCurrency(results.perShareValue);
    
    // 更新验证指标
    document.getElementById('peRatio').textContent = `${results.validation.peRatio}x`;
    document.getElementById('pbRatio').textContent = `${results.validation.pbRatio}x`;
    document.getElementById('evFcfRatio').textContent = `${results.validation.evFcfRatio}x`;
}
