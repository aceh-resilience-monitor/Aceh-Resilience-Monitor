const { fetchDataFromAPI, processApiData } = require('./helper');

async function test() {
    const apiData = await fetchDataFromAPI('2026-06-03', 1, 1);
    console.log("Raw API rows count:", apiData.length);
    const processed = processApiData(apiData, '2026-06-03', 1, 1);
    console.log("Processed rows count:", processed.length);
    console.log("Processed rows levels:", processed.map(p => p.level));
}
test();
