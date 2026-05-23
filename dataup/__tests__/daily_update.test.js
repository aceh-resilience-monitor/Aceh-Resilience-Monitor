/**
 * Unit Tests for daily_update.js — Deduplication & Idempotency Logic
 * 
 * Tests cover:
 * 1. generateKey() — Composite key generation for deduplication
 * 2. Idempotency guarantee — duplicate data must be rejected
 * 3. Edge cases — missing fields, special characters in komoditas names
 */

const { generateKey } = require('../daily_update');

// ============================================================
// 1. generateKey() — Composite Key for Deduplication
// ============================================================
describe('generateKey — Composite Key Generation (Idempotency)', () => {
    test('should generate key in format: tanggal|komoditas|daerah|sumber', () => {
        const item = {
            tanggal: '2025-01-15',
            komoditas: 'Beras',
            daerah: 'Banda Aceh',
            sumber: 'Pasar Tradisional'
        };

        const key = generateKey(item);
        expect(key).toBe('2025-01-15|Beras|Banda Aceh|Pasar Tradisional');
    });

    test('should produce identical keys for identical data (idempotent)', () => {
        const item1 = {
            tanggal: '2025-06-01',
            komoditas: 'Gula Pasir',
            daerah: 'Meulaboh',
            sumber: 'Produsen'
        };
        const item2 = { ...item1 }; // clone

        expect(generateKey(item1)).toBe(generateKey(item2));
    });

    test('should produce different keys for different dates', () => {
        const itemA = {
            tanggal: '2025-01-01',
            komoditas: 'Beras',
            daerah: 'Banda Aceh',
            sumber: 'Pasar Tradisional'
        };
        const itemB = { ...itemA, tanggal: '2025-01-02' };

        expect(generateKey(itemA)).not.toBe(generateKey(itemB));
    });

    test('should produce different keys for different regions', () => {
        const itemA = {
            tanggal: '2025-01-01',
            komoditas: 'Beras',
            daerah: 'Banda Aceh',
            sumber: 'Pasar Tradisional'
        };
        const itemB = { ...itemA, daerah: 'Lhokseumawe' };

        expect(generateKey(itemA)).not.toBe(generateKey(itemB));
    });

    test('should produce different keys for different price sources', () => {
        const itemA = {
            tanggal: '2025-01-01',
            komoditas: 'Beras',
            daerah: 'Banda Aceh',
            sumber: 'Pasar Tradisional'
        };
        const itemB = { ...itemA, sumber: 'Pasar Modern' };

        expect(generateKey(itemA)).not.toBe(generateKey(itemB));
    });

    test('should produce different keys for different commodities', () => {
        const itemA = {
            tanggal: '2025-01-01',
            komoditas: 'Beras',
            daerah: 'Banda Aceh',
            sumber: 'Pasar Tradisional'
        };
        const itemB = { ...itemA, komoditas: 'Gula Pasir' };

        expect(generateKey(itemA)).not.toBe(generateKey(itemB));
    });

    test('should handle commodity names with special characters', () => {
        const item = {
            tanggal: '2025-01-01',
            komoditas: 'Beras Kualitas Bawah I (Medium)',
            daerah: 'Banda Aceh',
            sumber: 'Pasar Tradisional'
        };

        const key = generateKey(item);
        expect(key).toContain('Beras Kualitas Bawah I (Medium)');
        expect(typeof key).toBe('string');
    });
});

// ============================================================
// 2. Deduplication Simulation — Map-based Idempotency
// ============================================================
describe('Deduplication via Composite Key Map', () => {
    test('should detect duplicates when same item is processed twice', () => {
        const existingDataMap = new Map();

        const item = {
            tanggal: '2025-03-01',
            komoditas: 'Daging Sapi',
            daerah: 'Banda Aceh',
            sumber: 'Pasar Tradisional'
        };

        // First insertion — should be new
        const key = generateKey(item);
        expect(existingDataMap.has(key)).toBe(false);
        existingDataMap.set(key, true);

        // Second insertion — should be detected as duplicate
        expect(existingDataMap.has(key)).toBe(true);
    });

    test('should allow different items from same date to coexist', () => {
        const existingDataMap = new Map();

        const items = [
            { tanggal: '2025-03-01', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' },
            { tanggal: '2025-03-01', komoditas: 'Gula', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' },
            { tanggal: '2025-03-01', komoditas: 'Beras', daerah: 'Lhokseumawe', sumber: 'Pasar Tradisional' },
            { tanggal: '2025-03-01', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Modern' }
        ];

        const newEntries = [];
        for (const item of items) {
            const key = generateKey(item);
            if (!existingDataMap.has(key)) {
                existingDataMap.set(key, true);
                newEntries.push(item);
            }
        }

        // All 4 items are unique (different commodity, region, or source)
        expect(newEntries).toHaveLength(4);
    });

    test('should correctly filter duplicates from a mixed batch', () => {
        const existingDataMap = new Map();

        // Pre-load one existing record
        const existing = { tanggal: '2025-03-01', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' };
        existingDataMap.set(generateKey(existing), true);

        // Incoming batch: 1 duplicate + 2 new
        const incoming = [
            { tanggal: '2025-03-01', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' },  // DUPLICATE
            { tanggal: '2025-03-01', komoditas: 'Gula', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' },   // NEW
            { tanggal: '2025-03-02', komoditas: 'Beras', daerah: 'Banda Aceh', sumber: 'Pasar Tradisional' }    // NEW
        ];

        const newEntries = [];
        for (const item of incoming) {
            const key = generateKey(item);
            if (!existingDataMap.has(key)) {
                existingDataMap.set(key, true);
                newEntries.push(item);
            }
        }

        expect(newEntries).toHaveLength(2);
        expect(newEntries[0].komoditas).toBe('Gula');
        expect(newEntries[1].tanggal).toBe('2025-03-02');
    });
});
