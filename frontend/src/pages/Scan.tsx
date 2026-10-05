import { useNavigate } from "react-router-dom";
import { useCreateScan } from "../api/hooks";
import Layout from "../components/Layout";
import ScanForm, { type ScanFormValue } from "../components/ScanForm";
import { useToast } from "../components/Toast";

function formatUploadError(error: Error): string {
  const responseData = (error as Error & { response?: { data?: { detail?: unknown } } }).response?.data;
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
  const navigate = useNavigate();
  const { push } = useToast();
  const createScan = useCreateScan();

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
      <h1 className="text-2xl font-bold">New scan</h1>
      <p className="mt-1 text-sm text-slate-500">
        Photo is analyzed on the server. Offline analysis is not available.
      </p>
      <div className="mt-4">
        <ScanForm onSubmit={handleSubmit} isSubmitting={createScan.isPending} />
        {createScan.isError && (
          <p role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {formatUploadError(createScan.error)}
          </p>
        )}
      </div>
    </Layout>
  );
}
