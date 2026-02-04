import { z } from "zod";
import axios from "axios";

// Search API configuration
const BRAVE_SEARCH_API_KEY = process.env.BRAVE_SEARCH_API_KEY || "demo-key";
const BRAVE_SEARCH_ENDPOINT = "https://api.search.brave.com/res/v1/web/search";

export class WebLearner {
  constructor() {
    console.log("[Cerebellum] Web Learner online.");
  }

  /**
   * Research a topic with specified depth
   */
  public async researchTopic(query: string, depth: "SURFACE" | "DEEP" | "ACADEMIC" = "SURFACE"): Promise<string> {
    console.log(`[Cerebellum] Researching: "${query}" (Depth: ${depth})`);

    // 1. Decompose Query
    const subQueries = this.decompose(query, depth);
    console.log(`[Cerebellum] Generated sub-queries: ${subQueries.join(", ")}`);

    // 2. Search
    const searchResults = await Promise.all(subQueries.map(q => this.braveSearch(q)));

    // 3. Synthesize
    return this.synthesizeResults(query, searchResults);
  }

  /**
   * Find code solution for an error
   */
  public async findCodeSolution(error: string): Promise<string> {
    console.log(`[Cerebellum] Hunting for fix for: ${error}`);
    
    // 1. Extract keywords from error
    const keywords = this.extractErrorKeywords(error);
    const searchQuery = `fix ${keywords} error`;

    // 2. Search GitHub/StackOverflow
    const results = await this.braveSearch(searchQuery);
    
    // 3. Extract and adapt code solutions
    const codeSnippets = this.extractCodeSnippets(results);
    
    if (codeSnippets.length > 0) {
      return codeSnippets[0]; // Return first relevant snippet
    }

    return "// No code solution found";
  }

  /**
   * Decompose query based on research depth
   */
  private decompose(query: string, depth: string): string[] {
    switch (depth) {
      case "SURFACE":
        return [`${query} tutorial`, `${query} documentation`];
      case "DEEP":
        return [`${query} tutorial`, `${query} documentation`, `${query} examples`, `${query} best practices`];
      case "ACADEMIC":
        return [`${query} tutorial`, `${query} documentation`, `${query} research papers`, `${query} implementation details`, `${query} benchmarks`];
      default:
        return [`${query} tutorial`, `${query} documentation`];
    }
  }

  /**
   * Extract keywords from error message
   */
  private extractErrorKeywords(error: string): string {
    // Simple keyword extraction - remove common words and symbols
    const keywords = error.toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 3 && !["error", "exception", "at", "in", "for", "the", "and"].includes(word));
    
    return keywords.slice(0, 3).join(" ");
  }

  /**
   * Brave Search API integration
   */
  private async braveSearch(query: string): Promise<any[]> {
    try {
      console.log(`[Cerebellum] Searching for: ${query}`);
      
      const response = await axios.get(BRAVE_SEARCH_ENDPOINT, {
        headers: {
          "Accept": "application/json",
          "X-Subscription-Token": BRAVE_SEARCH_API_KEY,
        },
        params: {
          q: query,
          count: 10,
        },
      });

      return response.data.web?.results || [];
    } catch (error) {
      console.error("[Cerebellum] Search failed:", error);
      return [];
    }
  }

  /**
   * Extract code snippets from search results
   */
  private extractCodeSnippets(results: any[]): string[] {
    const codeSnippets: string[] = [];
    
    results.forEach(result => {
      const codeBlockRegex = /```(?:[\w]*)\n([\s\S]*?)```/g;
      const matches = result.description.matchAll(codeBlockRegex);
      
      for (const match of matches) {
        codeSnippets.push(match[1].trim());
      }
    });

    return codeSnippets;
  }

  /**
   * Synthesize search results
   */
  private synthesizeResults(query: string, searchResults: any[][]): string {
    const allResults = searchResults.flat();
    let summary = `Synthesized knowledge about ${query}:\n\n`;

    allResults.slice(0, 3).forEach((result, index) => {
      summary += `${index + 1}. ${result.title}\n`;
      summary += `   ${result.description}\n`;
      summary += `   Source: ${result.url}\n\n`;
    });

    if (allResults.length > 3) {
      summary += `and ${allResults.length - 3} more results...\n`;
    }

    return summary;
  }
}
