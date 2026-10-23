import {
  useInfiniteQuery,
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
  key: z.enum(["vision", "product", "expiry", "sensor"]),
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

const PassportConflictSchema = z.object({
  key: z.enum(["vision_sensor", "vision_expiry"]),
  title: z.string(),
  detail: z.string()
});

const PassportSchema = z.object({
  summary: z.string(),
  explanation: z.string(),
  evidence: z.array(PassportEvidenceSchema),
  timeline: z.array(PassportEventSchema),
  conflicts: z.array(PassportConflictSchema).optional().default([]),
  limitations: z.array(z.string())
});

const NestedScanSchema = z.object({
  id: z.union([z.string(), z.number()]),
  tracked_item_id: z.string().nullable().optional(),
  tracked_item_label: z.string().nullable().optional(),
  image_url: z.string().optional().nullable(),
  food_label: z.string().optional().nullable(),
  product: z.object({
    category: z.string().nullable().optional(),
    product_name: z.string().nullable().optional(),
    confidence: z.number().nullable().optional(),
    evidence: z.array(z.string()).optional().default([]),
    source: z.enum(["package_text", "user_label", "unrecognized"]).optional().default("unrecognized")
  }).optional(),
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
    provider: z.string().optional(),
    confidence: z.number().nullable().optional(),
    expiry_label: z.string().nullable().optional(),
    expiry_text: z.string().nullable().optional(),
    created_at: z.string().optional()
  }).nullable().optional(),
  sensor: z.object({
    gas_value: z.number().nullable().optional(),
    temperature: z.number().nullable().optional(),
    humidity: z.number().nullable().optional(),
    source: z.enum(["user_entered", "demo_estimate", "mixed", "legacy"]).optional().default("legacy"),
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
  tracked_item_id: scan.tracked_item_id ?? null,
  tracked_item_label: scan.tracked_item_label ?? null,
  image_url: scan.image_url
    ? new URL(scan.image_url, apiClient.defaults.baseURL).toString()
    : null,
  food_type: scan.product?.category ?? scan.food_label ?? (scan.vision?.food_type === "unknown" ? null : scan.vision?.food_type ?? null),
  product: scan.product ?? { category: null, product_name: null, confidence: null, evidence: [], source: "unrecognized" as const },
  freshness: scan.assessment?.freshness ?? scan.vision?.freshness ?? null,
  freshness_label: scan.assessment?.freshness ?? scan.vision?.freshness ?? null,
  confidence: scan.assessment?.confidence ?? null,
  model_score: scan.vision?.confidence ?? null,
  model_type: scan.vision?.model_type ?? null,
  confidence_kind: scan.vision?.confidence_kind ?? null,
  visual_evidence: scan.vision?.visual_evidence ?? {},
  expiry_date: scan.ocr?.expiry_date ?? null,
  expiry_label: scan.ocr?.expiry_label ?? null,
  expiry_text: scan.ocr?.expiry_text ?? null,
  ocr_text: scan.ocr?.raw_text ?? "",
  ocr_provider: scan.ocr?.provider ?? "unknown",
  ocr_confidence: scan.ocr?.confidence ?? null,
  shelf_life_days: scan.assessment?.days_remaining ?? null,
  voc_index: scan.sensor?.gas_value ?? null,
  temperature_c: scan.sensor?.temperature ?? null,
  humidity_pct: scan.sensor?.humidity ?? null,
  sensor_source: scan.sensor?.source ?? "legacy",
  recommendation: scan.assessment?.recommendation ?? null,
  sources: scan.assessment?.modalities_used ?? [],
  warnings: scan.assessment?.warnings ?? [],
  notes: scan.notes ?? null,
  created_at: scan.created_at,
  passport: scan.passport
}));
export type Scan = z.infer<typeof ScanSchema>;

const ScanListSchema = z.array(ScanSchema);
const ScanPageSchema = z.object({
  items: ScanListSchema,
  total: z.number(),
  limit: z.number(),
  offset: z.number()
});

export const TrackedItemSchema = z.object({
  id: z.string(),
  label: z.string(),
  scan_count: z.number(),
  last_scanned: z.string()
});
export type TrackedItem = z.infer<typeof TrackedItemSchema>;

const TrackedItemDetailSchema = z.object({
  id: z.string(),
  label: z.string(),
  scans: ScanListSchema
});

export const InventoryItemSchema = z.object({
  id: z.string(),
  product_name: z.string(),
  category: z.string().nullable(),
  quantity: z.number(),
  expiry_date: z.string().nullable(),
  expiry_source: z.enum(["ocr_confirmed", "user_entered", "unknown"]),
  days_remaining: z.number().nullable(),
  status: z.enum(["expired", "urgent", "soon", "stored", "unknown"]),
  source_scan_id: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string()
});
export type InventoryItem = z.infer<typeof InventoryItemSchema>;

