-- Migration: Araçlara base_speed_kmh alanı ekleme
-- ETA (Tahmini Varış Süresi) hesaplaması için gerekli

-- Yeni kolon ekle
ALTER TABLE relief_vehicles 
ADD COLUMN IF NOT EXISTS base_speed_kmh INTEGER DEFAULT 60;

-- Mevcut araçlar için araç tipine göre hız ata
UPDATE relief_vehicles 
SET base_speed_kmh = CASE 
    WHEN vehicle_type = 'Ambulans' THEN 70
    WHEN vehicle_type = 'Kamyon' THEN 60
    WHEN vehicle_type = 'İtfaiye' THEN 65
    WHEN vehicle_type = 'Su Tankeri' THEN 55
    WHEN vehicle_type = 'İş Makinesi' THEN 30
    ELSE 60
END
WHERE base_speed_kmh IS NULL OR base_speed_kmh = 60;

-- Kolon açıklaması ekle
COMMENT ON COLUMN relief_vehicles.base_speed_kmh IS 'Aracın ortalama hızı (km/saat) - ETA hesaplaması için kullanılır';
