
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
  
        let rows = "";
        for (const [key, value] of Object.entries(data)) {
          rows += `<tr><td>${key}</td><td>${value !== null ? value : "N/A"}</td></tr>`;
        }
        tableBody.innerHTML = rows;
      })
      .catch(error => {
        tableBody.innerHTML = `<tr><td colspan='2'>Error fetching data</td></tr>`;
        console.error("Error:", error);
      });
  });
  