import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type WorkspaceMode = "personal" | "business";

export const WORKSPACE_MODE_STORAGE_KEY = "freshsense-workspace-mode";
export const BUSINESS_WORKSPACE_STORAGE_KEY = "freshsense-business-workspace-id";
const WorkspaceModeContext = createContext<{
  mode: WorkspaceMode;
  setMode: (mode: WorkspaceMode) => void;
  workspaceId: string | null;
  setWorkspaceId: (id: string | null) => void;
} | null>(null);

function readMode(): WorkspaceMode {
  try {
    return localStorage.getItem(WORKSPACE_MODE_STORAGE_KEY) === "business" ? "business" : "personal";
  } catch {
    return "personal";
  }
}

export function WorkspaceModeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<WorkspaceMode>(readMode);
  const [workspaceId, setWorkspaceId] = useState<string | null>(() => {
    try { return localStorage.getItem(BUSINESS_WORKSPACE_STORAGE_KEY); }
    catch { return null; }
  });

  const updateMode = (next: WorkspaceMode) => {
    setMode(next);
    try { localStorage.setItem(WORKSPACE_MODE_STORAGE_KEY, next); } catch { /* In-memory mode still works when storage is blocked. */ }
  };

  const updateWorkspaceId = (next: string | null) => {
    setWorkspaceId(next);
    try {
      if (next) localStorage.setItem(BUSINESS_WORKSPACE_STORAGE_KEY, next);
      else localStorage.removeItem(BUSINESS_WORKSPACE_STORAGE_KEY);
    } catch { /* In-memory selection still works when storage is blocked. */ }
  };

  useEffect(() => {
    try { localStorage.setItem(WORKSPACE_MODE_STORAGE_KEY, mode); } catch { /* The in-memory choice still works when storage is blocked. */ }
  }, [mode]);

  const value = useMemo(() => ({ mode, setMode: updateMode, workspaceId, setWorkspaceId: updateWorkspaceId }), [mode, workspaceId]);
  return <WorkspaceModeContext.Provider value={value}>{children}</WorkspaceModeContext.Provider>;
}

export function useWorkspaceMode() {
  const value = useContext(WorkspaceModeContext);
  if (!value) throw new Error("useWorkspaceMode must be used inside WorkspaceModeProvider");
  return value;
}
