import { Navigate } from "react-router-dom";
import { getToken } from "../api/client";
import { useMe } from "../api/hooks";
import LoadingSkeleton from "./LoadingSkeleton";

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
  const token = getToken();
  const meQuery = useMe();

  if (!token) return <Navigate to="/login" replace />;

  if (meQuery.isPending) return <LoadingSkeleton lines={3} />;
  if (meQuery.data === null) return <Navigate to="/login" replace />;

  return children;
}
