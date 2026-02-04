interface Tool {
    name: string;
    description: string;
    command: string;
    verified: boolean;
    repoUrl: string;
    stars: number;
    lastUpdated: string;
}
export declare class ToolSmith {
    private tools;
    private git;
    constructor();
    /**
     * Discover and integrate a tool from a GitHub repository
     */
    learnFromRepo(repoUrl: string): Promise<Tool | null>;
    /**
     * Extract repository info from URL
     */
    private extractRepoInfo;
    private getRepoMetadata;
    /**
     * Extract tool information from README
     */
    private extractToolInfo;
    private verifyTool;
    /**
     * Get all learned tools
     */
    getTools(): Tool[];
    /**
     * Search for tools by keyword
     */
    searchGitHub(query: string): Promise<string[]>;
    /**
     * Get tool by name
     */
    getTool(name: string): Tool | undefined;
    /**
     * Remove tool from registry
     */
    removeTool(name: string): boolean;
    /**
     * Create a new skill using the IPPOC scaffolding script
     */
    createSkill(name: string, pathStr: string, resources?: string[]): Promise<boolean>;
}
export {};
