/**
 * Helpers for parallel test execution safety
 */
export class ParallelTestHelpers {
    private static instanceCounter = 0;
    private static readonly workerInfo = process.env.TEST_WORKER_INDEX || '0';

    /**
     * Generate unique test ID that includes worker information
     */
    static generateUniqueTestId(prefix: string = 'test'): string {
        const timestamp = Date.now();
        const counter = ++this.instanceCounter;
        const workerId = this.workerInfo;
        const random = Math.random().toString(36).substring(2, 8);

        return `${prefix}-w${workerId}-${timestamp}-${counter}-${random}`;
    }

    /**
     * Generate unique email for parallel tests
     */
    static generateUniqueEmail(): string {
        const uniqueId = this.generateUniqueTestId('user');
        return `${uniqueId}@test.example.com`;
    }

    /**
     * Generate unique workflow name for parallel tests
     */
    static generateUniqueWorkflowName(): string {
        return this.generateUniqueTestId('workflow');
    }

    /**
     * Get worker-specific storage key
     */
    static getWorkerStorageKey(key: string): string {
        return `worker-${this.workerInfo}-${key}`;
    }

    /**
     * Add random delay to reduce race conditions
     */
    static async addJitter(maxMs: number = 1000): Promise<void> {
        const delay = Math.random() * maxMs;
        await new Promise(resolve => setTimeout(resolve, delay));
    }

    /**
     * Lock mechanism for critical sections (browser-based)
     */
    static async acquireLock(
        page: any,
        lockName: string,
        timeout: number = 30000
    ): Promise<() => Promise<void>> {
        const lockKey = `test-lock-${lockName}`;
        const lockId = this.generateUniqueTestId('lock');
        const startTime = Date.now();

        // Try to acquire lock
        while (Date.now() - startTime < timeout) {
            const isLocked = await page.evaluate((key: string) => {
                const currentLock = localStorage.getItem(key);
                if (!currentLock || Date.now() - parseInt(currentLock) > 60000) {
                    // No lock or expired lock
                    localStorage.setItem(key, Date.now().toString());
                    return true;
                }
                return false;
            }, lockKey);

            if (isLocked) {
                // Return release function
                return async () => {
                    await page.evaluate((key: string) => {
                        localStorage.removeItem(key);
                    }, lockKey);
                };
            }

            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        throw new Error(`Failed to acquire lock ${lockName} within ${timeout}ms`);
    }

    /**
     * Get worker index
     */
    static getWorkerIndex(): number {
        return parseInt(this.workerInfo);
    }

    /**
     * Check if running in parallel mode
     */
    static isParallelMode(): boolean {
        const workers = process.env.TEST_PARALLEL_WORKERS || '1';
        return parseInt(workers) > 1;
    }

    /**
     * Get test-specific port (useful for local services)
     */
    static getTestPort(basePort: number = 3000): number {
        return basePort + this.getWorkerIndex();
    }

    /**
     * Create isolated test namespace
     */
    static createTestNamespace(): string {
        return `test-ns-${this.workerInfo}-${Date.now()}`;
    }
}
