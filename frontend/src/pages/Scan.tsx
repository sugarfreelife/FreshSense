import { useNavigate } from "react-router-dom";
import { useCreateScan } from "../api/hooks";
import Layout from "../components/Layout";
import ScanForm, { type ScanFormValue } from "../components/ScanForm";
import { useToast } from "../components/Toast";

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
      onError: () => {
        push("Analysis failed. Check connection and try again.", "error");
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
            Upload failed. Please check your connection and retry.
          </p>
        )}
      </div>
    </Layout>
  );
}
