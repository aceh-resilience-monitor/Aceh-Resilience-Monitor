const dayjs = require('dayjs');

// Mock helper module
jest.mock('../helper', () => ({
    delay: jest.fn().mockResolvedValue(undefined),
    logMessage: jest.fn(),
    fetchDataFromAPI: jest.fn(),
    processApiData: jest.fn(),
    getFilePathForYear: jest.fn(),
    readJsonFile: jest.fn(),
    writeJsonFile: jest.fn(),
}));

const helper = require('../helper');
const {
    generateKey,
    mergeWithoutDuplicate,
    fetchDateData,
    checkLast7Days,
    appendMissingHistoricalData,
    runDailyUpdate,
} = require('../daily_update');

describe('daily_update.js', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    // ========================================
    // generateKey
    // ========================================
    describe('generateKey', () => {
        it('should generate correct composite key', () => {
            const item = { tanggal: '2026-01-01', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' };
            expect(generateKey(item)).toBe('2026-01-01|Beras|Banda Aceh|Pasar Tradisional');
        });

        it('should handle missing fields gracefully', () => {
            const item = { tanggal: '2026-01-01' };
            const key = generateKey(item);
            expect(key).toContain('2026-01-01');
            expect(key).toContain('undefined');
        });
    });

    // ========================================
    // mergeWithoutDuplicate
    // ========================================
    describe('mergeWithoutDuplicate', () => {
        const existing = [
            { tanggal: '2026-01-01', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' },
        ];

        it('should add new entries that dont exist', () => {
            const newEntries = [
                { tanggal: '2026-01-02', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' },
            ];
            const { addedEntries, duplicateCount } = mergeWithoutDuplicate(existing, newEntries);
            expect(addedEntries).toHaveLength(1);
            expect(duplicateCount).toBe(0);
        });

        it('should skip duplicate entries', () => {
            const newEntries = [
                { tanggal: '2026-01-01', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' },
            ];
            const { addedEntries, duplicateCount } = mergeWithoutDuplicate(existing, newEntries);
            expect(addedEntries).toHaveLength(0);
            expect(duplicateCount).toBe(1);
        });

        it('should handle mix of new and duplicate entries', () => {
            const newEntries = [
                { tanggal: '2026-01-01', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' },
                { tanggal: '2026-01-02', komoditas: 'Gula', daerah: 'Meulaboh', sumber: 'Produsen' },
            ];
            const { addedEntries, duplicateCount } = mergeWithoutDuplicate(existing, newEntries);
            expect(addedEntries).toHaveLength(1);
            expect(duplicateCount).toBe(1);
        });

        it('should handle empty existing data', () => {
            const newEntries = [
                { tanggal: '2026-01-01', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' },
            ];
            const { addedEntries, duplicateCount } = mergeWithoutDuplicate([], newEntries);
            expect(addedEntries).toHaveLength(1);
            expect(duplicateCount).toBe(0);
        });

        it('should handle empty new entries', () => {
            const { addedEntries, duplicateCount } = mergeWithoutDuplicate(existing, []);
            expect(addedEntries).toHaveLength(0);
            expect(duplicateCount).toBe(0);
        });
    });

    // ========================================
    // fetchDateData
    // ========================================
    describe('fetchDateData', () => {
        it('should call API for all regency and price type combinations', async () => {
            helper.fetchDataFromAPI.mockResolvedValue([]);

            await fetchDateData('2026-01-01');

            // 3 regencies * 4 price types = 12 calls
            expect(helper.fetchDataFromAPI).toHaveBeenCalledTimes(12);
        });

        it('should return combined processed data', async () => {
            const mockApi = [{ name: 'Beras', level: 1 }];
            const mockProcessed = [{ tanggal: '2026-01-01', komoditas: 'Beras' }];

            helper.fetchDataFromAPI.mockResolvedValue(mockApi);
            helper.processApiData.mockReturnValue(mockProcessed);

            const result = await fetchDateData('2026-01-01');

            // 12 calls * 1 item each = 12 items
            expect(result).toHaveLength(12);
        });

        it('should log skip message when no data found', async () => {
            helper.fetchDataFromAPI.mockResolvedValue([]);

            await fetchDateData('2026-01-01');

            expect(helper.logMessage).toHaveBeenCalledWith(
                expect.stringContaining('[SKIP]')
            );
        });
    });

    // ========================================
    // checkLast7Days
    // ========================================
    describe('checkLast7Days', () => {
        it('should check 8 dates (today + 7 days back)', async () => {
            helper.fetchDataFromAPI.mockResolvedValue([]);

            await checkLast7Days('2026-05-20');

            // 8 dates * 12 API calls per date = 96
            expect(helper.fetchDataFromAPI).toHaveBeenCalledTimes(96);
        });

        it('should mark i>0 entries as backfill', async () => {
            const mockApi = [{ name: 'Beras', level: 1 }];
            const mockProcessed = [{ tanggal: '2026-05-20', komoditas: 'Beras' }];

            helper.fetchDataFromAPI.mockResolvedValue(mockApi);
            helper.processApiData.mockReturnValue(mockProcessed);

            const result = await checkLast7Days('2026-05-20');

            // First entry (i=0) should not be backfill
            expect(result[0].isBackfill).toBe(false);
            // Rest should be backfill
            for (let i = 1; i < result.length; i++) {
                expect(result[i].isBackfill).toBe(true);
            }
        });
    });

    // ========================================
    // runDailyUpdate (integration-like)
    // ========================================
    describe('runDailyUpdate', () => {
        it('should complete without errors when no data returned', async () => {
            helper.fetchDataFromAPI.mockResolvedValue([]);
            helper.getFilePathForYear.mockReturnValue('/mock/2026.json');
            helper.readJsonFile.mockReturnValue([]);

            await expect(runDailyUpdate()).resolves.not.toThrow();

            expect(helper.logMessage).toHaveBeenCalledWith(
                expect.stringContaining('Daily update completed successfully')
            );
        });

        it('should write file when new data is found', async () => {
            const mockApi = [{ name: 'Beras', level: 1 }];
            const mockProcessed = [{
                tanggal: '2026-05-20',
                komoditas: 'Beras',
                daerah: 'Banda Aceh',
                sumber: 'Pasar Tradisional',
                harga: '10000'
            }];

            helper.fetchDataFromAPI.mockResolvedValue(mockApi);
            helper.processApiData.mockReturnValue(mockProcessed);
            helper.getFilePathForYear.mockReturnValue('/mock/2026.json');
            helper.readJsonFile.mockReturnValue([]);

            await runDailyUpdate();

            expect(helper.writeJsonFile).toHaveBeenCalled();
        });
    });

    // ========================================
    // Scheduler analysis (no cron in code)
    // ========================================
    describe('Scheduler Analysis', () => {
        it('NOTE: daily_update.js does NOT contain a cron scheduler', () => {
            /*
             * FINDING: daily_update.js tidak menggunakan cron/scheduler.
             * Script ini hanya auto-execute saat dijalankan via `node daily_update.js`.
             * 
             * Untuk menjalankan setiap jam 8 pagi dan 8 malam,
             * diperlukan external scheduler seperti:
             *   - cron (Linux): 0 8,20 * * * cd /path/to/dataup && node daily_update.js
             *   - Task Scheduler (Windows)
             *   - Azure Functions Timer Trigger
             *   - node-cron package
             * 
             * Rekomendasi cron expression: 0 8,20 * * *
             * Timezone: pastikan server timezone = Asia/Jakarta (WIB, UTC+7)
             */
            expect(true).toBe(true); // Documented finding
        });
    });
});
