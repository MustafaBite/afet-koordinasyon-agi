import { View, Text, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import MapView, { Marker, PROVIDER_GOOGLE } from "react-native-maps";
import { Platform } from "react-native";
import { ScreenHeader } from "@/src/components/ui";
import { useClusters } from "@/src/hooks/useClusters";
import { useVehicles } from "@/src/hooks/useVehicles";

export default function MapScreen() {
  const { data: clusters, isLoading: loadingClusters } = useClusters();
  const { data: vehicles, isLoading: loadingVehicles } = useVehicles();

  const getClusterColor = (priority: string) => {
    switch (priority) {
      case "critical": return "#EF4444"; // Red
      case "high": return "#F97316"; // Orange
      case "medium": return "#EAB308"; // Yellow
      case "low": return "#3B82F6"; // Blue
      default: return "#6B7280";
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-surface-card">
      <ScreenHeader
        title="Saha Haritası"
        subtitle="Afet kümeleri ve araç konumları"
      />
      <View className="flex-1 relative">
        {loadingClusters || loadingVehicles ? (
          <View className="flex-1 items-center justify-center">
            <ActivityIndicator size="large" color="#E63946" />
          </View>
        ) : (
          <MapView
            style={{ flex: 1 }}
            provider={Platform.OS === "android" ? PROVIDER_GOOGLE : undefined}
            initialRegion={{
              latitude: 37.0660,
              longitude: 37.3781, // Defaulting to Gaziantep for demo
              latitudeDelta: 0.5,
              longitudeDelta: 0.5,
            }}
          >
            {/* Render Clusters */}
            {clusters?.filter(c => c.status !== "resolved").map((cluster) => (
              <Marker
                key={cluster.cluster_id}
                coordinate={{
                  latitude: cluster.center_latitude,
                  longitude: cluster.center_longitude,
                }}
                title={cluster.cluster_name}
                description={`${cluster.total_persons_affected} Kişi | İhtiyaç: ${cluster.need_type} | Öncelik: ${cluster.priority_level}`}
                pinColor={getClusterColor(cluster.priority_level)}
              />
            ))}

            {/* Render Vehicles */}
            {vehicles?.filter(v => v.vehicle_status === "available" || v.vehicle_status === "en_route").map((vehicle) => (
              <Marker
                key={vehicle.id}
                coordinate={{
                  latitude: vehicle.latitude,
                  longitude: vehicle.longitude,
                }}
                title={`${vehicle.vehicle_type} (${vehicle.vehicle_status})`}
                description={`Kapasite: ${vehicle.capacity}`}
                pinColor={vehicle.vehicle_status === "en_route" ? "indigo" : "cyan"}
              />
            ))}
          </MapView>
        )}
        
        {/* Overlay Legend */}
        <View className="absolute bottom-6 left-4 right-4 bg-white/90 p-3 rounded-card shadow-sm border border-border">
          <Text className="text-xs font-bold text-text-primary uppercase mb-2">Harita Lejandı</Text>
          <View className="flex-row justify-between">
            <View className="flex-row items-center gap-2">
              <View className="w-3 h-3 rounded-full bg-[#EF4444]" />
              <Text className="text-xs text-text-secondary">Kritik Küme</Text>
            </View>
            <View className="flex-row items-center gap-2">
              <View className="w-3 h-3 rounded-full bg-[#EAB308]" />
              <Text className="text-xs text-text-secondary">Orta/Düşük</Text>
            </View>
            <View className="flex-row items-center gap-2">
              <View className="w-3 h-3 rounded-full bg-cyan-500" />
              <Text className="text-xs text-text-secondary">Araçlar</Text>
            </View>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}
