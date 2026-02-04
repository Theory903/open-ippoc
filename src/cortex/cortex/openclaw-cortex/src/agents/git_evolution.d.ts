export declare class GitEvolution {
    private git;
    private adapter;
    constructor(repoPath: string);
    /**
     * Propose and test a code patch
     */
    /**
     * Propose and test a code patch using Internal Evolution Tracking.
     * Steps:
     * 1. Check/Create 'evolution/stable' branch (disjoint from main).
     * 2. Create 'evolution/mutation-X' branch.
     * 3. Simulate.
     * 4. If PASS: Merge to 'evolution/stable' and tag with git-notes.
     */
    proposePatch(featureName: string, code: string): Promise<boolean>;
    /**
     * Check for recent failures and propose fixes
     */
    proposeFixes(): Promise<number>;
    /**
     * Check for possible optimizations
     */
    proposeOptimizations(): Promise<number>;
    /**
     * Update repository from remote
     */
    updateFromRemote(): Promise<boolean>;
}
