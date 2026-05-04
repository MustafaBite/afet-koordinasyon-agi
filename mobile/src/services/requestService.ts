import { api, API_URL, TOKEN_KEY, AppError } from "./api";
import * as SecureStore from "expo-secure-store";
import type { CreateRequestBody, DisasterRequest } from "@/src/types";

/**
 * Backend mount: `app.include_router(requests_router.router, prefix="/api/ihbarlar")`.
 * Mevcut endpoints:
 *   POST   /api/ihbarlar              create
 *   GET    /api/ihbarlar/prioritized  tum talepler (oncelik sirali)
 *   PATCH  /api/ihbarlar/{id}/status  durum guncelle
 *   GET    /api/ihbarlar/dogrulanmamis
 *   GET    /api/ihbarlar/istatistikler
 *
 * NOT: Backend'de su an "GET /api/ihbarlar" (list) ve "GET /api/ihbarlar/{id}" (detail)
 * endpoint'leri yok. Mobil tarafta `prioritized` listesini cekip client-side filter yapiyoruz.
 * Photo upload endpoint'i de henuz yok; gracefully no-op donduruyoruz.
 */

const BASE = "/api/ihbarlar";

export const requestService = {
  async create(data: CreateRequestBody): Promise<DisasterRequest> {
    const response = await api.post<DisasterRequest>(BASE, data);
    return response.data;
  },

  /** Giriş yapan kullanıcıya ait talepleri döndürür (GET /api/ihbarlar/mine). */
  async getMyRequests(): Promise<DisasterRequest[]> {
    const response = await api.get<DisasterRequest[]>(`${BASE}/mine`);
    return response.data;
  },

  /**
   * Backend `GET /api/ihbarlar` yok; `prioritized` endpoint'inden tum
   * talepleri cekiyoruz. Bu listede dynamic_priority_score var ama
   * DisasterRequest interface'i icin gereksiz alani yok sayiyoruz.
   */
  async getAll(): Promise<DisasterRequest[]> {
    const response = await api.get<DisasterRequest[]>(`${BASE}/prioritized`);
    return response.data;
  },

  async getPrioritized(): Promise<DisasterRequest[]> {
    const response = await api.get<DisasterRequest[]>(`${BASE}/prioritized`);
    return response.data;
  },

  /**
   * Backend'de detail endpoint'i yok; listeden filtreleyerek bulan
   * client-side fallback. Bulunamazsa 404 firlatir.
   */
  async getById(id: string): Promise<DisasterRequest> {
    const all = await this.getAll();
    const found = all.find((r) => r.id === id);
    if (!found) {
      throw new AppError("Talep bulunamadı", 404);
    }
    return found;
  },

  /**
   * Bir ihbara ait fotoğraf veya ses dosyasını backend'e yükler.
   * Backend dosyayı Supabase Storage'a aktarır ve public URL döndürür.
   * Hata durumunda yerel URI'yi olduğu gibi döndürür — UI akışı kesilmez.
   */
  async uploadPhoto(requestId: string, fileUri: string, mimeType = "image/jpeg"): Promise<string> {
    try {
      const token = await SecureStore.getItemAsync(TOKEN_KEY);

      const formData = new FormData();
      // React Native FormData blob ek — expo-file-system olmadan çalışır
      formData.append("files", {
        uri: fileUri,
        name: fileUri.split("/").pop() ?? "upload",
        type: mimeType,
      } as unknown as Blob);

      const res = await fetch(`${API_URL}${BASE}/${requestId}/photos`, {
        method: "POST",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          // Content-Type'ı açıkça set etme — fetch multipart boundary'yi otomatik ekler
        },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        if (__DEV__) console.warn("[requestService] uploadPhoto error:", err);
        return fileUri;
      }

      const data = await res.json();
      // Ses dosyası ise audio_url, fotoğrafsa son eklenen photo_url döner
      const urls: string[] = data.photo_urls ?? [];
      return data.audio_url ?? (urls[urls.length - 1] ?? fileUri);
    } catch (err) {
      if (__DEV__) console.warn("[requestService] uploadPhoto exception:", err);
      return fileUri;
    }
  },

  /** Birden fazla medya dosyasını tek seferde yükler; tüm public URL'leri döndürür. */
  async uploadFiles(
    requestId: string,
    files: { uri: string; mimeType: string }[]
  ): Promise<{ photo_urls: string[]; audio_url: string | null }> {
    try {
      const token = await SecureStore.getItemAsync(TOKEN_KEY);

      const formData = new FormData();
      for (const f of files) {
        formData.append("files", {
          uri: f.uri,
          name: f.uri.split("/").pop() ?? "upload",
          type: f.mimeType,
        } as unknown as Blob);
      }

      const res = await fetch(`${API_URL}${BASE}/${requestId}/photos`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      if (!res.ok) return { photo_urls: [], audio_url: null };
      return res.json();
    } catch {
      return { photo_urls: [], audio_url: null };
    }
  },
};
