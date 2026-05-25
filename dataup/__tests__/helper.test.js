/**
 * Unit Tests for helper.js — Core Utilities Module
 * 
 * Tests cover:
 * 1. MAPPING_DAERAH & MAPPING_SUMBER (configuration integrity)
 * 2. processApiData() — the critical data transformation function
 * 3. getFilePathForYear() — file path generation
 * 4. readJsonFile() & writeJsonFile() — file I/O with error handling
 * 5. logMessage() — dual-output logger
 * 6. fetchDataFromAPI() — API calls with retry mechanism (mocked)
 * 7. delay() — async delay utility
 */

const fs = require('fs');
const path = require('path');

// Mock axios before requiring helper to prevent real HTTP calls
jest.mock('axios');
const axios = require('axios');

const {
    MAPPING_DAERAH,
    MAPPING_SUMBER,
    logMessage,
    delay,
    fetchDataFromAPI,
    processApiData,
    getFilePathForYear,
    readJsonFile,
    writeJsonFile
} = require('../helper');

// ============================================================
// Test Setup & Teardown
// ============================================================
const TEST_DATA_DIR = path.join(__dirname, '..', 'data');
const TEST_FILE = path.join(TEST_DATA_DIR, '__test_temp__.json');
const LOG_FILE = path.join(__dirname, '..', 'process.log');

afterEach(() => {
    // Clean up test files
    if (fs.existsSync(TEST_FILE)) {
        fs.unlinkSync(TEST_FILE);
    }
    jest.restoreAllMocks();
});

// ============================================================
// 1. Configuration Mapping Tests
// ============================================================
describe('MAPPING_DAERAH — Region ID to Name Mapping', () => {
    test('should map ID 1 to Banda Aceh', () => {
        expect(MAPPING_DAERAH[1]).toBe('Banda Aceh');
    });

    test('should map ID 2 to Lhokseumawe', () => {
        expect(MAPPING_DAERAH[2]).toBe('Lhokseumawe');
    });

    test('should map ID 3 to Meulaboh', () => {
        expect(MAPPING_DAERAH[3]).toBe('Meulaboh');
    });

    test('should contain exactly 3 regions (Aceh province)', () => {
        expect(Object.keys(MAPPING_DAERAH)).toHaveLength(3);
    });

    test('should return undefined for invalid region ID', () => {
        expect(MAPPING_DAERAH[99]).toBeUndefined();
    });
});

describe('MAPPING_SUMBER — Price Source Mapping', () => {
    test('should map ID 1 to Pasar Tradisional', () => {
        expect(MAPPING_SUMBER[1]).toBe('Pasar Tradisional');
    });

    test('should map ID 2 to Pasar Modern', () => {
        expect(MAPPING_SUMBER[2]).toBe('Pasar Modern');
    });

    test('should map ID 3 to Pedagang Besar', () => {
        expect(MAPPING_SUMBER[3]).toBe('Pedagang Besar');
    });

    test('should map ID 4 to Produsen', () => {
        expect(MAPPING_SUMBER[4]).toBe('Produsen');
    });

    test('should contain exactly 4 price sources', () => {
        expect(Object.keys(MAPPING_SUMBER)).toHaveLength(4);
    });
});

