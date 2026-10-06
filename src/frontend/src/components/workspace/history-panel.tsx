import { Card } from "@/components/ui/card";
import { formatDateTime } from "@/lib/formatters";
import type { WorkspaceDetail } from "@/types/workspace";

export function HistoryPanel({ detail }: { detail: WorkspaceDetail }) {
  const conversations = detail.conversations ?? [];

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-950">History</h2>
      </div>
      {conversations.length === 0 ? (
        <p className="px-5 py-6 text-sm text-slate-600">
          No conversation history has been saved for this workspace yet.
        </p>
      ) : (
        <div className="divide-y divide-slate-100">
          {conversations.map((conversation, index) => (
            <div className="px-5 py-4" key={index}>
              <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm font-medium text-slate-950">
                  Conversation {index + 1}
                </p>
                <p className="text-xs text-slate-500">
                  {formatDateTime(
                    typeof conversation.conversation.updated_at === "string"
                      ? conversation.conversation.updated_at
                      : null,
                  )}
                </p>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                {conversation.messages.length} saved messages
              </p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
