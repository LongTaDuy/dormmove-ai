"use client";

import { FormEvent, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { ConnectionError } from "@/components/ConnectionError";
import { EvidencePanel } from "@/components/EvidencePanel";
import { LoadingState } from "@/components/LoadingState";
import { getApiErrorMessage, isNetworkError, searchKnowledge } from "@/lib/api";
import type { EvidenceItem } from "@/types";

const TAG_FILTERS = [
  "rules",
  "packing",
  "budget",
  "roommate",
  "logistics",
  "safety",
] as const;

export default function KnowledgePage() {
  const [query, setQuery] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [results, setResults] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);

  async function runSearch(searchQuery: string, tags: string[]) {
    const q = searchQuery.trim();
    if (!q) return;

    setLoading(true);
    setErrorMessage(null);
    setIsOffline(false);
    setSearched(true);

    try {
      const data = await searchKnowledge(q, 8, tags.length ? tags : undefined);
      setResults(data);
    } catch (e) {
      setResults([]);
      setErrorMessage(getApiErrorMessage(e));
      setIsOffline(isNetworkError(e));
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    runSearch(query, selectedTags);
  }

  function toggleTag(tag: string) {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <h1 className="page-title">Evidence Lab</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          Search the local curated dorm knowledge base. This debug view shows
          how DormMove grounds generic rule and logistics guidance—no external
          vector database required.
        </p>

        <form onSubmit={handleSubmit} className="card mt-6 space-y-4 p-5">
          <label className="block">
            <span className="section-title">Search query</span>
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. candles hot plate extension cord"
              className="mt-2 w-full rounded-xl border border-border bg-ivory px-4 py-3 text-base text-espresso placeholder:text-muted/70 focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
              aria-label="Knowledge search query"
            />
          </label>

          <div>
            <p className="section-title">Filter by tags</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {TAG_FILTERS.map((tag) => {
                const active = selectedTags.includes(tag);
                return (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => toggleTag(tag)}
                    aria-pressed={active}
                    className={`rounded-full border px-3 py-1 text-xs font-medium transition focus:outline-none focus:ring-2 focus:ring-brand/30 ${
                      active
                        ? "border-brand/40 bg-brand-light text-brand"
                        : "border-border bg-cream/60 text-muted hover:border-border-dark"
                    }`}
                  >
                    {tag}
                  </button>
                );
              })}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn-primary"
            aria-label="Search knowledge base"
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </form>

        {loading && <LoadingState message="Searching knowledge base…" />}

        {errorMessage && isOffline && (
          <div className="mt-6">
            <ConnectionError
              message={errorMessage}
              onRetry={() => runSearch(query, selectedTags)}
            />
          </div>
        )}

        {errorMessage && !isOffline && (
          <p className="mt-6 text-sm text-warning">{errorMessage}</p>
        )}

        {!loading && searched && !errorMessage && results.length === 0 && (
          <div className="card mt-6 p-8 text-center">
            <p className="text-sm text-muted">
              No documents matched your query. Try broader keywords or fewer tag
              filters.
            </p>
          </div>
        )}

        {!loading && results.length > 0 && (
          <div className="mt-6">
            <p className="mb-3 text-sm text-muted">
              {results.length} result{results.length === 1 ? "" : "s"}
            </p>
            <EvidencePanel evidence={results} title="" compact={false} />
          </div>
        )}
      </div>
    </AppShell>
  );
}
