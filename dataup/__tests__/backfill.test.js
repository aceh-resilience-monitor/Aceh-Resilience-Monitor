const fs = require('fs');
const path = require('path');
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
const { runBackfill } = require('../backfill');

describe('backfill.js', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should iterate over 8 days (today + 7 days back)', async () => {
        helper.fetchDataFromAPI.mockResolvedValue([]);
        helper.getFilePathForYear.mockReturnValue('/mock/2026.json');
        helper.readJsonFile.mockReturnValue([]);

        await runBackfill();

        // 8 days * 3 regencies * 4 price types = 96 API calls
        expect(helper.fetchDataFromAPI).toHaveBeenCalledTimes(96);
    });

    it('should save data when API returns results', async () => {
        const mockApiData = [{ name: 'Beras', level: 1 }];
        const mockProcessed = [{ name: 'Beras', tanggal: '2026-01-01', komoditas: 'Beras', harga: '10000', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' }];

        helper.fetchDataFromAPI.mockResolvedValue(mockApiData);
        helper.processApiData.mockReturnValue(mockProcessed);
        helper.getFilePathForYear.mockReturnValue('/mock/2026.json');
        helper.readJsonFile.mockReturnValue([]);

        await runBackfill();

        expect(helper.writeJsonFile).toHaveBeenCalled();
        expect(helper.logMessage).toHaveBeenCalledWith(expect.stringContaining('[SUCCESS]'));
    });

    it('should skip saving when no data is found for a date', async () => {
        helper.fetchDataFromAPI.mockResolvedValue([]);
        helper.getFilePathForYear.mockReturnValue('/mock/2026.json');

        await runBackfill();

        // writeJsonFile should NOT be called since all API calls return empty
        expect(helper.writeJsonFile).not.toHaveBeenCalled();
        expect(helper.logMessage).toHaveBeenCalledWith(expect.stringContaining('[SKIP]'));
    });

    it('should add delay between API requests', async () => {
        helper.fetchDataFromAPI.mockResolvedValue([]);

        await runBackfill();

        expect(helper.delay).toHaveBeenCalledWith(500);
    });

    it('should sort data by tanggal before writing', async () => {
        const mockProcessed = [
            { tanggal: '2026-01-02', komoditas: 'Beras' },
            { tanggal: '2026-01-01', komoditas: 'Gula' },
        ];

        helper.fetchDataFromAPI
            .mockResolvedValueOnce([{ name: 'Beras' }])
            .mockResolvedValue([]);
        helper.processApiData.mockReturnValue(mockProcessed);
        helper.getFilePathForYear.mockReturnValue('/mock/2026.json');
        helper.readJsonFile.mockReturnValue([]);

        await runBackfill();

        if (helper.writeJsonFile.mock.calls.length > 0) {
            const writtenData = helper.writeJsonFile.mock.calls[0][1];
            for (let i = 1; i < writtenData.length; i++) {
                expect(dayjs(writtenData[i].tanggal).valueOf())
                    .toBeGreaterThanOrEqual(dayjs(writtenData[i - 1].tanggal).valueOf());
            }
        }
    });
});
