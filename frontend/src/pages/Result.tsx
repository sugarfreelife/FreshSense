import { Link, useParams } from "react-router-dom";
import { useScan } from "../api/hooks";
import Layout from "../components/Layout";
import ResultCard from "../components/ResultCard";
import LoadingSkeleton from "../components/LoadingSkeleton";

export default function Result() {
  const { id } = useParams<{ id: string }>();
  const scanQuery = useScan(id);

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
          <ResultCard scan={scanQuery.data} />
        ) : null}
      </div>
    </Layout>
  );
}
