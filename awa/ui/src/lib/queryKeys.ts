export const queryKeys = {
    workflows: {
        run: () => ['workflows'],
        running: () => ['workflows', 'running'],
        available: () => ['workflows', 'available'],
    },
    tasks: {
        list: () => ['tasks'],
        details: (taskId: string) => ['tasks', taskId],
        response: (taskId: string) => ['tasks', 'response', taskId],
    },
}
