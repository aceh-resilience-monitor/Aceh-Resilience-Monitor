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

const loadExistingData = (year) => {
    const filePath = getFilePathForYear(year);
    const existingData = readJsonFile(filePath);
    return { filePath, existingData };
};

const fetchDateData = async (dateStr) => {
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
    
    if (!hasData) {
        logMessage(`[SKIP] No data found from API for ${dateStr}`);
    }
    
    return dailyData;
};

const mergeWithoutDuplicate = (existingData, newEntries) => {
    const existingDataMap = new Map();
    for (const item of existingData) {
        existingDataMap.set(generateKey(item), true);
    }
    
    const addedEntries = [];
    let duplicateCount = 0;
    
    for (const item of newEntries) {
        const key = generateKey(item);
        if (!existingDataMap.has(key)) {
            existingDataMap.set(key, true);
            addedEntries.push(item);
        } else {
            duplicateCount++;
        }
    }
    
    return { addedEntries, duplicateCount };
};

const checkLast7Days = async (todayStr) => {
    const allFetchedData = [];
    const today = dayjs(todayStr);
    
    // Loop dari i=0 (hari ini) sampai i=7 (7 hari ke belakang)
    for (let i = 0; i <= 7; i++) {
        const checkDateStr = today.subtract(i, 'day').format('YYYY-MM-DD');
        const isBackfill = i > 0;
        
        const dailyData = await fetchDateData(checkDateStr);
        
        if (dailyData.length > 0) {
            allFetchedData.push({
                date: checkDateStr,
                data: dailyData,
                isBackfill
            });
        }
    }
    
    return allFetchedData;
};

const appendMissingHistoricalData = async (todayStr, currentData) => {
    const fetchedDataList = await checkLast7Days(todayStr);
    
    let totalNewEntriesAdded = 0;
    let totalBackfillAdded = 0;
    
    for (const fetched of fetchedDataList) {
        const { date, data, isBackfill } = fetched;
        
        const { addedEntries, duplicateCount } = mergeWithoutDuplicate(currentData, data);
        
        if (addedEntries.length > 0) {
            // Append new data to current array
            currentData = currentData.concat(addedEntries);
            
            if (isBackfill) {
                totalBackfillAdded += addedEntries.length;
                logMessage(`[SUCCESS] Backfilled ${addedEntries.length} new records for ${date}. (Skipped ${duplicateCount} duplicates)`);
            } else {
                totalNewEntriesAdded += addedEntries.length;
                logMessage(`[SUCCESS] Added ${addedEntries.length} new records for today (${date}). (Skipped ${duplicateCount} duplicates)`);
            }
        } else {
            const typeLog = isBackfill ? "Backfill" : "Today";
            logMessage(`[INFO] Checked ${date} (${typeLog}): 0 new records, ${duplicateCount} duplicates skipped.`);
        }
    }
    
    return {
        updatedData: currentData,
        totalNewEntriesAdded,
        totalBackfillAdded
    };
};

const runDailyUpdate = async () => {
    logMessage('[INFO] Starting daily update process with 7-day backfill check...');
    
    const today = dayjs();
    const todayStr = today.format('YYYY-MM-DD');
    const year = today.format('YYYY');
    
    // 1. Load existing data
    const { filePath, existingData } = loadExistingData(year);
    logMessage(`[INFO] Loaded ${existingData.length} existing records for year ${year}`);
    
    // 2. Fetch and append data (Today + 7 days backfill)
    const { 
        updatedData, 
        totalNewEntriesAdded, 
        totalBackfillAdded 
    } = await appendMissingHistoricalData(todayStr, existingData);
    
    // 3. Save if there are new entries
    const totalAdded = totalNewEntriesAdded + totalBackfillAdded;
    if (totalAdded > 0) {
        // Sort data by date ascending
        updatedData.sort((a, b) => dayjs(a.tanggal).valueOf() - dayjs(b.tanggal).valueOf());
        
        writeJsonFile(filePath, updatedData);
        logMessage(`[SUCCESS] Update complete! Added ${totalNewEntriesAdded} today's records and ${totalBackfillAdded} backfill records. Total records now: ${updatedData.length}`);
    } else {
        logMessage(`[INFO] No new records to add (including backfill). System is up to date.`);
    }
    
    logMessage('[INFO] Daily update completed successfully!');
};

// Only auto-run when executed directly (not when required by tests)
if (require.main === module) {
    runDailyUpdate().catch(err => {
        logMessage(`[FATAL] Daily update error: ${err.message}`, true);
    });
}

module.exports = {
    generateKey,
    loadExistingData,
    fetchDateData,
    mergeWithoutDuplicate,
    checkLast7Days,
    appendMissingHistoricalData,
    runDailyUpdate,
    REGENCY_IDS,
    PRICE_TYPE_IDS
};
