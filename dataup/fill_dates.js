const dayjs = require('dayjs');
const { 
    delay, 
    logMessage,
    fetchDataFromAPI, 
    processApiData, 
    getFilePathForYear, 
    readJsonFile, 
    writeJsonFile 
} = require('./helper');

const REGENCY_IDS = [1, 2, 3];
const PRICE_TYPE_IDS = [1, 2, 3, 4];

const datesToFill = ['2026-05-14', '2026-05-15', '2026-06-01', '2026-06-03'];

const runFill = async () => {
    logMessage('[INFO] Starting custom fill process for incomplete dates...');
    const year = '2026';
    const filePath = getFilePathForYear(year);
    const existingData = readJsonFile(filePath);
    
    // Filter out existing data for the target dates to avoid any duplicates
    let cleanData = existingData.filter(item => !datesToFill.includes(item.tanggal));
    logMessage(`[INFO] Retained ${cleanData.length} records after removing incomplete dates.`);
    
    let allNewEntries = [];
    
    for (const dateStr of datesToFill) {
        logMessage(`[INFO] Fetching complete data for ${dateStr}...`);
        let dailyData = [];
        
        for (const regencyId of REGENCY_IDS) {
            for (const priceTypeId of PRICE_TYPE_IDS) {
                const apiData = await fetchDataFromAPI(dateStr, regencyId, priceTypeId);
                
                if (apiData && apiData.length > 0) {
                    const processed = processApiData(apiData, dateStr, regencyId, priceTypeId);
                    dailyData = dailyData.concat(processed);
                }
                
                await delay(500); // 500ms delay
            }
        }
        
        logMessage(`[SUCCESS] Fetched ${dailyData.length} records for ${dateStr}`);
        allNewEntries = allNewEntries.concat(dailyData);
    }
    
    const finalData = cleanData.concat(allNewEntries);
    finalData.sort((a, b) => dayjs(a.tanggal).valueOf() - dayjs(b.tanggal).valueOf());
    
    writeJsonFile(filePath, finalData);
    logMessage(`[SUCCESS] Saved updated 2026.json. Total records now: ${finalData.length}`);
};

runFill().catch(err => {
    logMessage(`[FATAL] Fill error: ${err.message}`, true);
});
