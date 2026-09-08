import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useRegister } from "../api/hooks";
import Layout from "../components/Layout";
import { useToast } from "../components/Toast";

export default function Register() {
  const navigate = useNavigate();
  const { push } = useToast();
  const register = useRegister();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || password.length < 6) {
      push("Enter a name, valid email and a 6+ character password.", "error");
      return;
    }
    register.mutate(
      { name: name.trim(), email: email.trim(), password },
      {
        onSuccess: () => {
          push("Account created.", "success");
          navigate("/dashboard");
        },
        onError: () => push("Registration failed. Try a different email.", "error")
      }
    );
  };

  return (
    <Layout hideNav>
      <h1 className="text-2xl font-bold">Create account</h1>
      <p className="mt-1 text-sm text-slate-500">
        Save scans, track shelf life, and review history.
      </p>
      <form onSubmit={handleSubmit} className="mt-4 space-y-3" aria-label="Register form">
        <label className="block text-sm">
          <span className="text-slate-600">Name</span>
          <input
            type="text"
            autoComplete="name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </label>
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
          <span className="text-slate-600">Password (min 6 chars)</span>
          <input
            type="password"
            autoComplete="new-password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </label>
        {register.isError && (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            Registration failed. The email may already be in use.
          </p>
        )}
        <button
          type="submit"
          disabled={register.isPending}
          className="w-full rounded-xl bg-green-600 px-4 py-3 font-semibold text-white hover:bg-green-700 disabled:opacity-60"
        >
          {register.isPending ? "Creating…" : "Create account"}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-slate-600">
        Have an account?{" "}
        <Link to="/login" className="text-green-700 underline">
          Sign in
        </Link>
      </p>
    </Layout>
  );
}
