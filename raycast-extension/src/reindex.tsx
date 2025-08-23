import { Detail, Toast, getPreferenceValues, showToast } from "@raycast/api";
import { useEffect, useRef, useState } from "react";

type Prefs = { apiUrl: string; apiToken: string };

export default function Reindex() {
  const { apiUrl: rawUrl, apiToken } = getPreferenceValues<Prefs>();
  const apiUrl = (rawUrl || "http://127.0.0.1:8002").replace(/\/$/, "");
  const [md, setMd] = useState("# Reindex\n\nStarting…");
  const [done, setDone] = useState(false);

  // Prevent double-fire in dev strict mode
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 12_000);

    (async () => {
      try {
        showToast({ style: Toast.Style.Animated, title: "Reindexing…" });
        const res = await fetch(`${apiUrl}/reindex`, {
          method: "POST",
          headers: { Authorization: `Bearer ${apiToken || "supersecret123"}` },
          signal: ctrl.signal,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json().catch(() => ({}));
        if (data?.status === "already_running") {
          setMd(`# Reindex\n\n**Already running** — try again in a moment.`);
          showToast({ style: Toast.Style.Secondary, title: "Reindex already running" });
        } else {
          setMd(`# Reindex\n\n**Started in background.**`);
          showToast({ style: Toast.Style.Success, title: "Reindex started" });
        }
      } catch (e: any) {
        const msg = e?.name === "AbortError" ? "Request timed out (12s)" : String(e?.message || e);
        setMd(`**Error**\n\n${msg}`);
        showToast({ style: Toast.Style.Failure, title: "Reindex failed", message: msg });
      } finally {
        clearTimeout(timer);
        setDone(true);
      }
    })();

    return () => clearTimeout(timer);
  }, [apiUrl, apiToken]);

  return <Detail markdown={md} isLoading={!done} />;
}