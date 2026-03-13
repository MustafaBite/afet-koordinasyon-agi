# Öncelik Puanlama Motoru (Priority Engine)
# Gelen afet taleplerini need_type alanına göre aciliyet puanı verir.

PRIORITY_SCORES = {
    "medikal":          90,  # Kanamalı yaralı, tıbbi müdahale
    "arama_kurtarma":  100,  # Enkaz altında kalan kişiler
    "enkaz":            95,  # Bina çökmesi, yapısal hasar
    "yangin":           85,  # Aktif yangın tehlikesi
    "barinma":          60,  # Çadır / hipotermi riski
    "su":               50,  # Temiz su ihtiyacı
    "gida":             40,  # Gıda / yemek ihtiyacı
    "ulasim":           30,  # Ulaşım desteği
    "is_makinesi":      75,  # İş makinesi talebi (enkaz kaldırma vb.)
}

DEFAULT_SCORE = 50  # Bilinmeyen kategoriler için

def calculate_priority_score(need_type: str) -> int:
    """
    Verilen need_type için öncelik puanını döndürür.
    Şuanlık sadece need_type kullanılıyor. İleride konum, zaman vb. eklenecek.
    Bilinmeyen kategoriler varsayılan 50 puan alır.
    """
    return PRIORITY_SCORES.get(need_type.lower(), DEFAULT_SCORE)
