import { Action, ActionPanel, Detail, Form, Icon, Toast, showHUD, showToast, useNavigation } from "@raycast/api";
import { useState } from "react";
import { apiFetch, getServerConfig } from "./shared";

type QueryResponse = {
  answer: string;
  sources?: { title?: string; path?: string; url?: string }[];
};

export default function Command() {
  const { push } = useNavigation();
  const [query, setQuery] = useState("");

  async function onSubmit(values: { question: string }) {
    const q = values.question?.trim();
    if (!q) {
      await showToast({ style: Toast.Style.Failure, title: "Please enter a question" });
      return;
    }
    try {
      const data = await apiFetch<QueryResponse>("/query", {
        method: "POST",
        body: JSON.stringify({ query: q }),
      });
      push(<AnswerDetail response={data} />);
      await showHUD("Answered by Academy Companion");
    } catch (e: any) {
      await showToast({ style: Toast.Style.Failure, title: "Query failed", message: String(e?.message ?? e) });
    }
  }

  const { url } = getServerConfig();

  return (
    <Form
      actions={
        <ActionPanel>
          <Action.SubmitForm title="Ask" onSubmit={onSubmit} />
          <Action.OpenInBrowser title="Open Server" url={url} />
        </ActionPanel>
      }
    >
      <Form.Description text="Ask your Academy knowledge base. Answers are grounded in your indexed content." />
      <Form.TextArea id="question" title="Your Question" value={query} onChange={setQuery} />
    </Form>
  );
}

function AnswerDetail({ response }: { response: QueryResponse }) {
  const md = `# Answer

${response.answer || "_No answer returned._"}

${
  response.sources && response.sources.length
    ? `## Sources\n` +
      response.sources
        .map((s, i) => {
          const label = s.title ?? s.path ?? s.url ?? "Source";
          const link = s.url ?? s.path ?? "";
          return `- ${i + 1}. ${link ? `[${label}](${link})` : label}`;
        })
        .join("\n")
    : ""
}
`;
  return (
    <Detail
      markdown={md}
      actions={
        <ActionPanel>
          <Action.CopyToClipboard title="Copy Answer" content={response.answer} />
        </ActionPanel>
      }
    />
  );
}