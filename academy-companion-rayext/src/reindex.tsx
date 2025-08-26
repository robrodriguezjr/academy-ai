import { Action, ActionPanel, Detail, Icon, Toast, showHUD, showToast } from "@raycast/api";
import { useEffect, useState } from "react";
import { apiFetch } from "./shared";

type ReindexResponse = { ok?: boolean; message?: string };

export default function ReindexCommand() {
  const [status, setStatus] = useState<"idle" | "running" | "done" | "error">("idle");
  const [msg, setMsg] = useState<string>("Starting reindex…");

  useEffect(() => {
    (async () => {
      setStatus("running");
      try {
        const res = await apiFetch<ReindexResponse>("/reindex", { method: "POST", body: JSON.stringify({}) });
        setStatus("done");
        setMsg(res?.message ?? "Reindex triggered");
        await showHUD("Reindex started");
      } catch (e: any) {
        setStatus("error");
        setMsg(String(e?.message ?? e));
        await showToast({ style: Toast.Style.Failure, title: "Reindex failed", message: String(e?.message ?? e) });
      }
    })();
  }, []);

  const icon =
    status === "running" ? Icon.CircleProgress : status === "done" ? Icon.CheckCircle : status === "error" ? Icon.XMarkCircle : Icon.Gear;

  const md = `# Reindex

**Status:** ${status.toUpperCase()}

${msg ? `\n${msg}\n` : ""}`;

  return (
    <Detail
      markdown={md}
      navigationTitle="Academy Companion: Reindex"
      actions={
        <ActionPanel>
          <Action.CopyToClipboard title="Copy Output" content={md} />
        </ActionPanel>
      }
      metadata={
        undefined /* keep simple; your FastAPI logs in terminal remain the source of truth while indexing runs */
      }
      icon={icon}
    />
  );
}