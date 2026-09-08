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

export const ScanSchema = z.object({
  id: z.union([z.string(), z.number()]),
  image_url: z.string().optional().nullable(),
  food_type: z.string().optional().nullable(),
  freshness: z.string().optional().nullable(),
  freshness_label: z.string().optional().nullable(),
  confidence: z.number().optional().nullable(),
  expiry_date: z.string().optional().nullable(),
  shelf_life_days: z.number().optional().nullable(),
  voc_index: z.number().optional().nullable(),
  temperature_c: z.number().optional().nullable(),
  humidity_pct: z.number().optional().nullable(),
  recommendation: z.string().optional().nullable(),
  sources: z.array(z.string()).optional().nullable(),
  warnings: z.array(z.string()).optional().nullable(),
  created_at: z.string().optional().nullable()
});
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
      form.append("image", input.image, input.image.name || "capture.jpg");
      if (input.food_type) form.append("food_type", input.food_type);
      if (input.temperature_c !== undefined)
        form.append("temperature_c", String(input.temperature_c));
      if (input.humidity_pct !== undefined)
        form.append("humidity_pct", String(input.humidity_pct));
      if (input.voc_index !== undefined)
        form.append("voc_index", String(input.voc_index));
      if (input.notes) form.append("notes", input.notes);
      const res = await apiClient.post("/scans", form, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      return ScanSchema.parse(res.data);
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["scans"] });
    }
  });
}
