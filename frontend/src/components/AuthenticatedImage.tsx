import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

export default function AuthenticatedImage({ src, alt }: { src: string; alt: string }) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    let createdUrl: string | null = null;
    setFailed(false);
    setObjectUrl(null);
    apiClient.get<Blob>(src, { responseType: "blob" }).then(({ data }) => {
      if (!active) return;
      createdUrl = URL.createObjectURL(data);
      setObjectUrl(createdUrl);
    }).catch(() => {
      if (active) {
        setObjectUrl(null);
        setFailed(true);
      }
    });
    return () => {
      active = false;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [src]);

  if (!objectUrl) {
    return failed
      ? <p role="status" className="mt-3 rounded-xl bg-slate-100 p-4 text-sm text-slate-600">Scan photo unavailable.</p>
      : <div aria-label="Loading private scan image" className="mt-3 h-40 animate-pulse rounded-xl bg-slate-100" />;
  }
  return <img src={objectUrl} alt={alt} className="mt-3 max-h-64 w-full rounded-xl object-cover" loading="lazy" />;
}
