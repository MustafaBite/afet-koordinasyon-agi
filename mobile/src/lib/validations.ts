import { z } from "zod";

// ─── Auth Schemas ──────────────────────────────────────────────────────────

export const loginSchema = z.object({
  email: z.string().email("Geçerli bir e-posta girin"),
  password: z.string().min(6, "Şifre en az 6 karakter olmalı"),
});

export type LoginFormData = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  email: z.string().email("Geçerli bir e-posta girin"),
  password: z
    .string()
    .min(8, "Şifre en az 8 karakter olmalı")
    .regex(/[A-Z]/, "En az bir büyük harf içermeli")
    .regex(/[0-9]/, "En az bir rakam içermeli"),
  first_name: z.string().min(2, "İsim en az 2 karakter olmalı"),
  last_name: z.string().min(2, "Soyisim en az 2 karakter olmalı"),
  tc_identity_no: z
    .string()
    .length(11, "T.C. Kimlik No 11 hane olmalı")
    .regex(/^\d+$/, "Sadece rakam girilmelidir"),
  phone: z
    .string()
    .min(10, "Geçerli bir telefon numarası girin")
    .regex(/^0?5\d{9}$/, "Geçerli bir Türk telefon numarası girin"),
  city: z.string().min(2, "Şehir seçin"),
  district: z.string().min(2, "İlçe seçin"),
  expertise_area: z.string().optional(),
  organization: z.string().optional(),
  profile_photo_url: z.string().optional(),
});

export type RegisterFormData = z.infer<typeof registerSchema>;

// ─── Request / İhbar Schemas ───────────────────────────────────────────────

export const NEED_TYPES = [
  "rescue",
  "medical",
  "food",
  "water",
  "shelter",
  "heating",
  "clothing",
  "hygiene",
  "other",
] as const;

export const createRequestSchema = z.object({
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  need_type: z.enum(NEED_TYPES),
  person_count: z
    .number()
    .int("Tam sayı girilmelidir")
    .min(1, "En az 1 kişi olmalı")
    .max(9999, "En fazla 9999 kişi olabilir"),
  description: z.string().optional(),
});

export type CreateRequestFormData = z.infer<typeof createRequestSchema>;

export const personCountSchema = z
  .number()
  .int("Tam sayı girilmelidir")
  .min(1, "En az 1 kişi olmalı")
  .max(9999, "En fazla 9999 kişi olabilir");
