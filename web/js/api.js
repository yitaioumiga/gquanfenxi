class StockAPI {
    static async searchStock(keyword, page = 1, per_page = 10) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 10000);
        
        try {
            const response = await fetch(
                `/api/search?keyword=${encodeURIComponent(keyword)}&page=${page}&per_page=${per_page}`,
                { signal: controller.signal }
            );
            
            clearTimeout(timeout);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('请求超时，请重试');
            }
            throw error;
        }
    }

    static async getStockAnalysis(stockCode, params) {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                stockCode,
                discountRate: params.discountRate,
                growthRate: params.growthRate,
                forecastPeriod: params.forecastPeriod
            })
        });
        return await response.json();
    }
}
