import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useLogin } from "../api/hooks";
import Layout from "../components/Layout";
import { useToast } from "../components/Toast";
import axios from "axios";
import { useWorkspaceMode } from "../context/WorkspaceModeContext";

function loginError(error: Error): string {
  if (!axios.isAxiosError(error)) return error.message;
  if (!error.response) return "The server could not be reached. Check your connection and try again.";
  if (error.response.status === 401) return "Sign in failed. Check your email and password.";
  if (error.response.status === 429) return "Too many sign-in attempts. Wait a minute and try again.";
  return "Sign in is temporarily unavailable. Please try again.";
}

export default function Login() {
  const navigate = useNavigate();
  const { push } = useToast();
  const login = useLogin();
  const workspace = useWorkspaceMode();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!e.currentTarget.reportValidity()) return;
    if (!email || !password) {
      push("Enter email and password.", "error");
      return;
    }
    login.mutate(
      { email: email.trim(), password },
      {
        onSuccess: () => {
          workspace.setMode("personal");
          workspace.setWorkspaceId(null);
          push("Signed in.", "success");
          navigate("/dashboard");
        },
        onError: (error) => push(loginError(error), "error")
      }
    );
  };

  return (
    <Layout hideNav>
      <h1 className="text-2xl font-bold">Sign in</h1>
      <p className="mt-1 text-sm text-slate-500">
        Access your scan history and freshness reports.
      </p>
      <form noValidate onSubmit={handleSubmit} className="mt-4 space-y-3" aria-label="Login form">
        <label className="block text-sm">
          <span className="text-slate-600">Email</span>
          <input
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="text-slate-600">Password</span>
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </label>
        {login.isError && (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {loginError(login.error)}
          </p>
        )}
        <button
          type="submit"
          disabled={login.isPending}
          className="w-full rounded-xl bg-green-600 px-4 py-3 font-semibold text-white hover:bg-green-700 disabled:opacity-60"
        >
          {login.isPending ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-slate-600">
        No account?{" "}
        <Link to="/register" className="text-green-700 underline">
          Register
        </Link>
      </p>
    </Layout>
  );
}
