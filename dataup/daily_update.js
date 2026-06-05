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

// Generate a unique key for deduplication
const generateKey = (item) => {
    return `${item.tanggal}|${item.name}|${item.daerah}|${item.sumber}`;
};

const processDate = async (dateStr, existingDataMap) => {
    let dailyData = [];
    let hasData = false;
    
    logMessage(`[INFO] Fetching data for ${dateStr}...`);
    
    for (const regencyId of REGENCY_IDS) {
        for (const priceTypeId of PRICE_TYPE_IDS) {
            const apiData = await fetchDataFromAPI(dateStr, regencyId, priceTypeId);
            
            if (apiData && apiData.length > 0) {
                const processed = processApiData(apiData, dateStr, regencyId, priceTypeId);
                dailyData = dailyData.concat(processed);
                hasData = true;
            }
            
            // Delay 500ms between requests
            await delay(500);
        }
    }
    
    return (hasData && dailyData.length > 0) ? dailyData : [];
};

const runDailyUpdate = async () => {
    logMessage('[INFO] Starting daily update process...');
    
    const today = dayjs();
    const todayStr = today.format('YYYY-MM-DD');
    const year = today.format('YYYY');
    
    const filePath = getFilePathForYear(year);
    const existingData = readJsonFile(filePath);
    
    // Tentukan 3 tanggal terakhir untuk dicek secara konstan
    const datesToCheck = [
        today.format('YYYY-MM-DD'),
        today.subtract(1, 'day').format('YYYY-MM-DD'),
        today.subtract(2, 'day').format('YYYY-MM-DD')
    ];
    
    let totalNewEntries = [];
    const datesSuccessfullyScraped = new Set();
    
    for (const dateStr of datesToCheck) {
        const dailyEntries = await processDate(dateStr, null);
        if (dailyEntries.length > 0) {
            logMessage(`[SUCCESS] Fetched ${dailyEntries.length} records for date ${dateStr}`);
            totalNewEntries = totalNewEntries.concat(dailyEntries);
            datesSuccessfullyScraped.add(dateStr);
        }
    }
    
    if (totalNewEntries.length > 0) {
        // OVERWRITE LOGIC: Saring data lama, buang record yang tanggalnya berhasil di-scrape ulang
        const cleanedExistingData = existingData.filter(
            item => !datesSuccessfullyScraped.has(item.tanggal)
        );
        
        const updatedData = cleanedExistingData.concat(totalNewEntries);
        
        // Urutkan data secara kronologis
        updatedData.sort((a, b) => dayjs(a.tanggal).valueOf() - dayjs(b.tanggal).valueOf());
        
        writeJsonFile(filePath, updatedData);
        logMessage(`[SUCCESS] Replaced and added data. Total records now: ${updatedData.length}`);
    } else {
        logMessage(`[INFO] No new data found in 3-day lookback window.`);
    }
    
    logMessage('[INFO] Daily update completed successfully!');
};

// Export for unit testing
module.exports = { generateKey, processDate, runDailyUpdate };

// Only auto-execute when run directly (not when imported by tests)
if (require.main === module) {
    runDailyUpdate().catch(err => {
        logMessage(`[FATAL] Daily update error: ${err.message}`, true);
    });
}
