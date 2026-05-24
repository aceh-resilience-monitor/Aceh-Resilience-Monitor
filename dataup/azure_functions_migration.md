# Migrasi Script ke Azure Functions

Untuk menjalankan script ini di Azure Functions, Anda perlu mengubah cara script membaca dan menyimpan file (menggunakan Azure Blob Storage) dan cara script dieksekusi (menggunakan *Trigger Context* dari Azure).

Berikut adalah draf atau contoh *code* yang sudah disesuaikan untuk Azure. Anda bisa menyimpan struktur ini nanti saat membuat project Azure Functions baru.

### 1. Install Dependencies Baru
Anda perlu menginstal modul resmi dari Azure untuk Blob Storage. Jalankan perintah ini di terminal project Azure Functions Anda nantinya:
```bash
npm install @azure/storage-blob axios dayjs
```

### 2. Update `helper.js`
Di file ini kita mengganti modul `fs` bawaan Node.js dengan `BlobServiceClient`. Semua fungsi *log* juga disesuaikan untuk menerima `context` dari Azure.

```javascript
const { BlobServiceClient } = require('@azure/storage-blob');
const axios = require('axios');
const dayjs = require('dayjs');

const MAPPING_DAERAH = { 1: 'Banda Aceh', 2: 'Lhokseumawe', 3: 'Meulaboh' };
const MAPPING_SUMBER = { 1: 'Pasar Tradisional', 2: 'Pasar Modern', 3: 'Pedagang Besar', 4: 'Produsen' };

// Mengambil Connection String dari Environment Variables Azure
const AZURE_STORAGE_CONNECTION_STRING = process.env.AZURE_STORAGE_CONNECTION_STRING;
const CONTAINER_NAME = process.env.CONTAINER_NAME || "arm-data";

const blobServiceClient = BlobServiceClient.fromConnectionString(AZURE_STORAGE_CONNECTION_STRING);
const containerClient = blobServiceClient.getContainerClient(CONTAINER_NAME);

// Fungsi log disesuaikan untuk memakai context.log dari Azure
const logMessage = (context, msg, isError = false) => {
    const timestamp = dayjs().format('YYYY-MM-DD HH:mm:ss');
    const logLine = `[${timestamp}] ${msg}`;
    
    if (context && context.log) {
        if (isError) context.log.error(logLine);
        else context.log(logLine);
    } else {
        if (isError) console.error(logLine);
        else console.log(logLine);
    }
};

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const fetchDataFromAPI = async (context, dateStr, regencyId, priceTypeId, retries = 3) => {
    const url = `https://www.bi.go.id/hargapangan/WebSite/TabelHarga/GetGridDataDaerah`;
    
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const response = await axios.get(url, {
                params: {
                    price_type_id: priceTypeId, comcat_id: '', province_id: 1, 
                    regency_id: regencyId, market_id: '', tipe_laporan: 1, 
                    start_date: dateStr, end_date: dateStr
                },
                timeout: 15000
            });
            
            if (response.data && response.data.data) return response.data.data;
            return [];
        } catch (error) {
            if (attempt === retries) {
                logMessage(context, `[ERROR] API Request failed for ${dateStr}. Error: ${error.message}`, true);
                return [];
            }
            await delay(2000);
        }
    }
    return [];
};

const processApiData = (apiData, dateStr, regencyId, priceTypeId) => {
    if (!apiData || apiData.length === 0) return [];
    const dateObj = dayjs(dateStr);
    const dateKey = dateObj.format('DD/MM/YYYY');
    
    const results = [];
    let currentCategory = "";
    
    for (const item of apiData) {
        if (item.level === 1) currentCategory = item.name;

        let harga = item[dateKey];
        if (harga === '-' || harga === undefined) harga = null;
        
        const cleanedItem = { ...item };
        delete cleanedItem[dateKey];

        results.push({
            ...cleanedItem,
            tanggal: dateStr,
            komoditas: currentCategory || item.name,
            harga: harga,
            daerah: MAPPING_DAERAH[regencyId],
            sumber: MAPPING_SUMBER[priceTypeId]
        });
    }
    return results;
};

// HELPER: Convert Readable Stream to String untuk baca dari Blob
async function streamToString(readableStream) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    readableStream.on("data", (data) => chunks.push(data.toString()));
    readableStream.on("end", () => resolve(chunks.join("")));
    readableStream.on("error", reject);
  });
}

// BACA DATA DARI AZURE BLOB STORAGE
const readJsonFromBlob = async (context, fileName) => {
    try {
        const blockBlobClient = containerClient.getBlockBlobClient(fileName);
        const exists = await blockBlobClient.exists();
        if (!exists) return [];

        const downloadResponse = await blockBlobClient.download(0);
        const downloadedContent = await streamToString(downloadResponse.readableStreamBody);
        return JSON.parse(downloadedContent);
    } catch (error) {
        logMessage(context, `[ERROR] Failed to read ${fileName} from Blob: ${error.message}`, true);
        return [];
    }
};

// TULIS DATA KE AZURE BLOB STORAGE
const writeJsonToBlob = async (context, fileName, data) => {
    try {
        // Otomatis membuat container jika belum ada
        await containerClient.createIfNotExists();
        
        const blockBlobClient = containerClient.getBlockBlobClient(fileName);
        const jsonString = JSON.stringify(data, null, 2);
        
        await blockBlobClient.upload(jsonString, jsonString.length);
        logMessage(context, `[INFO] Successfully uploaded ${fileName} to Blob Storage.`);
    } catch (error) {
        logMessage(context, `[ERROR] Failed to write ${fileName} to Blob: ${error.message}`, true);
    }
};

