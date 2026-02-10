export declare class WebLearner {
    constructor();
    /**
     * Research a topic with specified depth
     */
    researchTopic(query: string, depth?: "SURFACE" | "DEEP" | "ACADEMIC"): Promise<string>;
    /**
     * Find code solution for an error
     */
    findCodeSolution(error: string): Promise<string>;
    /**
     * Decompose query based on research depth
     */
    private decompose;
    /**
     * Extract keywords from error message
     */
    private extractErrorKeywords;
    private braveSearch;
    /**
     * Extract code snippets from search results
     */
    private extractCodeSnippets;
    /**
     * Synthesize search results
     */
    private synthesizeResults;
}
