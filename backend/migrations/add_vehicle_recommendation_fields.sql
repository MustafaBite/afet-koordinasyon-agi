-- Araç önerisi için gerekli alanları ekle
-- relief_vehicles tablosuna yeni kolonlar

ALTER TABLE relief_vehicles 
ADD COLUMN IF NOT EXISTS plate_number VARCHAR(20),
ADD COLUMN IF NOT EXISTS base_speed_kmh INTEGER DEFAULT 60,
ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

-- İndeks ekle (performans için)
CREATE INDEX IF NOT EXISTS idx_vehicles_team ON relief_vehicles(team_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_location ON relief_vehicles(latitude, longitude);

-- Mevcut araçlara varsayılan hız değerleri ata (araç tipine göre)
UPDATE relief_vehicles 
SET base_speed_kmh = CASE 
    WHEN vehicle_type ILIKE '%ambulans%' THEN 70
    WHEN vehicle_type ILIKE '%kamyon%' THEN 60
    WHEN vehicle_type ILIKE '%itfaiye%' THEN 65
    WHEN vehicle_type ILIKE '%tanker%' THEN 55
    WHEN vehicle_type ILIKE '%makine%' THEN 30
    ELSE 60
END
WHERE base_speed_kmh IS NULL;

-- Örnek plaka numaraları ekle (test için)
-- ROW_NUMBER() UPDATE'te çalışmadığı için WITH kullanıyoruz
WITH numbered_vehicles AS (
    SELECT id, ROW_NUMBER() OVER() as rn
    FROM relief_vehicles
    WHERE plate_number IS NULL
)
UPDATE relief_vehicles
SET plate_number = '34 ' || LPAD(nv.rn::TEXT, 5, '0')
FROM numbered_vehicles nv
WHERE relief_vehicles.id = nv.id;

COMMENT ON COLUMN relief_vehicles.plate_number IS 'Araç plaka numarası (örn: 34 ABC 12)';
COMMENT ON COLUMN relief_vehicles.base_speed_kmh IS 'Aracın standart hızı (km/saat)';
COMMENT ON COLUMN relief_vehicles.team_id IS 'Aracın bağlı olduğu takım';
