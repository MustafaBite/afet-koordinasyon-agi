"""
Dinamik Önceliklendirme Servisi
Zaman sönümleme (Time Decay / DPS) formülü ile öncelik hesaplama
"""
import math
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# 1) Statik Taban Puanları (S_base) — 0-100 arası (Aciliyet başlangıç değeri)
# ---------------------------------------------------------------------------
BASE_SCORES = {
    "arama_kurtarma": 100,
    "medikal":         95,
    "yangin":          90,
    "enkaz":           80,
    "su":              60,
    "barinma":         50,
    "gida":            40,
    "is_makinesi":     35,
    "ulasim":          25,
}

# ---------------------------------------------------------------------------
# 2) Ağırlık Katsayıları (C_i) — Sistemin genelindeki etki katsayısı
# ---------------------------------------------------------------------------
WEIGHT_COEFFICIENTS = {
    "arama_kurtarma": 0.25,
    "medikal":        0.20,
    "yangin":         0.15,
    "enkaz":          0.12,
    "su":             0.09,
    "barinma":        0.07,
    "gida":           0.06,
    "is_makinesi":    0.04,
    "ulasim":         0.02,
}

# ---------------------------------------------------------------------------
# 3) Maksimum Tolerans Süreleri (M) — saat cinsinden
# ---------------------------------------------------------------------------
MAX_TOLERANCE_HOURS = {
    "arama_kurtarma": 6,
    "medikal":        2,
    "yangin":         1,
    "enkaz":          12,
    "su":             72,    # Dehidrasyon (~3 gün)
    "barinma":        48,
    "gida":           168,   # Açlık (~7 gün)
    "is_makinesi":    24,
    "ulasim":         24,
}

TIME_SENSITIVITY_LAMBDA = 1.5
DEFAULT_BASE_SCORE = 50
DEFAULT_WEIGHT = 0.05
DEFAULT_MAX_TOLERANCE = 24


def calculate_dynamic_priority(need_type: str, created_at: datetime) -> float:
    """
    Zaman sönümleme (Time Decay / DPS) formülü ile dinamik öncelik puanını hesaplar.
    
    Formül: P_dynamic(t) = S_base + (S_base * λ * (t / M)) * (1 + C_i)
    
    Kuyruk açlığını (queue starvation) önlemek için bekleyen ihbarların puanını zamanla artırır.
    
    Args:
        need_type: İhtiyaç tipi (arama_kurtarma, medikal, vb.)
        created_at: İhbar oluşturulma zamanı
    
    Returns:
        Dinamik öncelik puanı (0-100 arası)
    """
    need = need_type.lower()
    base_score = BASE_SCORES.get(need, DEFAULT_BASE_SCORE)
    weight = WEIGHT_COEFFICIENTS.get(need, DEFAULT_WEIGHT)
    max_tolerance = MAX_TOLERANCE_HOURS.get(need, DEFAULT_MAX_TOLERANCE)

    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    wait_seconds = (now - created_at).total_seconds()
    wait_hours = max(wait_seconds / 3600, 0)

    time_ratio = wait_hours / max_tolerance
    time_bonus = (base_score * TIME_SENSITIVITY_LAMBDA * time_ratio) * (1 + weight)

    # Arka plan tavan puan sınırı (1000)
    MAX_POSSIBLE_SCORE = 1000.0
    raw_score = min(base_score + time_bonus, MAX_POSSIBLE_SCORE)
    
    # Kullanıcıya (Frontend) 100 üzerinden %'lik skor dön (0-100 skalası)
    scaled_score = (raw_score / MAX_POSSIBLE_SCORE) * 100.0
    
    return round(scaled_score, 1)
