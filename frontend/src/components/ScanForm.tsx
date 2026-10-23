import { useEffect, useRef, useState } from "react";
import type { CreateScanInput, TrackedItem } from "../api/hooks";

export interface ScanFormValue extends CreateScanInput {}

export default function ScanForm({
  onSubmit,
  isSubmitting,
  items
}: {
  onSubmit: (value: ScanFormValue) => void;
  isSubmitting: boolean;
  items: TrackedItem[];
}) {
  const [image, setImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [foodType, setFoodType] = useState("");
  const [trackedItemId, setTrackedItemId] = useState(() => new URLSearchParams(window.location.search).get("item") ?? "");
  const [newItemName, setNewItemName] = useState("");
  const [temperature, setTemperature] = useState("");
  const [humidity, setHumidity] = useState("");
  const [voc, setVoc] = useState("");
  const sensorTouched = useRef({ temperature: false, humidity: false, voc: false });
  const [notes, setNotes] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const cameraRef = useRef<HTMLInputElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!image || !foodType.trim()) return;
    const type = foodType.toLowerCase();
    const temp = /frozen|ice cream/.test(type) ? "-18"
      : /milk|dairy|fish|seafood|meat|chicken|egg|yogurt|cheese/.test(type) ? "4"
      : /produce|fruit|vegetable|apple|tomato/.test(type) ? "8" : "22";
    const rh = /produce|fruit|vegetable|spinach|lettuce/.test(type) ? "85" : "50";
    if (!sensorTouched.current.temperature) setTemperature(temp);
    if (!sensorTouched.current.humidity) setHumidity(rh);
    if (!sensorTouched.current.voc) setVoc("21");
  }, [image, foodType]);

  const pickFile = (file: File | undefined) => {
    setFormError(null);
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setFormError("Please choose an image file (JPEG/PNG).");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setFormError("Image must be smaller than 10 MB.");
      return;
    }
    setImage(file);
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return URL.createObjectURL(file);
    });
  };

  const clearImage = () => {
    setImage(null);
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    if (cameraRef.current) cameraRef.current.value = "";
    if (fileRef.current) fileRef.current.value = "";
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!image) {
      setFormError("A food photo is required.");
      return;
    }
    if (!navigator.onLine) {
      setFormError("Connection required for AI analysis. Please go online and retry.");
      return;
    }
    const numOrUndef = (s: string): number | undefined => {
      const t = s.trim();
      if (!t) return undefined;
      const n = Number(t);
      return Number.isFinite(n) ? n : undefined;
    };
    const t = numOrUndef(temperature);
    const h = numOrUndef(humidity);
    const v = numOrUndef(voc);
    if (temperature.trim() && t === undefined) {
      setFormError("Temperature must be a number (°C).");
      return;
    }
    if (humidity.trim() && h === undefined) {
      setFormError("Humidity must be a number (%).");
      return;
    }
    if (voc.trim() && v === undefined) {
      setFormError("VOC index must be a number.");
      return;
    }
    onSubmit({
      image,
      tracked_item_id: trackedItemId || undefined,
      new_item_name: !trackedItemId ? newItemName.trim() || undefined : undefined,
      food_type: foodType.trim() || undefined,
      temperature_c: t,
      humidity_pct: h,
      voc_index: v,
      sensor_source: Object.values(sensorTouched.current).every((touched) => !touched)
        ? "demo_estimate"
        : Object.values(sensorTouched.current).every(Boolean) ? "user_entered" : "mixed",
      notes: notes.trim() || undefined
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" aria-label="New scan form">
      {/* Hidden native inputs: one for camera, one for gallery */}
      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        aria-hidden="true"
        tabIndex={-1}
        onChange={(e) => pickFile(e.target.files?.[0])}
      />
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        aria-hidden="true"
        tabIndex={-1}
        onChange={(e) => pickFile(e.target.files?.[0])}
      />

      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-slate-800">1. Food photo</h2>
        <p className="mt-1 text-xs leading-relaxed text-slate-600">
          For package recognition, frame the product name and printed date together. Move close, tap to focus, avoid glare, and retake if the date looks blurry. For loose produce, fill the frame with the food.
        </p>
        {!previewUrl ? (
          <div className="mt-3 grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => cameraRef.current?.click()}
              className="rounded-lg bg-green-600 px-3 py-2.5 text-sm font-semibold text-white hover:bg-green-700"
            >
              Take photo
            </button>
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="rounded-lg border border-slate-300 px-3 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Upload
            </button>
          </div>
        ) : (
          <div className="mt-3">
            <img
              src={previewUrl}
              alt="Selected food preview"
              className="max-h-64 w-full rounded-xl object-cover"
            />
            <div className="mt-2 grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => cameraRef.current?.click()}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                Retake
              </button>
              <button
                type="button"
                onClick={clearImage}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-50"
              >
                Remove
              </button>
            </div>
          </div>
        )}
        <p className="mt-2 text-xs text-slate-500">
          On mobile, “Take photo” opens the rear camera.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-slate-800">
          2. Details <span className="font-normal text-slate-500">(optional)</span>
        </h2>
        <label className="mt-3 block text-sm">
          <span className="text-slate-600">Food type</span>
          <input
            type="text"
            value={foodType}
            onChange={(e) => setFoodType(e.target.value)}
            placeholder="e.g. milk, canned tuna, bread, apple"
            list="freshsense-food-suggestions"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          />
          <datalist id="freshsense-food-suggestions">
            {["Milk", "Yogurt", "Cheese", "Eggs", "Canned tuna", "Canned beans", "Bread", "Chicken", "Apples", "Frozen vegetables", "Juice", "Other"].map((choice) => <option key={choice} value={choice} />)}
          </datalist>
        </label>
        <div className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 p-3">
          <label className="block text-sm">
            <span className="font-medium text-emerald-950">Build a Freshness Passport</span>
            <span className="mt-1 block text-xs text-emerald-900">
              Track the same item across scans to compare its evidence over time.
            </span>
            <select
              value={trackedItemId}
              onChange={(e) => setTrackedItemId(e.target.value)}
              className="mt-2 w-full rounded-lg border border-emerald-300 bg-white px-3 py-2"
            >
              <option value="">Start a new passport or leave untracked</option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  Continue: {item.label} ({item.scan_count} scan{item.scan_count === 1 ? "" : "s"})
                </option>
              ))}
            </select>
          </label>
          {!trackedItemId && (
            <label className="mt-2 block text-sm">
              <span className="text-emerald-950">Passport name <span className="font-normal">(optional)</span></span>
              <input
                type="text"
                maxLength={100}
                value={newItemName}
                onChange={(e) => setNewItemName(e.target.value)}
                placeholder="e.g. Milk carton opened Monday"
                className="mt-1 w-full rounded-lg border border-emerald-300 bg-white px-3 py-2"
              />
            </label>
          )}
        </div>
        <div className="mt-3 grid grid-cols-3 gap-2">
          <label className="block text-sm">
            <span className="text-slate-600">Temp °C</span>
            <input
              type="number"
              inputMode="decimal"
              value={temperature}
              onChange={(e) => { sensorTouched.current.temperature = true; setTemperature(e.target.value); }}
              placeholder="4"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="text-slate-600">RH %</span>
            <input
              type="number"
              inputMode="decimal"
              value={humidity}
              onChange={(e) => { sensorTouched.current.humidity = true; setHumidity(e.target.value); }}
              placeholder="60"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="text-slate-600">VOC</span>
            <input
              type="number"
              inputMode="decimal"
              value={voc}
              onChange={(e) => { sensorTouched.current.voc = true; setVoc(e.target.value); }}
              placeholder="—"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </label>
        </div>
        <p className="mt-2 text-xs text-amber-800" aria-live="polite">
          {image && foodType.trim()
            ? "Illustrative demo readings are auto-filled and editable; they are not measured by a real sensor. Clear a field to omit it."
            : "Choose a photo and enter a food type to auto-fill editable demo readings. These are examples, not live sensor measurements."}
          {image && foodType.trim() && <span className="block">VOC cannot be inferred from a photo; the shown value is only a demo placeholder.</span>}
        </p>
        <label className="mt-3 block text-sm">
          <span className="text-slate-600">Notes</span>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            placeholder="Storage conditions, printed expiry…"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </label>
      </div>

      {formError && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {formError}
        </p>
      )}

      <button
        type="submit"
        disabled={isSubmitting || !image}
        className="w-full rounded-xl bg-green-600 px-4 py-3 text-base font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? "Analyzing… (server inference)" : "Analyze freshness"}
      </button>
      {isSubmitting && (
        <p aria-live="polite" className="text-center text-sm text-slate-500">
          Uploading photo and running multimodal analysis…
        </p>
      )}
    </form>
  );
}
