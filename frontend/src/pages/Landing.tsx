import { Link } from "react-router-dom";
import Layout from "../components/Layout";

export default function Landing() {
  return (
    <Layout hideNav>
      <div className="space-y-6 py-4 text-center">
        <img
          src="/icons/icon-192.svg"
          alt="FreshSense AI leaf logo"
          className="mx-auto h-20 w-20"
        />
        <div>
          <h1 className="text-3xl font-bold text-slate-900">FreshSense AI</h1>
          <p className="mt-2 text-sm text-slate-600">
            A Multimodal Edge-AI Framework for Food Freshness Assessment and
            Shelf-Life Prediction Using Vision, VOC Sensing and OCR
          </p>
        </div>

        <section aria-label="How it works" className="space-y-3 text-left">
          <h2 className="text-base font-semibold text-slate-800">How it works</h2>
          <ol className="space-y-2 text-sm text-slate-600">
            <li className="rounded-xl border border-slate-200 bg-white p-3">
              <strong className="text-slate-800">1. Vision</strong> — snap a photo;
              the model assesses appearance and spoilage cues.
            </li>
            <li className="rounded-xl border border-slate-200 bg-white p-3">
              <strong className="text-slate-800">2. Sensors</strong> — optional
              temperature, humidity and VOC readings refine the verdict.
            </li>
            <li className="rounded-xl border border-slate-200 bg-white p-3">
              <strong className="text-slate-800">3. OCR + fusion</strong> — printed
              expiry dates are extracted and fused into a final recommendation
              with shelf-life estimate.
            </li>
          </ol>
        </section>

        <div className="space-y-2">
          <Link
            to="/scan"
            className="block w-full rounded-xl bg-green-600 px-4 py-3 text-base font-semibold text-white hover:bg-green-700"
          >
            Start Scan
          </Link>
          <div className="flex gap-2">
            <Link
              to="/login"
              className="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Sign in
            </Link>
            <Link
              to="/register"
              className="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Create account
            </Link>
          </div>
          <Link
            to="/dashboard"
            className="inline-block text-sm text-green-700 underline"
          >
            View demo dashboard
          </Link>
        </div>

        <p className="text-xs text-slate-400">
          Academic prototype. All predictions come from the server — nothing is
          guessed on-device, and analysis requires a connection.
        </p>
      </div>
    </Layout>
  );
}