// ============================================================
// 2. processApiData() — Critical Data Transformation
// ============================================================
describe('processApiData — API JSON to Flat Tabular Transformation', () => {
    // Simulated API response structure from Bank Indonesia PIHPS
    const mockApiResponse = [
        {
            no: 'I',
            name: 'Beras',
            level: 1,
            '23/05/2026': '12,500'
        },
        {
            no: '1',
            name: 'Beras Kualitas Bawah I',
            level: 2,
            '23/05/2026': '11,000'
        },
        {
            no: '2',
            name: 'Beras Kualitas Bawah II',
            level: 2,
            '23/05/2026': '10,500'
        }
    ];

    test('should transform API data to flat tabular form with correct fields', () => {
        const result = processApiData(mockApiResponse, '2026-05-23', 1, 1);

        expect(result).toHaveLength(3);
        // Check that every item has the required tabular fields
        result.forEach(item => {
            expect(item).toHaveProperty('tanggal', '2026-05-23');
            expect(item).toHaveProperty('komoditas');
            expect(item).toHaveProperty('harga');
            expect(item).toHaveProperty('daerah', 'Banda Aceh');
            expect(item).toHaveProperty('sumber', 'Pasar Tradisional');
        });
    });

    test('should assign parent category (level 1) name to child items (level 2)', () => {
        const result = processApiData(mockApiResponse, '2026-05-23', 1, 1);

        // Parent item (level 1) — komoditas = own name
        expect(result[0].komoditas).toBe('Beras');
        // Child items (level 2) — komoditas = parent's name
        expect(result[1].komoditas).toBe('Beras');
        expect(result[2].komoditas).toBe('Beras');
    });

    test('should extract price from dynamic date key (DD/MM/YYYY format)', () => {
        const result = processApiData(mockApiResponse, '2026-05-23', 1, 1);

        expect(result[0].harga).toBe('12,500');
        expect(result[1].harga).toBe('11,000');
        expect(result[2].harga).toBe('10,500');
    });

    test('should remove the dynamic date key from output items', () => {
        const result = processApiData(mockApiResponse, '2026-05-23', 1, 1);

        result.forEach(item => {
            expect(item).not.toHaveProperty('23/05/2026');
        });
    });

    test('should map regencyId to correct daerah name', () => {
        const resultBandaAceh = processApiData(mockApiResponse, '2026-05-23', 1, 1);
        const resultLhokseumawe = processApiData(mockApiResponse, '2026-05-23', 2, 1);
        const resultMeulaboh = processApiData(mockApiResponse, '2026-05-23', 3, 1);

        expect(resultBandaAceh[0].daerah).toBe('Banda Aceh');
        expect(resultLhokseumawe[0].daerah).toBe('Lhokseumawe');
        expect(resultMeulaboh[0].daerah).toBe('Meulaboh');
    });

    test('should map priceTypeId to correct sumber name', () => {
        const resultTraditional = processApiData(mockApiResponse, '2026-05-23', 1, 1);
        const resultModern = processApiData(mockApiResponse, '2026-05-23', 1, 2);
        const resultWholesale = processApiData(mockApiResponse, '2026-05-23', 1, 3);
        const resultProducer = processApiData(mockApiResponse, '2026-05-23', 1, 4);

        expect(resultTraditional[0].sumber).toBe('Pasar Tradisional');
        expect(resultModern[0].sumber).toBe('Pasar Modern');
        expect(resultWholesale[0].sumber).toBe('Pedagang Besar');
        expect(resultProducer[0].sumber).toBe('Produsen');
    });

    test('should handle dash "-" price as null (no data available)', () => {
        const dataWithDash = [
            { no: 'I', name: 'Gula', level: 1, '01/01/2025': '-' }
        ];
        const result = processApiData(dataWithDash, '2025-01-01', 1, 1);

        expect(result[0].harga).toBeNull();
    });

    test('should handle undefined price key as null', () => {
        // Item has no price key for the given date at all
        const dataNoPrice = [
            { no: 'I', name: 'Gula', level: 1 }
        ];
        const result = processApiData(dataNoPrice, '2025-01-01', 1, 1);

        expect(result[0].harga).toBeNull();
    });

    test('should return empty array for null input', () => {
        expect(processApiData(null, '2025-01-01', 1, 1)).toEqual([]);
    });

    test('should return empty array for empty array input', () => {
        expect(processApiData([], '2025-01-01', 1, 1)).toEqual([]);
    });

    test('should handle multiple parent categories in sequence', () => {
        const multiCategory = [
            { no: 'I', name: 'Beras', level: 1, '01/01/2025': '12,000' },
            { no: '1', name: 'Beras Bawah', level: 2, '01/01/2025': '11,000' },
            { no: 'II', name: 'Daging', level: 1, '01/01/2025': '80,000' },
            { no: '1', name: 'Daging Sapi', level: 2, '01/01/2025': '120,000' }
        ];
        const result = processApiData(multiCategory, '2025-01-01', 1, 1);

        expect(result[0].komoditas).toBe('Beras');
        expect(result[1].komoditas).toBe('Beras');
        expect(result[2].komoditas).toBe('Daging');
        expect(result[3].komoditas).toBe('Daging');
    });
});

