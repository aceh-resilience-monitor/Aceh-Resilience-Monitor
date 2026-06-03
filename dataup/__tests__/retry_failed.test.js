/**
 * Unit Tests for retry_failed.js — Error Log Parsing & Recovery Logic
 * 
 * Tests cover:
 * 1. generateKey() — Same composite key format as daily_update (consistency)
 * 2. Error log regex parsing — extracting failed tasks from process.log
 * 3. Year-based task grouping — optimizing file I/O by year
 * 4. Edge cases — empty logs, no errors, duplicate error entries
 */

const { generateKey } = require('../retry_failed');

// The exact regex used in retry_failed.js to parse error logs
const ERROR_REGEX = /\[ERROR\] API Request failed for (\d{4}-\d{2}-\d{2}) - Daerah: (\d+), Sumber: (\d+)/;

// ============================================================
// 1. generateKey() — Composite Key Consistency
// ============================================================
describe('generateKey — Consistency with daily_update', () => {
    test('should produce same format as daily_update generateKey', () => {
        const item = {
            tanggal: '2025-01-15',
            komoditas: 'Beras',
            daerah: 'Banda Aceh',
            sumber: 'Pasar Tradisional'
        };

        const key = generateKey(item);
        expect(key).toBe('2025-01-15|Beras|Banda Aceh|Pasar Tradisional');
    });

    test('should match daily_update key format for cross-module deduplication', () => {
        // Import daily_update's generateKey for direct comparison
        const dailyGenerateKey = require('../daily_update').generateKey;

        const item = {
            tanggal: '2025-06-01',
            komoditas: 'Gula Pasir',
            daerah: 'Meulaboh',
            sumber: 'Produsen'
        };

        expect(generateKey(item)).toBe(dailyGenerateKey(item));
    });
});

// ============================================================
// 2. Error Log Regex Parsing
// ============================================================
describe('Error Log Regex — Parsing Failed Task Entries', () => {
    test('should match standard error log line format', () => {
        const logLine = '[2025-01-08 14:23:45] [ERROR] API Request failed for 2021-01-08 - Daerah: 1, Sumber: 3 after 3 attempts. Error: ECONNRESET';
        const match = logLine.match(ERROR_REGEX);

        expect(match).not.toBeNull();
        expect(match[1]).toBe('2021-01-08');  // dateStr
        expect(match[2]).toBe('1');           // regencyId
        expect(match[3]).toBe('3');           // priceTypeId
    });

    test('should extract all 3 capture groups correctly', () => {
        const logLine = '[2025-05-20 09:15:00] [ERROR] API Request failed for 2024-12-31 - Daerah: 3, Sumber: 4 after 3 attempts. Error: ENOTFOUND';
        const match = logLine.match(ERROR_REGEX);

        expect(match[1]).toBe('2024-12-31');
        expect(parseInt(match[2])).toBe(3);
        expect(parseInt(match[3])).toBe(4);
    });

    test('should NOT match INFO log lines', () => {
        const infoLine = '[2025-01-08 14:23:45] [INFO] Fetching data for 2021-01-08...';
        expect(infoLine.match(ERROR_REGEX)).toBeNull();
    });

    test('should NOT match WARN log lines', () => {
        const warnLine = '[2025-01-08 14:23:45] [WARN] Network error on 2021-01-08 (Daerah: 1, Sumber: 3) - ECONNRESET. Retrying... (1/3)';
        expect(warnLine.match(ERROR_REGEX)).toBeNull();
    });

    test('should NOT match SUCCESS log lines', () => {
        const successLine = '[2025-01-08 14:23:45] [SUCCESS] Saved 120 records for 2021-01-08 to 2021.json';
        expect(successLine.match(ERROR_REGEX)).toBeNull();
    });

    test('should NOT match malformed date formats', () => {
        const badDate = '[2025-01-08 14:23:45] [ERROR] API Request failed for 2021-1-8 - Daerah: 1, Sumber: 3 after 3 attempts.';
        expect(badDate.match(ERROR_REGEX)).toBeNull();
    });
});

