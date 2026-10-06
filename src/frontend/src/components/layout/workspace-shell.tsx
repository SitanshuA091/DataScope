import type { ReactNode } from "react";
import { AppSidebar } from "./app-sidebar";
import { Topbar } from "./topbar";

export function WorkspaceShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Topbar />
      <div className="md:flex md:min-h-[calc(100vh-4rem)]">
        <AppSidebar />
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
