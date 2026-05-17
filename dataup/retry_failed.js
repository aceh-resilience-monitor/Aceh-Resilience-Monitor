const fs = require('fs');
const path = require('path');
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

const LOG_FILE = path.join(__dirname, 'process.log');

// Generate a unique key for deduplication so we don't accidentally add the same item twice
const generateKey = (item) => {
    return `${item.tanggal}|${item.komoditas}|${item.daerah}|${item.sumber}`;
};

const runRetryFailed = async () => {
    logMessage('[INFO] Starting to retry failed requests from log...');
    
    if (!fs.existsSync(LOG_FILE)) {
        logMessage('[INFO] No process.log found. Nothing to retry.');
        return;
    }
    
    const logContent = fs.readFileSync(LOG_FILE, 'utf8');
    const lines = logContent.split('\n');
    
    // Extract unique failed requests from log text
    // Matches patterns like: [ERROR] API Request failed for 2021-01-08 - Daerah: 1, Sumber: 3
    const errorRegex = /\[ERROR\] API Request failed for (\d{4}-\d{2}-\d{2}) - Daerah: (\d+), Sumber: (\d+)/;
    
    const failedTasks = [];
    const taskSet = new Set();
    
    for (const line of lines) {
        const match = line.match(errorRegex);
        if (match) {
            const dateStr = match[1];
            const regencyId = parseInt(match[2]);
            const priceTypeId = parseInt(match[3]);
            
            const taskKey = `${dateStr}-${regencyId}-${priceTypeId}`;
            if (!taskSet.has(taskKey)) {
                taskSet.add(taskKey);
                failedTasks.push({ dateStr, regencyId, priceTypeId });
            }
        }
    }
    
    if (failedTasks.length === 0) {
        logMessage('[INFO] No failed requests found in log. Everything is good.');
        return;
    }
    
    logMessage(`[INFO] Found ${failedTasks.length} unique failed requests to retry.`);
    
    // Group tasks by year to avoid constantly reading/writing the same large year JSON file
    const tasksByYear = {};
    for (const task of failedTasks) {
        const year = task.dateStr.substring(0, 4);
        if (!tasksByYear[year]) tasksByYear[year] = [];
        tasksByYear[year].push(task);
    }
    
    for (const year of Object.keys(tasksByYear)) {
        const filePath = getFilePathForYear(year);
        const existingData = readJsonFile(filePath);
        
        // Build map for existing data
        const existingDataMap = new Map();
        for (const item of existingData) {
            existingDataMap.set(generateKey(item), true);
        }
        
        let newEntries = [];
        const tasks = tasksByYear[year];
        
        logMessage(`[INFO] Retrying ${tasks.length} tasks for year ${year}...`);
        
        for (const task of tasks) {
            const { dateStr, regencyId, priceTypeId } = task;
            logMessage(`[INFO] Retrying ${dateStr} - Daerah: ${regencyId}, Sumber: ${priceTypeId}...`);
            
            // Retry the API request
            const apiData = await fetchDataFromAPI(dateStr, regencyId, priceTypeId);
            
            if (apiData && apiData.length > 0) {
                const processed = processApiData(apiData, dateStr, regencyId, priceTypeId);
                
                // Deduplicate and append
                for (const item of processed) {
                    const key = generateKey(item);
                    if (!existingDataMap.has(key)) {
                        existingDataMap.set(key, true);
                        newEntries.push(item);
                    }
                }
            }
            
            // Delay 1 second between retries to be extra safe
            await delay(1000);
        }
        
        if (newEntries.length > 0) {
            const updatedData = existingData.concat(newEntries);
            updatedData.sort((a, b) => dayjs(a.tanggal).valueOf() - dayjs(b.tanggal).valueOf());
            writeJsonFile(filePath, updatedData);
            logMessage(`[SUCCESS] Recovered ${newEntries.length} records for year ${year}.`);
        } else {
            logMessage(`[INFO] No new records recovered for year ${year} (maybe already existed or still failed).`);
        }
    }
    
    logMessage('[INFO] Finished retrying failed requests.');
};

runRetryFailed().catch(err => {
    logMessage(`[FATAL] Retry failed error: ${err.message}`, true);
});
