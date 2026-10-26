import { useEffect, useState } from "react";
import {
  useAddWorkspaceMember,
  useBusinessWorkspaces,
  useCreateBusinessWorkspace,
  useRemoveWorkspaceMember,
  useWorkspaceMembers
} from "../api/hooks";

type Props = {
  workspaces: NonNullable<ReturnType<typeof useBusinessWorkspaces>["data"]>;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onCreated: (id: string) => void;
};

export default function BusinessWorkspacePanel({ workspaces, selectedId, onSelect, onCreated }: Props) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"manager" | "staff">("staff");
  const [message, setMessage] = useState("");
  const create = useCreateBusinessWorkspace();
  const membersQuery = useWorkspaceMembers(selectedId);
  const selected = workspaces.find((workspace) => workspace.id === selectedId);
  const addMember = useAddWorkspaceMember(selectedId);
  const removeMember = useRemoveWorkspaceMember(selectedId);

  useEffect(() => {
    if (selected?.role !== "owner") setRole("staff");
  }, [selected?.id, selected?.role]);

  const createWorkspace = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!event.currentTarget.reportValidity()) return;
    create.mutate(name.trim(), {
      onSuccess: (workspace) => {
        setName("");
        setMessage("Stock workspace created.");
        onCreated(workspace.id);
      },
      onError: () => setMessage("Could not create the workspace. Check the connection and retry.")
    });
  };

  const inviteMember = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!event.currentTarget.reportValidity()) return;
    addMember.mutate({ email: email.trim(), role: selected?.role === "owner" ? role : "staff" }, {
      onSuccess: (member) => {
        setEmail("");
        setMessage(`${member.name || member.email} added to this stock workspace.`);
      },
      onError: (error) => {
        const response = "response" in error ? (error as { response?: { data?: { detail?: string } } }).response : undefined;
        setMessage(response?.data?.detail || "Could not add that account. Check its email and your access.");
      }
    });
  };

  const canManage = selected?.role === "owner" || selected?.role === "manager";

  return (
    <section className="mt-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5" aria-labelledby="workspace-heading">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Shared business stock</p>
          <h2 id="workspace-heading" className="mt-1 text-lg font-bold text-slate-950">Stock workspace & team</h2>
          <p className="mt-1 max-w-2xl text-sm text-slate-600">Business batches are shared with members you add. Personal pantry batches stay private to your account.</p>
        </div>
        {workspaces.length > 0 && (
          <label className="min-w-52 text-xs font-semibold text-slate-600">
            Stock workspace
            <select value={selectedId ?? ""} onChange={(event) => onSelect(event.target.value || null)} className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900">
              {!selectedId && <option value="">Select a workspace</option>}
              {workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}
            </select>
          </label>
        )}
      </div>

      {workspaces.length === 0 ? (
        <form noValidate onSubmit={createWorkspace} className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto]">
          <label className="text-sm font-medium text-slate-700">Business or store name
            <input required minLength={1} maxLength={120} value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Green Market - Main Store" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </label>
          <button type="submit" disabled={create.isPending} className="self-end rounded-xl bg-emerald-800 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60">{create.isPending ? "Creating…" : "Create stock workspace"}</button>
        </form>
      ) : (
        <div className="mt-4 grid gap-4 border-t border-slate-100 pt-4 lg:grid-cols-[1fr_1.2fr]">
          <div>
            <p className="text-sm font-semibold text-slate-900">{selected?.name ?? "Choose a stock workspace"}</p>
            <p className="mt-1 text-xs text-slate-600">Your role: {selected?.role ?? "—"}. Staff members must create their own FreshSense account before you can add them.</p>
            {canManage && membersQuery.data && <ul className="mt-3 space-y-2">
      {membersQuery.data?.map((member) => (
                <li key={member.id} className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2 text-sm">
                  <span className="min-w-0"><strong className="block truncate text-slate-900">{member.name || member.email}</strong><span className="text-xs text-slate-600">{member.email} · {member.role}</span></span>
                  {selected?.role === "owner" && member.role !== "owner" && <button type="button" onClick={() => {
                    if (window.confirm(`Remove ${member.email} from ${selected?.name}? They will lose access to its stock.`)) {
                      removeMember.mutate(member.id, { onSuccess: () => setMessage("Workspace access removed."), onError: () => setMessage("Could not update workspace access.") });
                    }
                  }} className="rounded-md px-2 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-100">Remove</button>}
                </li>
              ))}
            </ul>}
            {canManage && membersQuery.isLoading && <p className="mt-3 text-sm text-slate-500">Loading team members…</p>}
            {canManage && membersQuery.isError && <p role="alert" className="mt-3 text-sm text-rose-700">Could not load team members.</p>}
          </div>
          {canManage && (
            <form noValidate onSubmit={inviteMember} className="rounded-xl border border-slate-200 p-3">
              <p className="text-sm font-semibold text-slate-900">Add a team member</p>
              <p className="mt-1 text-xs text-slate-600">Only accounts you add can see this workspace’s business inventory.</p>
              <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto_auto]">
                <label className="text-xs font-medium text-slate-600">Account email
                  <input type="email" required maxLength={255} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="colleague@example.com" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                </label>
                <label className="text-xs font-medium text-slate-600">Role
                  <select value={role} onChange={(event) => setRole(event.target.value as "manager" | "staff")} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                    <option value="staff">Staff</option>
                    {selected?.role === "owner" && <option value="manager">Manager</option>}
                  </select>
                </label>
                <button type="submit" disabled={addMember.isPending || !selectedId} className="self-end rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60">{addMember.isPending ? "Adding…" : "Add member"}</button>
              </div>
            </form>
          )}
        </div>
      )}

      {workspaces.length > 0 && (selected?.role === "owner" || selected?.role === "manager") && (
        <details className="mt-4 border-t border-slate-100 pt-3">
          <summary className="cursor-pointer text-sm font-semibold text-slate-700">Create another stock workspace</summary>
          <form noValidate onSubmit={createWorkspace} className="mt-3 flex flex-wrap gap-2">
            <label className="min-w-60 flex-1 text-xs font-semibold text-slate-600">Workspace name
              <input required maxLength={120} value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Green Market - Branch 2" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </label>
            <button type="submit" disabled={create.isPending} className="self-end rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-800">Create workspace</button>
          </form>
        </details>
      )}
      {message && <p role="status" className="mt-3 text-sm text-slate-700">{message}</p>}
    </section>
  );
}