module.exports = {
    REGENCY_IDS: [1, 2, 3],
    PRICE_TYPE_IDS: [1, 2, 3, 4],
    logMessage, delay, fetchDataFromAPI, processApiData,
    readJsonFromBlob, writeJsonToBlob
};
```

### 3. Setup Timer Trigger (Pengganti `daily_update.js`)
Di Azure Functions, script ini biasa disimpan di dalam folder bernama fungsi Anda (misal `DailyUpdateTimer`) pada file bernama `index.js`. 
Fungsi ini akan menerima parameter `context` yang wajib diteruskan (pass down) ke fungsi-fungsi lainnya untuk kebutuhan logging.

```javascript
const dayjs = require('dayjs');
const { 
    REGENCY_IDS, PRICE_TYPE_IDS, delay, logMessage,
    fetchDataFromAPI, processApiData, readJsonFromBlob, writeJsonToBlob 
} = require('./helper'); // Pastikan path helper sudah benar

// Format wajib untuk Azure Function
module.exports = async function (context, myTimer) {
    logMessage(context, '[INFO] Timer trigger function executed.');
    
    if (myTimer.isPastDue) {
        logMessage(context, '[WARN] Timer is running late!');
    }

    try {
        await runDailyUpdate(context);
    } catch (error) {
        logMessage(context, `[FATAL] Function failed: ${error.message}`, true);
    }
};

const generateKey = (item) => `${item.tanggal}|${item.komoditas}|${item.daerah}|${item.sumber}`;

const fetchDateData = async (context, dateStr) => {
    let dailyData = [];
    let hasData = false;
    
    logMessage(context, `[INFO] Fetching data for ${dateStr}...`);
    for (const regencyId of REGENCY_IDS) {
        for (const priceTypeId of PRICE_TYPE_IDS) {
            const apiData = await fetchDataFromAPI(context, dateStr, regencyId, priceTypeId);
            if (apiData && apiData.length > 0) {
                const processed = processApiData(apiData, dateStr, regencyId, priceTypeId);
                dailyData = dailyData.concat(processed);
                hasData = true;
            }
            await delay(500);
        }
    }
    
    if (!hasData) logMessage(context, `[SKIP] No data found from API for ${dateStr}`);
    return dailyData;
};

const mergeWithoutDuplicate = (existingData, newEntries) => {
    const existingDataMap = new Map();
    for (const item of existingData) existingDataMap.set(generateKey(item), true);
    
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

const runDailyUpdate = async (context) => {
    logMessage(context, '[INFO] Starting daily update process...');
    
    const today = dayjs();
    const todayStr = today.format('YYYY-MM-DD');
    const year = today.format('YYYY');
    const fileName = `${year}.json`;
    
    // Load from Blob
    let currentData = await readJsonFromBlob(context, fileName);
    logMessage(context, `[INFO] Loaded ${currentData.length} existing records from Blob`);
    
    let totalNewEntriesAdded = 0;
    let totalBackfillAdded = 0;
    
    // 7 Days Check Loop
    for (let i = 0; i <= 7; i++) {
        const checkDateStr = today.subtract(i, 'day').format('YYYY-MM-DD');
        const isBackfill = i > 0;
        
        const dailyData = await fetchDateData(context, checkDateStr);
        if (dailyData.length > 0) {
            const { addedEntries, duplicateCount } = mergeWithoutDuplicate(currentData, dailyData);
            
            if (addedEntries.length > 0) {
                currentData = currentData.concat(addedEntries);
                if (isBackfill) {
                    totalBackfillAdded += addedEntries.length;
                    logMessage(context, `[SUCCESS] Backfilled ${addedEntries.length} new records for ${checkDateStr}. (Skipped ${duplicateCount} duplicates)`);
                } else {
                    totalNewEntriesAdded += addedEntries.length;
                    logMessage(context, `[SUCCESS] Added ${addedEntries.length} new records for today (${checkDateStr}). (Skipped ${duplicateCount} duplicates)`);
                }
            } else {
                const typeLog = isBackfill ? "Backfill" : "Today";
                logMessage(context, `[INFO] Checked ${checkDateStr} (${typeLog}): 0 new records, ${duplicateCount} duplicates skipped.`);
            }
        }
    }
    
    // Save back to Blob if updated
    const totalAdded = totalNewEntriesAdded + totalBackfillAdded;
    if (totalAdded > 0) {
        currentData.sort((a, b) => dayjs(a.tanggal).valueOf() - dayjs(b.tanggal).valueOf());
        await writeJsonToBlob(context, fileName, currentData);
        logMessage(context, `[SUCCESS] Update complete! Added ${totalNewEntriesAdded} today's records and ${totalBackfillAdded} backfill records.`);
    } else {
        logMessage(context, `[INFO] System is up to date.`);
    }
};
```

### 4. Hal yang perlu diperhatikan
1. Di project Azure Functions, Anda perlu menambahkan variabel `AZURE_STORAGE_CONNECTION_STRING` dan `CONTAINER_NAME` (contoh: `arm-data`) di file **`local.settings.json`** saat tes lokal, dan di **Application Settings** jika sudah di-deploy ke portal Azure.
2. Semua eksekusi `logMessage` sekarang mewajibkan pengiriman variabel `context` dari Azure. Hal ini wajib agar log otomatis masuk ke *App Insights*.
