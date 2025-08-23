import { Action, ActionPanel, Detail, Toast, getPreferenceValues, showToast } from "@raycast/api";
import { useEffect, useState } from "react";

type Prefs = { apiUrl: string; apiToken: string };

export default function Status() {
  const { apiUrl: rawUrl, apiToken } = getPreferenceValues<Prefs>();
  const apiUrl = (rawUrl || "http://127.0.0.1:8002").replace(/\/$/, "");
  const [md, setMd] = useState("# Index Status\n\nLoading…");
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      setLoading(true);
      const res = await fetch(`${apiUrl}/stats`, {
        headers: apiToken ? { Authorization: `Bearer ${apiToken}` } : undefined,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const count = data?.count ?? "—";
      const last = data?.last_indexed ?? "Unknown";
      setMd(`# Index Status

**Vector count:** ${count}
**Last indexed:** ${last}`);
    } catch (e: any) {
      const msg = String(e?.message || e);
      setMd(`**Error**\n\n${msg}`);
      showToast({ style: Toast.Style.Failure, title: "Status failed", message: msg });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <Detail
      markdown={md}
      isLoading={loading}
      actions={
        <ActionPanel>
          <Action title="Refresh" onAction={refresh} shortcut={{ modifiers: ["cmd"], key: "r" }} />
          <Action
            title="Start Reindex"
            onAction={async () => {
              try {
                showToast({ style: Toast.Style.Animated, title: "Reindexing…" });
                const res = await fetch(`${apiUrl}/reindex`, {
                  method: "POST",
                  headers: apiToken ? { Authorization: `Bearer ${apiToken}` } : undefined,
                });
                const data = await res.json().catch(() => ({}));
                if (data?.status === "already_running") {
                  showToast({ style: Toast.Style.Secondary, title: "Reindex already running" });
                } else {
                  showToast({ style: Toast.Style.Success, title: "Reindex started" });
                }
              } catch (e: any) {
                showToast({ style: Toast.Style.Failure, title: "Reindex failed", message: String(e?.message || e) });
              }
            }}
            shortcut={{ modifiers: ["cmd", "shift"], key: "r" }}
          />
        </ActionPanel>
      }
    />
  );
}