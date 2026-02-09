export type SignalType = "KERNEL_EVENT" | "USER_INTENT" | "HIVE_PREFIX";
export interface Signal {
    id: string;
    type: SignalType;
    priority: number;
    payload: any;
}
export declare class Thalamus {
    private adapter;
    private habits;
    private reflexRules;
    constructor();
    /**
     * Route signal based on priority and type
     */
    route(signal: Signal): Promise<string>;
    /**
     * Initialize reflex rules
     */
    private initializeReflexRules;
    /**
     * Trigger reflex action based on signal
     */
    private triggerReflex;
    /**
     * Trigger habit response if available
     */
    private triggerHabit;
    /**
     * Extract query from signal
     */
    private extractQuery;
    private triggerCognition;
    /**
     * Add habit to the system
     */
    addHabit(query: string, response: string): void;
    /**
     * Remove habit from the system
     */
    removeHabit(query: string): boolean;
    /**
     * Get all habits
     */
    getHabits(): Array<{
        query: string;
        response: string;
    }>;
}
