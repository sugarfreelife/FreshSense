import { Link } from "react-router-dom";
import Layout from "../components/Layout";

function EvidencePreview() {
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div className="absolute -inset-3 rounded-[2rem] border border-emerald-200/80" aria-hidden="true" />
      <article className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_18px_48px_-28px_rgba(15,23,42,.4)]">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Example package record</p>
            <h2 className="mt-1 text-lg font-bold text-slate-950">Chickpeas in brine</h2>
          </div>
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-900">Canned food</span>
        </div>
        <div className="grid grid-cols-[1fr_auto] gap-4 px-5 py-5">
          <div>
            <p className="text-xs font-medium text-slate-500">Package text</p>
            <p className="mt-1 font-semibold text-slate-900">BEST BEFORE</p>
            <p className="mt-1 text-sm text-slate-600">OCR found a date. Check the package before saving it.</p>
          </div>
          <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-right">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-amber-900">Review</p>
            <p className="mt-1 text-xl font-bold tabular-nums text-slate-950">14 May</p>
            <p className="text-xs text-slate-700">2027 · example only</p>
          </div>
        </div>
        <div className="border-t border-dashed border-slate-300 px-5 py-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-900">Keep the purchase as its own batch</p>
              <p className="mt-1 text-xs text-slate-600">The person saving it confirms the quantity and date.</p>
            </div>
            <span className="shrink-0 rounded-lg bg-slate-950 px-3 py-2 text-sm font-semibold text-white">12 units</span>
          </div>
        </div>
        <p className="border-t border-slate-100 bg-slate-50 px-5 py-3 text-xs text-slate-600">Illustrative screen content. FreshSense does not certify food safety.</p>
      </article>
    </div>
  );
}

export default function Landing() {
  return (
    <Layout hideNav>
      <div className="mx-auto max-w-6xl pb-10 pt-6 sm:pt-12">
        <section className="grid items-center gap-10 lg:grid-cols-[1.05fr_.95fr] lg:gap-16" aria-labelledby="landing-title">
          <div>
            <h1 id="landing-title" className="max-w-2xl text-4xl font-bold leading-[1.08] tracking-[-0.035em] text-slate-950 sm:text-5xl lg:text-[3.5rem]">
              Every package date, tied to the batch it belongs to.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-slate-700 sm:text-lg">
              Read a food label, review what the scan found, then keep each purchase or delivery lot in a date-aware inventory.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link to="/register" className="inline-flex min-h-12 items-center justify-center rounded-xl bg-emerald-800 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-900">
                Create your workspace
              </Link>
              <Link to="/login" className="inline-flex min-h-12 items-center justify-center rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50">
                Sign in
              </Link>
            </div>
            <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 border-t border-slate-200 pt-5 text-sm text-slate-700">
              <span>Package date evidence</span>
              <span>Separate purchase batches</span>
              <span>Personal and seller views</span>
            </div>
          </div>
          <EvidencePreview />
        </section>

        <section id="workflow" className="mt-16 border-t border-slate-200 pt-8 sm:mt-20" aria-labelledby="workflow-title">
          <h2 id="workflow-title" className="max-w-2xl text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">From label photo to a record you can act on.</h2>
          <ol className="mt-7 grid gap-6 border-t border-slate-200 pt-5 sm:grid-cols-3 sm:gap-8">
            <li>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-emerald-900">Capture</p>
              <h3 className="mt-2 text-lg font-semibold text-slate-950">Read the package</h3>
              <p className="mt-2 text-sm leading-6 text-slate-700">Upload or photograph the label. FreshSense shows the text and dates its OCR could read.</p>
            </li>
            <li>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-emerald-900">Review</p>
              <h3 className="mt-2 text-lg font-semibold text-slate-950">Check uncertain details</h3>
              <p className="mt-2 text-sm leading-6 text-slate-700">Confirm the product and printed date yourself when the label is unclear or incomplete.</p>
            </li>
            <li>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-emerald-900">Track</p>
              <h3 className="mt-2 text-lg font-semibold text-slate-950">Follow each batch</h3>
              <p className="mt-2 text-sm leading-6 text-slate-700">See quantities and label-date reminders across household purchases or received stock.</p>
            </li>
          </ol>
        </section>

        <p className="mt-10 max-w-4xl rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-950">
          FreshSense is an informational prototype. Its image-based freshness score is not a validated food-safety judgment; check the product and package directly.
        </p>
      </div>
    </Layout>
  );
}
