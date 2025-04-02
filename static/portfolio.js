async function fetchStockData() {
    try {
        const response = await fetch('/api/stock');
        const data = await response.json();
        let tableContent = '';
        for (const symbol in data) {
            const stock = data[symbol];
            tableContent += `
                            <tr>
                                <td>${symbol}</td>
                                <td>${stock.shares}</td>
                                <td>${stock.marketPrice}</td>
                                <td>${new Date (stock.timestamp * 1000).toLocaleTimeString()}</td>
                                <td>${stock.gain}</td>
                                <td>${stock.total}</td>
                            </tr>`

        }
        document.getElementById('stockTable').innerHTML = tableContent;
    } catch (error) {
        console.error("Error fetching stock data:", error);
    }
}

// Poll for new data every 5 seconds.
setInterval(fetchStockData, 5000);
fetchStockData(); // Initial fetch.