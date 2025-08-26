import { Action, ActionPanel, Detail, Icon, Toast, showHUD, showToast } from "@raycast/api";
import { useEffect, useState } from "react";
import { apiFetch } from "./shared";

type StatusResponse = {
  vector_count?: number;
  last_indexed?: string | null;
  index_paths?: string[]; // optional if your API returns it
};

export default function StatusCommand() {
  const [data, setData] = useState<StatusResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const s = await apiFetch<StatusResponse>("/index-status");
        setData(s);
        // Don't use showHUD here - it closes the window!
      } catch (e: any) {
        setErr(String(e?.message ?? e));
        await showToast({ style: Toast.Style.Failure, title: "Status fetch failed", message: String(e?.message ?? e) });
      }
    })();
  }, []);

  const md = err
    ? `# Index Status\n\n**Error:** ${err}`
    : `# Index Status

- **Vector count:** ${data?.vector_count ?? "unknown"}
- **Last indexed:** ${data?.last_indexed ?? "unknown"}

${
  data?.index_paths?.length
    ? `## Indexed Paths\n${data.index_paths.map((p) => `- ${p}`).join("\n")}`
    : ""
}
`;

  return (
    <Detail
      markdown={md}
      icon={err ? Icon.XMarkCircle : Icon.Info}
      actions={
        <ActionPanel>
          <Action.CopyToClipboard title="Copy Status" content={md} />
        </ActionPanel>
      }
    />
  );
}