export interface CreateInventoryInput {
  product_name: string;
  category?: string;
  quantity: number;
  expiry_date?: string;
  expiry_source: "ocr_confirmed" | "user_entered" | "unknown";
  source_scan_id?: string;
}

export type UpdateInventoryInput = Partial<Pick<CreateInventoryInput, "product_name" | "category" | "quantity" | "expiry_source">> & { expiry_date?: string | null };

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

export function useScans() {
  return useInfiniteQuery({
    queryKey: ["scans"],
    initialPageParam: 0,
    queryFn: async ({ pageParam }) => {
      const res = await apiClient.get("/scans", { params: { limit: 20, offset: pageParam } });
      const items = ScanListSchema.parse(res.data);
      return ScanPageSchema.parse({
        items,
        total: Number(res.headers["x-total-count"] ?? items.length + pageParam),
        limit: 20,
        offset: pageParam
      });
    },
    getNextPageParam: (lastPage) =>
      lastPage.offset + lastPage.items.length < lastPage.total
        ? lastPage.offset + lastPage.limit
        : undefined
  });
}

export function useTrackedItems(): UseQueryResult<TrackedItem[], Error> {
  return useQuery({
    queryKey: ["tracked-items"],
    queryFn: async () => {
      const res = await apiClient.get("/scans/items");
      return z.array(TrackedItemSchema).parse(res.data);
    }
  });
}

export function useTrackedItem(id: string | undefined) {
  return useQuery({
    queryKey: ["tracked-item", id],
    queryFn: async () => {
      const res = await apiClient.get(`/scans/items/${id}`);
      return TrackedItemDetailSchema.parse(res.data);
    },
    enabled: Boolean(id)
  });
}

export function useInventory() {
  return useQuery({
    queryKey: ["inventory"],
    queryFn: async () => {
      const res = await apiClient.get("/inventory");
      return z.array(InventoryItemSchema).parse(res.data);
    }
  });
}

export function useCreateInventoryItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateInventoryInput) => {
      const res = await apiClient.post("/inventory", input);
      return InventoryItemSchema.parse(res.data);
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["inventory"] });
      void qc.invalidateQueries({ queryKey: ["scans"] });
    }
  });
}

export function useUpdateInventoryItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...input }: UpdateInventoryInput & { id: string }) => {
      const res = await apiClient.patch(`/inventory/${id}`, input);
      return InventoryItemSchema.parse(res.data);
    },
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["inventory"] })
  });
}

export function useDeleteInventoryItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/inventory/${id}`);
    },
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["inventory"] })
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
  tracked_item_id?: string;
  new_item_name?: string;
  food_type?: string;
  temperature_c?: number;
  humidity_pct?: number;
  voc_index?: number;
  sensor_source?: "user_entered" | "demo_estimate" | "mixed";
  notes?: string;
}

export function useCreateScan(): UseMutationResult<Scan, Error, CreateScanInput> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateScanInput) => {
      const form = new FormData();
      form.append("file", input.image, input.image.name || "capture.jpg");
      if (input.tracked_item_id) form.append("tracked_item_id", input.tracked_item_id);
      if (input.new_item_name) form.append("new_item_name", input.new_item_name);
      if (input.food_type) form.append("food_type", input.food_type);
      if (input.temperature_c !== undefined)
        form.append("temperature_c", String(input.temperature_c));
      if (input.humidity_pct !== undefined)
        form.append("humidity_pct", String(input.humidity_pct));
      if (input.voc_index !== undefined)
        form.append("voc_index", String(input.voc_index));
      if (input.sensor_source) form.append("sensor_source", input.sensor_source);
      if (input.notes) form.append("notes", input.notes);
      const res = await apiClient.post("/scans", form);
      return ScanSchema.parse(res.data);
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["scans"] });
      void qc.invalidateQueries({ queryKey: ["tracked-items"] });
      void qc.invalidateQueries({ queryKey: ["tracked-item"] });
    }
  });
}

export function useReanalyzeScan(id: string): UseMutationResult<Scan, Error, void> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const res = await apiClient.post(`/scans/${id}/reanalyze`, undefined, { timeout: 180000 });
      return ScanSchema.parse(res.data);
    },
    onSuccess: (scan) => {
      qc.setQueryData(["scan", id], scan);
      void qc.invalidateQueries({ queryKey: ["scans"] });
      void qc.invalidateQueries({ queryKey: ["tracked-items"] });
      void qc.invalidateQueries({ queryKey: ["tracked-item"] });
    }
  });
}