// ============================================================
// 3. getFilePathForYear() — Path Generation
// ============================================================
describe('getFilePathForYear — File Path Generation', () => {
    test('should generate correct path for a given year', () => {
        const result = getFilePathForYear('2025');
        expect(result).toBe(path.join(TEST_DATA_DIR, '2025.json'));
    });

    test('should generate path ending with .json extension', () => {
        const result = getFilePathForYear('2021');
        expect(result).toMatch(/\.json$/);
    });

    test('should include the data directory in path', () => {
        const result = getFilePathForYear('2026');
        expect(result).toContain(path.join('dataup', 'data'));
    });
});

// ============================================================
// 4. readJsonFile() & writeJsonFile() — File I/O
// ============================================================
describe('readJsonFile & writeJsonFile — File I/O Operations', () => {
    test('writeJsonFile should create a valid JSON file', () => {
        const testData = [{ komoditas: 'Beras', harga: '12,000' }];
        writeJsonFile(TEST_FILE, testData);

        expect(fs.existsSync(TEST_FILE)).toBe(true);

        const content = fs.readFileSync(TEST_FILE, 'utf8');
        const parsed = JSON.parse(content);
        expect(parsed).toEqual(testData);
    });

    test('readJsonFile should parse and return JSON data', () => {
        const testData = [
            { komoditas: 'Beras', harga: '12,000', tanggal: '2025-01-01' },
            { komoditas: 'Gula', harga: '18,000', tanggal: '2025-01-01' }
        ];
        writeJsonFile(TEST_FILE, testData);

        const result = readJsonFile(TEST_FILE);
        expect(result).toEqual(testData);
        expect(result).toHaveLength(2);
    });

    test('readJsonFile should return empty array for non-existent file', () => {
        const result = readJsonFile('/nonexistent/path/ghost.json');
        expect(result).toEqual([]);
    });

    test('readJsonFile should return empty array for corrupted JSON', () => {
        const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
        fs.writeFileSync(TEST_FILE, '{ this is not valid JSON !!!', 'utf8');
        const result = readJsonFile(TEST_FILE);
        expect(result).toEqual([]);
        spy.mockRestore();
    });

    test('writeJsonFile should pretty-print with 2-space indentation', () => {
        writeJsonFile(TEST_FILE, [{ a: 1 }]);
        const content = fs.readFileSync(TEST_FILE, 'utf8');
        // JSON.stringify with null, 2 produces 2-space indented output
        expect(content).toBe(JSON.stringify([{ a: 1 }], null, 2));
    });

    test('writeJsonFile should handle write errors gracefully', () => {
        // Try writing to an invalid path — should not throw
        const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
        expect(() => {
            writeJsonFile('/invalid/path/impossible.json', []);
        }).not.toThrow();
        spy.mockRestore();
    });
});

// ============================================================
// 5. logMessage() — Dual-Output Logger
// ============================================================
describe('logMessage — Structured Logger', () => {
    test('should log info messages to console.log', () => {
        const spy = jest.spyOn(console, 'log').mockImplementation(() => {});
        logMessage('[INFO] Test message');
        expect(spy).toHaveBeenCalledTimes(1);
        expect(spy.mock.calls[0][0]).toContain('[INFO] Test message');
        spy.mockRestore();
    });

    test('should log error messages to console.error when isError=true', () => {
        const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
        logMessage('[ERROR] Something broke', true);
        expect(spy).toHaveBeenCalledTimes(1);
        expect(spy.mock.calls[0][0]).toContain('[ERROR] Something broke');
        spy.mockRestore();
    });

    test('should include timestamp in log output', () => {
        const spy = jest.spyOn(console, 'log').mockImplementation(() => {});
        logMessage('timestamp test');
        // Timestamp format: [YYYY-MM-DD HH:mm:ss]
        expect(spy.mock.calls[0][0]).toMatch(/^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]/);
        spy.mockRestore();
    });

    test('should append to process.log file', () => {
        const spy = jest.spyOn(console, 'log').mockImplementation(() => {});
        logMessage('[INFO] File log test');
        spy.mockRestore();

        expect(fs.existsSync(LOG_FILE)).toBe(true);
        const logContent = fs.readFileSync(LOG_FILE, 'utf8');
        expect(logContent).toContain('[INFO] File log test');
    });
});

