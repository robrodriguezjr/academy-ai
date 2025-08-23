import {
  Action,
  ActionPanel,
  Detail,
  Form,
  Icon,
  Toast,
  getPreferenceValues,
  open,
  showToast,
  useNavigation,
} from "@raycast/api";
import { useEffect, useMemo, useState } from "react";

type Prefs = { apiUrl?: string; apiToken?: string };

type SourceMeta = {
  title?: string | null;
  source_url?: string | null;
  tags?: string[] | null;
  category?: string | null;
  last_updated?: string | null;
  relpath?: string | null;
  filename?: string | null;
  ext?: string | null;
  snippet?: string | null; // populated on suggestions
};

type QueryOK = {
  answer: string;
  sources: SourceMeta[];
  strict: boolean;
  top_score: number;
  threshold: number;
};

type QueryMiss = {
  answer: null;
  sources: [];
  suggestions: SourceMeta[];
  rephrases: string[];
  strict: boolean;
  top_score: number;
  threshold: number;
};

type QueryResponse = QueryOK | QueryMiss;

export default function AskForm() {
  const { push } = useNavigation();
  const [query, setQuery] = useState("");

  return (
    <Form
      actions={
        <ActionPanel>
          <Action
            title="Ask Academy KB"
            icon={Icon.MagnifyingGlass}
            onAction={() => {
              const q = query.trim();
              if (!q) return;
              push(<Results initialQuery={q} />);
            }}
          />
        </ActionPanel>
      }
    >
      <Form.TextArea
        id="query"
        title="Your Question"
        placeholder="Ask about papers, color management, workshop topics, etc."
        value={query}
        onChange={setQuery}
        enableMarkdown
        autoFocus
      />
    </Form>
  );
}

function Results({ initialQuery }: { initialQuery: string }) {
  const prefs = getPreferenceValues<Prefs>();
  const apiUrl = (prefs.apiUrl || "http://127.0.0.1:8002").replace(/\/$/, "");
  const token = prefs.apiToken?.trim();

  const [query, setQuery] = useState(initialQuery);
  const [resp, setResp] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  async function runQuery(q: string) {
    setLoading(true);
    setResp(null);
    try {
      showToast({ style: Toast.Style.Animated, title: "Querying Academy KB…" });
      const res = await fetch(`${apiUrl}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ query: q }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as QueryResponse;
      setResp(data);
      showToast({ style: Toast.Style.Success, title: "Answer ready" });
    } catch (e: any) {
      showToast({ style: Toast.Style.Failure, title: "Query failed", message: String(e?.message || e) });
      setResp(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    runQuery(query);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const markdown = useMemo(() => buildMarkdown(query, resp), [query, resp]);

  return (
    <Detail
      isLoading={loading}
      markdown={markdown}
      actions={
        <ActionPanel>
          <Action.CopyToClipboard title="Copy Answer/Details" content={markdown} />
          {"answer" in (resp || {}) && resp && (resp as QueryOK).sources?.[0]?.source_url ? (
            <Action
              title="Open First Source"
              icon={Icon.Globe}
              onAction={() => {
                const url = (resp as QueryOK).sources?.[0]?.source_url!;
                if (url) open(url);
              }}
            />
          ) : null}

          {/* When there’s no exact match, show quick actions for rephrases and suggestions */}
          {resp && "answer" in resp && resp.answer === null ? (
            <>
              {(resp.rephrases || []).slice(0, 3).map((p, i) => (
                <Action
                  key={`rephrase-${i}`}
                  title={`Try Rephrase: ${p}`}
                  icon={Icon.Sparkles}
                  onAction={() => {
                    setQuery(p);
                    runQuery(p);
                  }}
                />
              ))}
              {(resp.suggestions || []).slice(0, 3).map((s, i) =>
                s.source_url ? (
                  <Action
                    key={`sugg-${i}`}
                    title={`Open Suggested: ${s.title || s.filename || `Suggestion ${i + 1}`}`}
                    icon={Icon.Link}
                    onAction={() => open(s.source_url!)}
                  />
                ) : null
              )}
            </>
          ) : null}
        </ActionPanel>
      }
    />
  );
}

function buildMarkdown(q: string, data: QueryResponse | null): string {
  if (!data) {
    return `# Academy KB

_asking…_

> ${q}
`;
  }

  // Miss case (no exact match under threshold)
  if ("answer" in data && data.answer === null) {
    const { suggestions = [], rephrases = [], top_score, threshold } = data;

    const suggMd =
      suggestions.length === 0
        ? "_No close suggestions._"
        : suggestions
            .map((s) => {
              const title = s.title || s.filename || "Untitled";
              const updated = s.last_updated ? ` · updated ${s.last_updated}` : "";
              const tags =
                s.tags && s.tags.length ? ` · tags: ${s.tags.filter(Boolean).join(", ")}` : "";
              const cat = s.category ? ` · ${s.category}` : "";
              const link = s.source_url ? `\n   ${s.source_url}` : s.relpath ? `\n   ${s.relpath}` : "";
              const snippet = s.snippet ? `\n> ${s.snippet}` : "";
              return `- ${title}${updated}${cat}${tags}${link}${snippet}`;
            })
            .join("\n");

    const reMd =
      rephrases.length === 0 ? "_No rephrases available._" : rephrases.map((r) => `- ${r}`).join("\n");

    return `# Academy KB

No exact match found in the archive.

Query
> ${q}

Nearest suggestions
${suggMd}

Try asking it like this
${reMd}

Info
- top score: ${top_score.toFixed(2)}
- threshold: ${threshold.toFixed(2)}
`;
  }

  // OK case (we have an answer)
  const ok = data as QueryOK;
  const sources = ok.sources || [];

  const srcMd =
    sources.length === 0
      ? "_No sources returned._"
      : sources
          .map((s, i) => {
            const title = s.title || s.filename || `Source ${i + 1}`;
            const updated = s.last_updated ? ` · updated ${s.last_updated}` : "";
            const cat = s.category ? ` · ${s.category}` : "";
            const tags =
              s.tags && s.tags.length ? ` · tags: ${s.tags.filter(Boolean).join(", ")}` : "";
            const link = s.source_url ? `\n   ${s.source_url}` : s.relpath ? `\n   ${s.relpath}` : "";
            return `- ${title}${updated}${cat}${tags}${link}`;
          })
          .join("\n");

  return `# Academy KB

Q
> ${q}

${ok.answer}

---

Sources (for you in Raycast)
${srcMd}

Info
- top score: ${ok.top_score.toFixed(2)}
- threshold: ${ok.threshold.toFixed(2)}
`;
}