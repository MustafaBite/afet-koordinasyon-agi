# Öncelik Puanlama Motoru (Priority Engine)
# Gelen afet taleplerini need_type alanına göre aciliyet puanı verir.

ONCELIK_PUANLARI = {
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

VARSAYILAN_PUAN = 50  # Bilinmeyen kategoriler için

def oncelik_puani_hesapla(need_type: str) -> int:
    """
    Verilen need_type için öncelik puanını döndürür(Şuanlık sadece need_type kullanılıyor. İleride konum, zaman vb. eklenecek.).
    Bilinmeyen kategoriler varsayılan 50 puan alır.
    """
    return ONCELIK_PUANLARI.get(need_type.lower(), VARSAYILAN_PUAN)
