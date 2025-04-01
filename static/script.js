// const symbol = document.getElementById("symbol").textContent;
// const priceElem = document.getElementById("price");

// function fetchPrice() {
//     fetch(`/price/${symbol}`)
//         .then(response => response.json())
//         .then(data => {
//             if (data.price) {
//                 priceElem.textContent = parseFloat(data.price).toFixed(2);
//             } else {
//                 priceElem.textContent = "Error";
//             }
//         })
//         .catch(() => {
//             priceElem.textContent = "Error";
//         });
// }

// fetchPrice();
// setInterval(fetchPrice, 5000);  // update every 5 seconds