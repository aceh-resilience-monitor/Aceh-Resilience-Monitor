const fs = require('fs');
const axios = require('axios');
const path = require('path');
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

jest.mock('fs');
jest.mock('axios');

describe('helper.js', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('fetchDataFromAPI', () => {
        it('should fetch data successfully on the first attempt', async () => {
            const mockData = { data: [{ id: 1, name: 'Beras' }] };
            axios.get.mockResolvedValueOnce({ data: mockData });

            const result = await fetchDataFromAPI('2023-10-01', 1, 1);
            
            expect(result).toEqual(mockData.data);
            expect(axios.get).toHaveBeenCalledTimes(1);
        });

        it('should return empty array if no data in response', async () => {
            axios.get.mockResolvedValueOnce({ data: {} });

            const result = await fetchDataFromAPI('2023-10-01', 1, 1);
            
            expect(result).toEqual([]);
        });

        it('should retry on failure and eventually succeed', async () => {
            const mockData = { data: [{ id: 1, name: 'Beras' }] };
            axios.get
                .mockRejectedValueOnce(new Error('Network Error'))
                .mockResolvedValueOnce({ data: mockData });

            // Spy on console to prevent cluttering output
            jest.spyOn(console, 'log').mockImplementation(() => {});
            // Mock fs.appendFileSync for logMessage to avoid writing real files
            fs.appendFileSync.mockImplementation(() => {});

            // Retries = 2, so it will fail once, delay 2 seconds, and then succeed.
            const result = await fetchDataFromAPI('2023-10-01', 1, 1, 2);
            
            expect(result).toEqual(mockData.data);
            expect(axios.get).toHaveBeenCalledTimes(2);
            
            console.log.mockRestore();
        }, 10000); // increase timeout for this test due to 2000ms delay

        it('should return empty array after all retries fail', async () => {
            axios.get.mockRejectedValue(new Error('Network Error'));
            
            jest.spyOn(console, 'log').mockImplementation(() => {});
            jest.spyOn(console, 'error').mockImplementation(() => {});
            fs.appendFileSync.mockImplementation(() => {});

            // Retries = 2
            const result = await fetchDataFromAPI('2023-10-01', 1, 1, 2);
            
            expect(result).toEqual([]);
            expect(axios.get).toHaveBeenCalledTimes(2);
            
            console.log.mockRestore();
            console.error.mockRestore();
        }, 10000);
    });

    describe('processApiData', () => {
        it('should process API data correctly', () => {
            const apiData = [
                {
                    id: 1,
                    name: 'Beras',
                    level: 1,
                    '01/10/2023': '10000'
                },
                {
                    id: 2,
                    name: 'Beras Kualitas Bawah I',
                    level: 2,
                    '01/10/2023': '9000'
                }
            ];

            const result = processApiData(apiData, '2023-10-01', 1, 1);

            expect(result).toHaveLength(2);
            
            // Parent logic check
            expect(result[0].komoditas).toBe('Beras');
            expect(result[0].harga).toBe('10000');
            expect(result[0].daerah).toBe('Banda Aceh'); // MAPPING_DAERAH[1]
            expect(result[0].sumber).toBe('Pasar Tradisional'); // MAPPING_SUMBER[1]
            expect(result[0]['01/10/2023']).toBeUndefined(); // ensure raw date key is deleted

            // Child logic check (inherits parent's kategori/komoditas if parent was processed just before)
            expect(result[1].komoditas).toBe('Beras');
            expect(result[1].harga).toBe('9000');
        });

        it('should handle "-" or undefined prices as null', () => {
            const apiData = [
                {
                    name: 'Beras',
                    level: 1,
                    '01/10/2023': '-'
                }
            ];

            const result = processApiData(apiData, '2023-10-01', 1, 1);
            expect(result[0].harga).toBeNull();
        });

        it('should return empty array if apiData is empty', () => {
            expect(processApiData([], '2023-10-01', 1, 1)).toEqual([]);
            expect(processApiData(null, '2023-10-01', 1, 1)).toEqual([]);
        });
    });

    describe('getFilePathForYear', () => {
        it('should return the correct file path for a given year', () => {
            const filePath = getFilePathForYear(2023);
            expect(filePath).toContain('2023.json');
            expect(filePath).toContain('data');
        });
    });

    describe('readJsonFile', () => {
        it('should read and parse JSON if file exists', () => {
            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockReturnValue('{"key":"value"}');

            const result = readJsonFile('test.json');
            expect(result).toEqual({ key: 'value' });
            expect(fs.readFileSync).toHaveBeenCalledWith('test.json', 'utf8');
        });

        it('should return empty array if file does not exist', () => {
            fs.existsSync.mockReturnValue(false);

            const result = readJsonFile('test.json');
            expect(result).toEqual([]);
        });

        it('should return empty array and log error if parsing fails', () => {
            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockReturnValue('invalid-json');
            
            jest.spyOn(console, 'error').mockImplementation(() => {});
            fs.appendFileSync.mockImplementation(() => {});

            const result = readJsonFile('test.json');
            expect(result).toEqual([]);
            
            console.error.mockRestore();
        });
    });

    describe('writeJsonFile', () => {
        it('should write data to JSON file', () => {
            const data = { key: 'value' };
            writeJsonFile('test.json', data);

            expect(fs.writeFileSync).toHaveBeenCalledWith('test.json', JSON.stringify(data, null, 2), 'utf8');
        });

        it('should log error if writing fails', () => {
            fs.writeFileSync.mockImplementation(() => {
                throw new Error('Write error');
            });
            
            jest.spyOn(console, 'error').mockImplementation(() => {});
            fs.appendFileSync.mockImplementation(() => {});

            writeJsonFile('test.json', { key: 'value' });
            
            expect(console.error).toHaveBeenCalled();
            
            console.error.mockRestore();
        });
    });
});
