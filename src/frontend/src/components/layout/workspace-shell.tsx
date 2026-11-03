"use client";

import { useEffect, useState, type ReactNode } from "react";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { AppSidebar } from "./app-sidebar";
import { Topbar } from "./topbar";

const STORAGE_KEY = "datascope.sidebar.collapsed";

export function WorkspaceShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    void Promise.resolve().then(() => {
      try {
        if (window.localStorage.getItem(STORAGE_KEY) === "1") {
          setCollapsed(true);
        }
      } catch {}
    });
  }, []);

  function toggleSidebar() {
    const next = !collapsed;
    setCollapsed(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
    } catch {}
  }

  return (
    <div className="min-h-screen">
      <Topbar />
      <div className="md:flex md:min-h-[calc(100vh-4rem)]">
        {collapsed ? (
          <div className="flex items-center border-b border-slate-200 bg-white px-3 py-2 md:w-12 md:shrink-0 md:flex-col md:border-b-0 md:border-r md:px-0 md:pt-3">
            <button
              aria-label="Expand sidebar"
              className="grid h-8 w-8 place-items-center rounded-md text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
              onClick={toggleSidebar}
              title="Expand sidebar"
              type="button"
            >
              <PanelLeftOpen className="h-5 w-5" />
            </button>
          </div>
        ) : (
          <div className="relative md:flex md:shrink-0">
            <AppSidebar />
            <button
              aria-label="Collapse sidebar"
              className="absolute right-2 top-2 z-10 grid h-8 w-8 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-950"
              onClick={toggleSidebar}
              title="Collapse sidebar"
              type="button"
            >
              <PanelLeftClose className="h-5 w-5" />
            </button>
          </div>
        )}
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}