const fs = require('fs');
const path = require('path');

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

// Mock fs for log file reading
jest.mock('fs');

const helper = require('../helper');
const { runRetryFailed, generateKey } = require('../retry_failed');

describe('retry_failed.js', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('generateKey', () => {
        it('should generate correct composite key', () => {
            const item = { tanggal: '2026-01-01', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' };
            expect(generateKey(item)).toBe('2026-01-01|Beras|Banda Aceh|Pasar Tradisional');
        });
    });

    describe('runRetryFailed', () => {
        it('should return early if no log file exists', async () => {
            fs.existsSync.mockReturnValue(false);

            await runRetryFailed();

            expect(helper.logMessage).toHaveBeenCalledWith(
                expect.stringContaining('No process.log found')
            );
            expect(helper.fetchDataFromAPI).not.toHaveBeenCalled();
        });

        it('should return early if no errors found in log', async () => {
            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockReturnValue('[2026-01-01] [INFO] Some normal log message\n');

            await runRetryFailed();

            expect(helper.logMessage).toHaveBeenCalledWith(
                expect.stringContaining('No failed requests found')
            );
            expect(helper.fetchDataFromAPI).not.toHaveBeenCalled();
        });

        it('should parse error lines and retry API calls', async () => {
            const logContent = [
                '[2026-01-01] [ERROR] API Request failed for 2026-01-01 - Daerah: 1, Sumber: 3 after 3 attempts. Error: timeout',
                '[2026-01-01] [ERROR] API Request failed for 2026-01-02 - Daerah: 2, Sumber: 1 after 3 attempts. Error: timeout',
            ].join('\n');

            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockReturnValue(logContent);
            helper.fetchDataFromAPI.mockResolvedValue([]);
            helper.getFilePathForYear.mockReturnValue('/mock/2026.json');
            helper.readJsonFile.mockReturnValue([]);

            await runRetryFailed();

            expect(helper.fetchDataFromAPI).toHaveBeenCalledTimes(2);
            expect(helper.fetchDataFromAPI).toHaveBeenCalledWith('2026-01-01', 1, 3);
            expect(helper.fetchDataFromAPI).toHaveBeenCalledWith('2026-01-02', 2, 1);
        });

        it('should deduplicate error entries from log', async () => {
            const logContent = [
                '[2026-01-01] [ERROR] API Request failed for 2026-01-01 - Daerah: 1, Sumber: 3 after 3 attempts.',
                '[2026-01-02] [ERROR] API Request failed for 2026-01-01 - Daerah: 1, Sumber: 3 after 3 attempts.',
            ].join('\n');

            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockReturnValue(logContent);
            helper.fetchDataFromAPI.mockResolvedValue([]);
            helper.getFilePathForYear.mockReturnValue('/mock/2026.json');
            helper.readJsonFile.mockReturnValue([]);

            await runRetryFailed();

            // Same task appearing twice should only be retried once
            expect(helper.fetchDataFromAPI).toHaveBeenCalledTimes(1);
        });

        it('should save recovered data and skip duplicates', async () => {
            const logContent = '[2026-01-01] [ERROR] API Request failed for 2026-01-01 - Daerah: 1, Sumber: 1 after 3 attempts.';

            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockReturnValue(logContent);

            const existingData = [
                { tanggal: '2026-01-01', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' },
            ];

            const apiData = [{ name: 'Gula', level: 1 }];
            const processedNew = [
                { tanggal: '2026-01-01', komoditas: 'Gula', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' },
            ];

            helper.fetchDataFromAPI.mockResolvedValue(apiData);
            helper.processApiData.mockReturnValue(processedNew);
            helper.getFilePathForYear.mockReturnValue('/mock/2026.json');
            helper.readJsonFile.mockReturnValue(existingData);

            await runRetryFailed();

            expect(helper.writeJsonFile).toHaveBeenCalled();
            expect(helper.logMessage).toHaveBeenCalledWith(
                expect.stringContaining('Recovered 1 records')
            );
        });

        it('should use 1000ms delay between retries', async () => {
            const logContent = '[2026-01-01] [ERROR] API Request failed for 2026-01-01 - Daerah: 1, Sumber: 1 after 3 attempts.';

            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockReturnValue(logContent);
            helper.fetchDataFromAPI.mockResolvedValue([]);
            helper.getFilePathForYear.mockReturnValue('/mock/2026.json');
            helper.readJsonFile.mockReturnValue([]);

            await runRetryFailed();

            expect(helper.delay).toHaveBeenCalledWith(1000);
        });
    });
});
