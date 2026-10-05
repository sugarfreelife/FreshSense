import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult
} from "@tanstack/react-query";
import { z } from "zod";
import { apiClient, setToken } from "./client";

/* ---------- Schemas ---------- */

export const UserSchema = z.object({
  id: z.union([z.string(), z.number()]),
  email: z.string().email(),
  name: z.string().optional().nullable()
});
export type User = z.infer<typeof UserSchema>;

const AuthResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string().optional().default("bearer"),
  user: UserSchema.optional()
});
export type AuthResponse = z.infer<typeof AuthResponseSchema>;

const PassportEvidenceSchema = z.object({
  key: z.enum(["vision", "expiry", "sensor"]),
  title: z.string(),
  state: z.enum(["used", "warning", "missing", "context"]),
  observation: z.string(),
  explanation: z.string()
});

const PassportEventSchema = z.object({
  key: z.string(),
  title: z.string(),
  state: z.enum(["complete", "warning", "missing"]),
  detail: z.string(),
  occurred_at: z.string().nullable().optional()
});

const PassportSchema = z.object({
  summary: z.string(),
  explanation: z.string(),
  evidence: z.array(PassportEvidenceSchema),
  timeline: z.array(PassportEventSchema),
  limitations: z.array(z.string())
});

const NestedScanSchema = z.object({
  id: z.union([z.string(), z.number()]),
  image_url: z.string().optional().nullable(),
  food_label: z.string().optional().nullable(),
  notes: z.string().optional().nullable(),
  created_at: z.string(),
  vision: z.object({
    food_type: z.string(),
    freshness: z.string(),
    confidence: z.number(),
    model_version: z.string(),
    model_type: z.string(),
    confidence_kind: z.string().optional(),
    visual_evidence: z.record(z.string(), z.number()).optional()
  }).nullable().optional(),
  ocr: z.object({
    raw_text: z.string(),
    expiry_date: z.string().nullable().optional(),
    date_detected: z.boolean(),
    created_at: z.string().optional()
  }).nullable().optional(),
  sensor: z.object({
    gas_value: z.number().nullable().optional(),
    temperature: z.number().nullable().optional(),
    humidity: z.number().nullable().optional(),
    created_at: z.string()
  }).nullable().optional(),
  assessment: z.object({
    freshness: z.string(),
    confidence: z.number(),
    recommendation: z.string(),
    warnings: z.array(z.string()),
    modalities_used: z.array(z.string()),
    expiry_status: z.string(),
    days_remaining: z.number().nullable().optional(),
    created_at: z.string().optional()
  }).nullable().optional(),
  passport: PassportSchema
});

export const ScanSchema = NestedScanSchema.transform((scan) => ({
  id: scan.id,
  image_url: scan.image_url
    ? new URL(scan.image_url, apiClient.defaults.baseURL).toString()
    : null,
  food_type: scan.food_label ?? (scan.vision?.food_type === "unknown" ? null : scan.vision?.food_type ?? null),
  freshness: scan.assessment?.freshness ?? scan.vision?.freshness ?? null,
  freshness_label: scan.assessment?.freshness ?? scan.vision?.freshness ?? null,
  confidence: scan.assessment?.confidence ?? null,
  model_score: scan.vision?.confidence ?? null,
  model_type: scan.vision?.model_type ?? null,
  confidence_kind: scan.vision?.confidence_kind ?? null,
  visual_evidence: scan.vision?.visual_evidence ?? {},
  expiry_date: scan.ocr?.expiry_date ?? null,
  shelf_life_days: scan.assessment?.days_remaining ?? null,
  voc_index: scan.sensor?.gas_value ?? null,
  temperature_c: scan.sensor?.temperature ?? null,
  humidity_pct: scan.sensor?.humidity ?? null,
  recommendation: scan.assessment?.recommendation ?? null,
  sources: scan.assessment?.modalities_used ?? [],
  warnings: scan.assessment?.warnings ?? [],
  notes: scan.notes ?? null,
  created_at: scan.created_at,
  passport: scan.passport
}));
export type Scan = z.infer<typeof ScanSchema>;

const ScanListSchema = z.array(ScanSchema);

/* ---------- Queries ---------- */

export function useMe(): UseQueryResult<User | null, Error> {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      try {
        const res = await apiClient.get("/auth/me");
        return UserSchema.parse(res.data);
      } catch (err) {
        // 401 -> not logged in; return null instead of throwing so
        // ProtectedRoute can redirect cleanly.
        if (
          err &&
          typeof err === "object" &&
          "response" in err &&
          (err as { response?: { status?: number } }).response?.status === 401
        ) {
          return null;
        }
        throw err;
      }
    },
    retry: false,
    staleTime: 60_000
  });
}

export function useScans(): UseQueryResult<Scan[], Error> {
  return useQuery({
    queryKey: ["scans"],
    queryFn: async () => {
      const res = await apiClient.get("/scans");
      const data = Array.isArray(res.data)
        ? res.data
        : (res.data?.items ?? res.data?.scans ?? []);
      return ScanListSchema.parse(data);
    }
  });
}

export function useScan(id: string | undefined): UseQueryResult<Scan, Error> {
  return useQuery({
    queryKey: ["scan", id],
    queryFn: async () => {
      const res = await apiClient.get(`/scans/${id}`);
      return ScanSchema.parse(res.data);
    },
    enabled: Boolean(id)
  });
}

/* ---------- Mutations ---------- */

interface LoginInput {
  email: string;
  password: string;
}

export function useLogin(): UseMutationResult<AuthResponse, Error, LoginInput> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: LoginInput) => {
      const res = await apiClient.post("/auth/login", input);
      return AuthResponseSchema.parse(res.data);
    },
    onSuccess: (data) => {
      setToken(data.access_token);
      if (data.user) qc.setQueryData(["me"], data.user);
      else void qc.invalidateQueries({ queryKey: ["me"] });
    }
  });
}

interface RegisterInput {
  name: string;
  email: string;
  password: string;
}

export function useRegister(): UseMutationResult<AuthResponse, Error, RegisterInput> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: RegisterInput) => {
      const res = await apiClient.post("/auth/register", input);
      return AuthResponseSchema.parse(res.data);
    },
    onSuccess: (data) => {
      setToken(data.access_token);
      if (data.user) qc.setQueryData(["me"], data.user);
      else void qc.invalidateQueries({ queryKey: ["me"] });
    }
  });
}

export interface CreateScanInput {
  image: File;
  food_type?: string;
  temperature_c?: number;
  humidity_pct?: number;
  voc_index?: number;
  notes?: string;
}

export function useCreateScan(): UseMutationResult<Scan, Error, CreateScanInput> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateScanInput) => {
      const form = new FormData();
      form.append("file", input.image, input.image.name || "capture.jpg");
      if (input.food_type) form.append("food_type", input.food_type);
      if (input.temperature_c !== undefined)
        form.append("temperature_c", String(input.temperature_c));
      if (input.humidity_pct !== undefined)
        form.append("humidity_pct", String(input.humidity_pct));
      if (input.voc_index !== undefined)
        form.append("voc_index", String(input.voc_index));
      if (input.notes) form.append("notes", input.notes);
      const res = await apiClient.post("/scans", form);
      return ScanSchema.parse(res.data);
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["scans"] });
    }
  });
}
