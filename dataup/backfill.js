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

const runBackfill = async () => {
    logMessage('[INFO] Starting backfill process...');

    const startDateStr = '2021-01-01';
    const endDateStr = dayjs().format('YYYY-MM-DD');

    let currentDate = dayjs(startDateStr);
    const endDate = dayjs(endDateStr);

    // Iterate day by day
    while (currentDate.isBefore(endDate) || currentDate.isSame(endDate, 'day')) {
        const dateStr = currentDate.format('YYYY-MM-DD');
        const year = currentDate.format('YYYY');

        logMessage(`[INFO] Processing date: ${dateStr}`);

        let dailyData = [];
        let hasData = false;

        for (const regencyId of REGENCY_IDS) {
            for (const priceTypeId of PRICE_TYPE_IDS) {
                const apiData = await fetchDataFromAPI(dateStr, regencyId, priceTypeId);

                if (apiData && apiData.length > 0) {
                    const processed = processApiData(apiData, dateStr, regencyId, priceTypeId);
                    dailyData = dailyData.concat(processed);
                    hasData = true;
                }

                // Delay 500ms between requests to avoid getting blocked
                await delay(500);
            }
        }

        if (hasData && dailyData.length > 0) {
            const filePath = getFilePathForYear(year);
            const existingData = readJsonFile(filePath);

            // Append data
            const updatedData = existingData.concat(dailyData);

            // Sort data by date
            updatedData.sort((a, b) => dayjs(a.tanggal).valueOf() - dayjs(b.tanggal).valueOf());

            writeJsonFile(filePath, updatedData);
            logMessage(`[SUCCESS] Saved ${dailyData.length} records for ${dateStr} to ${year}.json`);
        } else {
            logMessage(`[SKIP] No data found for ${dateStr}`);
        }

        currentDate = currentDate.add(1, 'day');
    }

    logMessage('[INFO] Backfill completed successfully!');
};

runBackfill().catch(err => {
    logMessage(`[FATAL] Backfill error: ${err.message}`, true);
});