// ============================================================
// 6. delay() — Async Utility
// ============================================================
describe('delay — Async Delay Utility', () => {
    test('should resolve after the specified milliseconds', async () => {
        const start = Date.now();
        await delay(100);
        const elapsed = Date.now() - start;
        // Allow 50ms tolerance for timer imprecision
        expect(elapsed).toBeGreaterThanOrEqual(80);
    });

    test('should return a Promise', () => {
        const result = delay(10);
        expect(result).toBeInstanceOf(Promise);
    });
});

// ============================================================
// 7. fetchDataFromAPI() — API Calls with Auto-Retry (Mocked)
// ============================================================
describe('fetchDataFromAPI — API Fetch with Retry Mechanism', () => {
    beforeEach(() => {
        jest.spyOn(console, 'log').mockImplementation(() => {});
        jest.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
        jest.restoreAllMocks();
        axios.get.mockReset();
    });

    test('should return data on successful API response', async () => {
        const mockData = [{ name: 'Beras', level: 1 }];
        axios.get.mockResolvedValueOnce({
            data: { data: mockData }
        });

        const result = await fetchDataFromAPI('2025-01-01', 1, 1);
        expect(result).toEqual(mockData);
    });

    test('should return empty array when API returns no data field', async () => {
        axios.get.mockResolvedValueOnce({ data: {} });

        const result = await fetchDataFromAPI('2025-01-01', 1, 1);
        expect(result).toEqual([]);
    });

    test('should return empty array when API returns null data', async () => {
        axios.get.mockResolvedValueOnce({ data: null });

        const result = await fetchDataFromAPI('2025-01-01', 1, 1);
        expect(result).toEqual([]);
    });

    test('should retry on network error and succeed on 2nd attempt', async () => {
        axios.get
            .mockRejectedValueOnce(new Error('ECONNRESET'))
            .mockResolvedValueOnce({
                data: { data: [{ name: 'Gula' }] }
            });

        const result = await fetchDataFromAPI('2025-01-01', 1, 1, 2);
        expect(result).toEqual([{ name: 'Gula' }]);
        expect(axios.get).toHaveBeenCalledTimes(2);
    });

    test('should return empty array after all retries exhausted', async () => {
        axios.get
            .mockRejectedValueOnce(new Error('ECONNRESET'))
            .mockRejectedValueOnce(new Error('ENOTFOUND'))
            .mockRejectedValueOnce(new Error('Timeout'));

        const result = await fetchDataFromAPI('2025-01-01', 1, 1, 3);
        expect(result).toEqual([]);
        expect(axios.get).toHaveBeenCalledTimes(3);
    });

    test('should pass correct parameters to BI API endpoint', async () => {
        axios.get.mockResolvedValueOnce({ data: { data: [] } });

        await fetchDataFromAPI('2025-03-15', 2, 3);

        expect(axios.get).toHaveBeenCalledWith(
            'https://www.bi.go.id/hargapangan/WebSite/TabelHarga/GetGridDataDaerah',
            expect.objectContaining({
                params: expect.objectContaining({
                    price_type_id: 3,
                    province_id: 1,
                    regency_id: 2,
                    start_date: '2025-03-15',
                    end_date: '2025-03-15'
                }),
                timeout: 15000
            })
        );
    });

    test('should default to 3 retries when not specified', async () => {
        axios.get
            .mockRejectedValueOnce(new Error('err1'))
            .mockRejectedValueOnce(new Error('err2'))
            .mockRejectedValueOnce(new Error('err3'));

        await fetchDataFromAPI('2025-01-01', 1, 1);
        expect(axios.get).toHaveBeenCalledTimes(3);
    });
});
