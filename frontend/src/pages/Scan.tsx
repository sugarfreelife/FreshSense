import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useBusinessWorkspaces, useCreateScan, useTrackedItems } from "../api/hooks";
import Layout from "../components/Layout";
import ScanForm, { type ScanFormValue } from "../components/ScanForm";
import { useToast } from "../components/Toast";
import { useWorkspaceMode } from "../context/WorkspaceModeContext";

function formatUploadError(error: Error): string {
  const requestError = error as Error & {
    code?: string;
    response?: { status?: number; data?: { detail?: unknown } };
  };
  if (requestError.code === "ECONNABORTED" || requestError.code === "ETIMEDOUT") {
    return "This scan is taking longer than expected. Check Scan history before retrying; if no result appears, try a closer photo of the printed date.";
  }
  if (!requestError.response && /network|fetch/i.test(error.message)) {
    return "FreshSense could not reach the server. Check your connection, then retry the scan.";
  }
  const responseData = requestError.response?.data;
  const detail = responseData?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail.flatMap((item) => {
      if (!item || typeof item !== "object" || !("msg" in item)) return [];
      return typeof item.msg === "string" ? [item.msg] : [];
    });
    if (messages.length) return messages.join("; ");
  }
  return error.message || "Upload failed. Please check your connection and retry.";
}

export default function Scan() {
  const { mode, workspaceId, setWorkspaceId } = useWorkspaceMode();
  const business = mode === "business";
  const navigate = useNavigate();
  const { push } = useToast();
  const createScan = useCreateScan();
  const trackedItems = useTrackedItems();
  const workspaces = useBusinessWorkspaces();
  const hasActiveWorkspace = Boolean(workspaces.data?.some((workspace) => workspace.id === workspaceId));

  useEffect(() => {
    if (!business || !workspaces.data) return;
    if (!workspaceId || !workspaces.data.some((workspace) => workspace.id === workspaceId)) {
      setWorkspaceId(workspaces.data[0]?.id ?? null);
    }
  }, [business, setWorkspaceId, workspaceId, workspaces.data]);

  const handleSubmit = (value: ScanFormValue) => {
    createScan.mutate(value, {
      onSuccess: (scan) => {
        push("Analysis complete.", "success");
        navigate(`/result/${String(scan.id)}`);
      },
      onError: (error) => {
        push(formatUploadError(error), "error");
      }
    });
  };

  return (
    <Layout>
      <h1 className="text-2xl font-bold">{business ? "Scan incoming stock" : "New scan"}</h1>
      <p className="mt-1 text-sm text-slate-500">
        {business ? "Scan a product package to identify it, read its printed date, then record the received batch quantity." : "Photo is analyzed on the server. Offline analysis is not available."}
      </p>
      <div className="mt-4">
        {business && (workspaces.isPending || (workspaces.data?.length && !hasActiveWorkspace)) ? <p role="status" className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">Loading your business stock workspace…</p>
          : business && (workspaces.isError || !hasActiveWorkspace) ? <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
            <h2 className="font-semibold text-amber-950">Set up your stock workspace first</h2>
            <p className="mt-1 text-sm text-amber-900">Business scans are shared with your stock team. Create or select a workspace before scanning incoming stock.</p>
            <Link to="/inventory" className="mt-3 inline-flex rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white">Open stock workspace setup</Link>
          </section> : <ScanForm
            onSubmit={handleSubmit}
            isSubmitting={createScan.isPending}
            items={business ? [] : trackedItems.data ?? []}
          />}
        {createScan.isError && (
          <p role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {formatUploadError(createScan.error)}
          </p>
        )}
      </div>
    </Layout>
  );
}
