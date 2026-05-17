const fs = require('fs');
const path = require('path');
const axios = require('axios');
const dayjs = require('dayjs');

const MAPPING_DAERAH = {
    1: 'Banda Aceh',
    2: 'Lhokseumawe',
    3: 'Meulaboh'
};

const MAPPING_SUMBER = {
    1: 'Pasar Tradisional',
    2: 'Pasar Modern',
    3: 'Pedagang Besar',
    4: 'Produsen'
};

// Data folder will be created inside the 'dataup' directory
const DATA_DIR = path.join(__dirname, 'data');
const LOG_FILE = path.join(__dirname, 'process.log');

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
}

// Global logger to write to both console and process.log
const logMessage = (msg, isError = false) => {
    const timestamp = dayjs().format('YYYY-MM-DD HH:mm:ss');
    const logLine = `[${timestamp}] ${msg}`;
    
    if (isError) {
        console.error(logLine);
    } else {
        console.log(logLine);
    }
    
    try {
        fs.appendFileSync(LOG_FILE, logLine + '\n', 'utf8');
    } catch (err) {
        console.error(`Failed to write to log file: ${err.message}`);
    }
};

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const fetchDataFromAPI = async (dateStr, regencyId, priceTypeId, retries = 3) => {
    const url = `https://www.bi.go.id/hargapangan/WebSite/TabelHarga/GetGridDataDaerah`;
    
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const response = await axios.get(url, {
                params: {
                    price_type_id: priceTypeId,
                    comcat_id: '',
                    province_id: 1, // Default to Aceh (1)
                    regency_id: regencyId,
                    market_id: '',
                    tipe_laporan: 1,
                    start_date: dateStr,
                    end_date: dateStr
                },
                timeout: 15000 // 15 seconds timeout
            });
            
            if (response.data && response.data.data) {
                return response.data.data;
            }
            return [];
        } catch (error) {
            const isLastAttempt = attempt === retries;
            if (isLastAttempt) {
                logMessage(`[ERROR] API Request failed for ${dateStr} - Daerah: ${regencyId}, Sumber: ${priceTypeId} after ${retries} attempts. Error: ${error.message}`, true);
                return [];
            } else {
                logMessage(`[WARN] Network error on ${dateStr} (Daerah: ${regencyId}, Sumber: ${priceTypeId}) - ${error.message}. Retrying... (${attempt}/${retries})`);
                await delay(2000); // Wait 2 seconds before retrying
            }
        }
    }
    return [];
};

const processApiData = (apiData, dateStr, regencyId, priceTypeId) => {
    if (!apiData || apiData.length === 0) return [];
    
    const dateObj = dayjs(dateStr);
    const dateKey = dateObj.format('DD/MM/YYYY'); // API uses DD/MM/YYYY for the price field key
    
    const results = [];
    let currentCategory = "";
    
    for (const item of apiData) {
        // Set kategori (komoditas) jika menemukan parent (level 1)
        if (item.level === 1) {
            currentCategory = item.name;
        }

        // Extract price dynamically based on dateKey
        let harga = item[dateKey];
        if (harga === '-' || harga === undefined) {
            harga = null;
        }
        
        // Clean up the dynamic date key so the resulting JSON is standard
        const cleanedItem = { ...item };
        delete cleanedItem[dateKey];

        results.push({
            ...cleanedItem,
            tanggal: dateStr,
            komoditas: currentCategory || item.name, // Assign kategori parent ke anak-anaknya
            harga: harga,
            daerah: MAPPING_DAERAH[regencyId],
            sumber: MAPPING_SUMBER[priceTypeId]
        });
    }
    
    return results;
};

const getFilePathForYear = (year) => {
    return path.join(DATA_DIR, `${year}.json`);
};

const readJsonFile = (filePath) => {
    if (fs.existsSync(filePath)) {
        try {
            const rawData = fs.readFileSync(filePath, 'utf8');
            return JSON.parse(rawData);
        } catch (error) {
            logMessage(`[ERROR] Failed to read ${filePath}: ${error.message}`, true);
            return [];
        }
    }
    return [];
};

const writeJsonFile = (filePath, data) => {
    try {
        fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
    } catch (error) {
        logMessage(`[ERROR] Failed to write ${filePath}: ${error.message}`, true);
    }
};

module.exports = {
    MAPPING_DAERAH,
    MAPPING_SUMBER,
    logMessage,
    delay,
    fetchDataFromAPI,
    processApiData,
    getFilePathForYear,
    readJsonFile,
    writeJsonFile
};
