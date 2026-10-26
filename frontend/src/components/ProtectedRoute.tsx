import { Navigate } from "react-router-dom";
import { useMe } from "../api/hooks";
import LoadingSkeleton from "./LoadingSkeleton";

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
  const meQuery = useMe();

  if (meQuery.isPending) return <LoadingSkeleton lines={3} />;
  if (meQuery.data === null) return <Navigate to="/login" replace />;
  if (meQuery.isError) {
    return (
      <div role="alert" className="mx-auto mt-12 max-w-md rounded-2xl border border-amber-200 bg-amber-50 p-6 text-center text-sm text-amber-950">
        <p className="font-semibold">We couldn’t confirm your session.</p>
        <p className="mt-2">Check your connection and try again.</p>
        <button type="button" onClick={() => void meQuery.refetch()} className="mt-4 rounded-lg border border-amber-300 bg-white px-4 py-2 font-semibold hover:bg-amber-100">
          Retry
        </button>
      </div>
    );
  }

  return children;
}
