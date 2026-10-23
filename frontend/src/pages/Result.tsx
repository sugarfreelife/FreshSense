import { Link, useParams } from "react-router-dom";
import axios from "axios";
import { useReanalyzeScan, useScan } from "../api/hooks";
import Layout from "../components/Layout";
import ResultCard from "../components/ResultCard";
import LoadingSkeleton from "../components/LoadingSkeleton";
import { useToast } from "../components/Toast";

function reanalyzeFailureMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return "Could not reread the saved photo.";
  if (!error.response) {
    return "FreshSense’s backend is not reachable. Start the FreshSense app on this PC, then try again.";
  }
  if (error.response.status === 401) return "Your session expired. Sign in again, then reopen this scan.";
  if (error.response.status === 404) return "The saved scan or photo is missing from the backend database.";
  const detail = (error.response.data as { detail?: unknown } | undefined)?.detail;
  return typeof detail === "string" ? detail : "The backend could not reread this photo.";
}

export default function Result() {
  const { id } = useParams<{ id: string }>();
  const scanQuery = useScan(id);
  const reanalyze = useReanalyzeScan(id ?? "");
  const { push } = useToast();

  const readLabelAgain = () => {
    reanalyze.mutate(undefined, {
      onSuccess: (scan) => {
        push(scan.expiry_date ? `Package date read: ${scan.expiry_date}.` : "Package text checked.", "success");
      },
      onError: (error) => push(reanalyzeFailureMessage(error), "error")
    });
  };

  return (
    <Layout>
      <Link to="/history" className="text-sm text-green-700 underline">
        ← Back to history
      </Link>
      <h1 className="mt-2 text-2xl font-bold">Scan result</h1>
      <div className="mt-4">
        {scanQuery.isPending ? (
          <LoadingSkeleton lines={4} />
        ) : scanQuery.isError ? (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            Could not load this scan. It may not exist or you may be offline.
          </p>
        ) : scanQuery.data ? (
          <ResultCard
            scan={scanQuery.data}
            onReanalyze={readLabelAgain}
            isReanalyzing={reanalyze.isPending}
            reanalyzeError={reanalyze.error ? reanalyzeFailureMessage(reanalyze.error) : null}
          />
        ) : null}
      </div>
    </Layout>
  );
}
