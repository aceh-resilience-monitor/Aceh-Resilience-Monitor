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
const { runWeeklySync } = require('../weekly_sync');

describe('weekly_sync.js', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should iterate over 8 days (7 days back + today)', async () => {
        helper.fetchDataFromAPI.mockResolvedValue([]);

        await runWeeklySync();

        // 8 days * 3 regencies * 4 price types = 96
        expect(helper.fetchDataFromAPI).toHaveBeenCalledTimes(96);
    });

    it('should save data when API returns results', async () => {
        const mockApi = [{ name: 'Beras', level: 1 }];
        const mockProcessed = [{
            tanggal: '2026-01-01', komoditas: 'Beras',
            daerah: 'Banda Aceh', sumber: 'Pasar Tradisional', harga: '10000'
        }];

        helper.fetchDataFromAPI.mockResolvedValue(mockApi);
        helper.processApiData.mockReturnValue(mockProcessed);
        helper.getFilePathForYear.mockReturnValue('/mock/2026.json');
        helper.readJsonFile.mockReturnValue([]);

        await runWeeklySync();

        expect(helper.writeJsonFile).toHaveBeenCalled();
    });

    it('should skip dates with no data', async () => {
        helper.fetchDataFromAPI.mockResolvedValue([]);

        await runWeeklySync();

        expect(helper.writeJsonFile).not.toHaveBeenCalled();
        expect(helper.logMessage).toHaveBeenCalledWith(expect.stringContaining('[SKIP]'));
    });

    it('should append to existing data', async () => {
        const existing = [{ tanggal: '2026-01-01', komoditas: 'Existing' }];
        const mockProcessed = [{ tanggal: '2026-01-02', komoditas: 'New' }];

        helper.fetchDataFromAPI
            .mockResolvedValueOnce([{ name: 'Beras' }])
            .mockResolvedValue([]);
        helper.processApiData.mockReturnValue(mockProcessed);
        helper.getFilePathForYear.mockReturnValue('/mock/2026.json');
        helper.readJsonFile.mockReturnValue(existing);

        await runWeeklySync();

        if (helper.writeJsonFile.mock.calls.length > 0) {
            const written = helper.writeJsonFile.mock.calls[0][1];
            expect(written.length).toBeGreaterThanOrEqual(2);
        }
    });

    it('should complete successfully and log completion', async () => {
        helper.fetchDataFromAPI.mockResolvedValue([]);

        await runWeeklySync();

        expect(helper.logMessage).toHaveBeenCalledWith(
            expect.stringContaining('Weekly sync completed successfully')
        );
    });
});
