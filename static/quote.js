// Currency formatter (USD)
const currencyFormatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2
    });
  
    // Large number formatter (e.g., Market Cap, Volume)
    const numberFormatter = new Intl.NumberFormat('en-US', {
    notation: "compact",
    compactDisplay: "short",
    maximumFractionDigits: 2
    });

  
document.getElementById("stock-form").addEventListener("submit", function (e) {
    e.preventDefault();
  
    
    const symbol = document.getElementById("symbol").value;
    const tableBody = document.getElementById("stock-data");
    tableBody.innerHTML = "<tr><td colspan='2'>Loading...</td></tr>";
  
    fetch("/get_stock_data", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ symbol })
    })
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          tableBody.innerHTML = `<tr><td colspan='2'>Error: ${data.error}</td></tr>`;
          return;
        }
  
        const orderedFields = [
            "Symbol",
            "Name",
            "Current Price",
            "Open",
            "Previous Close",
            "Volume",
            "Average Volume",
            "Market Cap",
            "PE Ratio",
            "1Y Target Estimate",
            "52 Week High"
          ];
          
          let rows = "";

          orderedFields.forEach(label => {
            let value = data[label];

            if (value === null || value === undefined) {
                value = "N/A";
              } else {
                // Format based on the field type
                if (["Current Price", "Open", "Previous Close", "1Y Target Estimate", "52 Week High"].includes(label)) {
                  value = currencyFormatter.format(value);
                } else if (["Volume", "Average Volume", "Market Cap"].includes(label)) {
                  value = numberFormatter.format(value);
                } else if (label === "PE Ratio") {
                  value = value.toFixed(1);
                }
              }

            rows += `<tr><td>${label}</td><td>${value !== null ? value : "N/A"}</td></tr>`;
          });
          
        tableBody.innerHTML = rows;
      })
      .catch(error => {
        tableBody.innerHTML = `<tr><td colspan='2'>Error fetching data</td></tr>`;
        console.error("Error:", error);
      });
  });
  