// ============================================================
// 3. Multi-line Log Parsing Simulation
// ============================================================
describe('Multi-line Log Parsing — Full Recovery Workflow', () => {
    const sampleLog = `[2025-01-08 14:20:00] [INFO] Starting backfill process...
[2025-01-08 14:20:01] [INFO] Processing date: 2021-01-04
[2025-01-08 14:20:02] [SUCCESS] Saved 48 records for 2021-01-04 to 2021.json
[2025-01-08 14:20:15] [WARN] Network error on 2021-01-08 (Daerah: 1, Sumber: 3) - ECONNRESET. Retrying... (1/3)
[2025-01-08 14:20:18] [WARN] Network error on 2021-01-08 (Daerah: 1, Sumber: 3) - ECONNRESET. Retrying... (2/3)
[2025-01-08 14:20:21] [ERROR] API Request failed for 2021-01-08 - Daerah: 1, Sumber: 3 after 3 attempts. Error: ECONNRESET
[2025-01-08 14:20:30] [ERROR] API Request failed for 2021-01-08 - Daerah: 2, Sumber: 1 after 3 attempts. Error: ENOTFOUND
[2025-01-08 14:20:45] [ERROR] API Request failed for 2022-03-15 - Daerah: 3, Sumber: 4 after 3 attempts. Error: Timeout
[2025-01-08 14:21:00] [INFO] Backfill completed successfully!`;

    function parseFailedTasks(logContent) {
        const lines = logContent.split('\n');
        const failedTasks = [];
        const taskSet = new Set();

        for (const line of lines) {
            const match = line.match(ERROR_REGEX);
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
        return failedTasks;
    }

    test('should extract exactly 3 unique failed tasks from sample log', () => {
        const tasks = parseFailedTasks(sampleLog);
        expect(tasks).toHaveLength(3);
    });

    test('should correctly identify all failed date-region-source combinations', () => {
        const tasks = parseFailedTasks(sampleLog);

        expect(tasks[0]).toEqual({ dateStr: '2021-01-08', regencyId: 1, priceTypeId: 3 });
        expect(tasks[1]).toEqual({ dateStr: '2021-01-08', regencyId: 2, priceTypeId: 1 });
        expect(tasks[2]).toEqual({ dateStr: '2022-03-15', regencyId: 3, priceTypeId: 4 });
    });

    test('should deduplicate if same error appears multiple times in log', () => {
        const duplicateLog = `[2025-01-08 14:20:21] [ERROR] API Request failed for 2021-01-08 - Daerah: 1, Sumber: 3 after 3 attempts. Error: ECONNRESET
[2025-01-09 10:00:00] [ERROR] API Request failed for 2021-01-08 - Daerah: 1, Sumber: 3 after 3 attempts. Error: ECONNRESET
[2025-01-09 10:00:05] [ERROR] API Request failed for 2021-01-08 - Daerah: 1, Sumber: 3 after 3 attempts. Error: ENOTFOUND`;

        const tasks = parseFailedTasks(duplicateLog);
        expect(tasks).toHaveLength(1);  // Same task, logged 3 times
    });

    test('should return empty array when log has no errors', () => {
        const cleanLog = `[2025-01-08 14:20:00] [INFO] Starting backfill process...
[2025-01-08 14:20:01] [SUCCESS] Saved 48 records
[2025-01-08 14:21:00] [INFO] Backfill completed successfully!`;

        const tasks = parseFailedTasks(cleanLog);
        expect(tasks).toHaveLength(0);
    });

    test('should return empty array for empty log content', () => {
        expect(parseFailedTasks('')).toHaveLength(0);
    });
});

// ============================================================
// 4. Year-based Task Grouping
// ============================================================
describe('Year-based Task Grouping — I/O Optimization', () => {
    function groupByYear(tasks) {
        const tasksByYear = {};
        for (const task of tasks) {
            const year = task.dateStr.substring(0, 4);
            if (!tasksByYear[year]) tasksByYear[year] = [];
            tasksByYear[year].push(task);
        }
        return tasksByYear;
    }

    test('should group tasks by year from date string', () => {
        const tasks = [
            { dateStr: '2021-01-08', regencyId: 1, priceTypeId: 3 },
            { dateStr: '2021-03-15', regencyId: 2, priceTypeId: 1 },
            { dateStr: '2022-06-20', regencyId: 3, priceTypeId: 4 },
            { dateStr: '2022-12-31', regencyId: 1, priceTypeId: 2 }
        ];

        const grouped = groupByYear(tasks);

        expect(Object.keys(grouped)).toHaveLength(2);
        expect(grouped['2021']).toHaveLength(2);
        expect(grouped['2022']).toHaveLength(2);
    });

    test('should handle single year correctly', () => {
        const tasks = [
            { dateStr: '2025-01-01', regencyId: 1, priceTypeId: 1 },
            { dateStr: '2025-06-15', regencyId: 2, priceTypeId: 2 }
        ];

        const grouped = groupByYear(tasks);
        expect(Object.keys(grouped)).toHaveLength(1);
        expect(grouped['2025']).toHaveLength(2);
    });

    test('should handle empty task list', () => {
        const grouped = groupByYear([]);
        expect(Object.keys(grouped)).toHaveLength(0);
    });
});
