import { ParallelTestHelpers } from '@helpers/ParallelTestHelpers';

/**
 * Helper utilities for test data generation
 */
export class TestDataHelpers {
    /**
     * Generate unique ID (parallel-safe)
     */
    static generateId(): string {
        return ParallelTestHelpers.generateUniqueTestId('test');
    }

    /**
     * Generate unique email (parallel-safe)
     */
    static generateEmail(): string {
        return ParallelTestHelpers.generateUniqueEmail();
    }

    /**
     * Generate random string
     */
    static generateString(length: number = 10): string {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }

    /**
     * Generate random number
     */
    static generateNumber(min: number = 0, max: number = 1000): number {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    /**
     * Generate workflow name (parallel-safe)
     */
    static generateWorkflowName(): string {
        return ParallelTestHelpers.generateUniqueWorkflowName();
    }

    /**
     * Generate workflow input
     */
    static generateWorkflowInput(template: Record<string, any> = {}): string {
        const defaultInput = {
            id: this.generateId(),
            timestamp: new Date().toISOString(),
            ...template
        };
        return JSON.stringify(defaultInput);
    }

    /**
     * Get current timestamp
     */
    static getTimestamp(): string {
        return new Date().toISOString();
    }

    /**
     * Get formatted date
     */
    static getFormattedDate(date: Date = new Date()): string {
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    }


    /**
     * Create test object with defaults
     */
    static createTestObject<T>(defaults: T, overrides: Partial<T> = {}): T {
        return { ...defaults, ...overrides };
    }
}
