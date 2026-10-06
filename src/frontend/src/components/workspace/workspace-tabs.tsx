"use client";

type WorkspaceTab = "schema" | "analyses" | "history";

const tabs: Array<{ id: WorkspaceTab; label: string }> = [
  { id: "schema", label: "Schema" },
  { id: "analyses", label: "Analyses" },
  { id: "history", label: "History" },
];

export function WorkspaceTabs({
  activeTab,
  onChange,
}: {
  activeTab: WorkspaceTab;
  onChange: (tab: WorkspaceTab) => void;
}) {
  return (
    <div className="flex gap-1 border-b border-slate-200 bg-white px-5">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;

        return (
          <button
            className={`min-h-11 border-b-2 px-3 text-sm font-medium transition ${
              isActive
                ? "border-blue-600 text-blue-700"
                : "border-transparent text-slate-600 hover:text-slate-950"
            }`}
            key={tab.id}
            onClick={() => onChange(tab.id)}
            type="button"
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

export type { WorkspaceTab };
