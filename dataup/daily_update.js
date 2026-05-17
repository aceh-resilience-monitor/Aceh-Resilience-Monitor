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
    return `${item.tanggal}|${item.komoditas}|${item.daerah}|${item.sumber}`;
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
    
    if (hasData && dailyData.length > 0) {
        const newEntries = [];
        
        for (const item of dailyData) {
            const key = generateKey(item);
            if (!existingDataMap.has(key)) {
                // If the item doesn't exist yet, we add it
                existingDataMap.set(key, true);
                newEntries.push(item);
            }
        }
        
        return newEntries;
    } else {
        logMessage(`[SKIP] No data found from API for ${dateStr}`);
        return [];
    }
};

const runDailyUpdate = async () => {
    logMessage('[INFO] Starting daily update process...');
    
    const today = dayjs();
    const todayStr = today.format('YYYY-MM-DD');
    const year = today.format('YYYY');
    
    const filePath = getFilePathForYear(year);
    const existingData = readJsonFile(filePath);
    
    // Create a map for fast deduplication checking
    const existingDataMap = new Map();
    for (const item of existingData) {
        existingDataMap.set(generateKey(item), true);
    }
    
    logMessage(`[INFO] Loaded ${existingData.length} existing records for year ${year}`);
    
    let totalNewEntries = [];

    // 1. Fetch today's data
    const todayNewEntries = await processDate(todayStr, existingDataMap);
    
    // 2. If today is empty, check 7 days back
    if (todayNewEntries.length === 0) {
        logMessage(`[INFO] No new data for today (${todayStr}). Checking 7 days back...`);
        
        for (let i = 1; i <= 7; i++) {
            const pastDateStr = today.subtract(i, 'day').format('YYYY-MM-DD');
            const pastEntries = await processDate(pastDateStr, existingDataMap);
            
            if (pastEntries.length > 0) {
                totalNewEntries = totalNewEntries.concat(pastEntries);
            }
        }
    } else {
        totalNewEntries = totalNewEntries.concat(todayNewEntries);
    }
    
    // 3. Save if there are new entries
    if (totalNewEntries.length > 0) {
        const updatedData = existingData.concat(totalNewEntries);
        
        // Sort data by date
        updatedData.sort((a, b) => dayjs(a.tanggal).valueOf() - dayjs(b.tanggal).valueOf());
        
        writeJsonFile(filePath, updatedData);
        logMessage(`[SUCCESS] Added ${totalNewEntries.length} new records. Total records now: ${updatedData.length}`);
    } else {
        logMessage(`[INFO] No new records to add. System is up to date.`);
    }
    
    logMessage('[INFO] Daily update completed successfully!');
};

runDailyUpdate().catch(err => {
    logMessage(`[FATAL] Daily update error: ${err.message}`, true);
});
