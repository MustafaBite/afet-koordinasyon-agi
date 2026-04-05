"""
WebSocket bağlantı yönetimi
"""
from fastapi import WebSocket


class ConnectionManager:
    """
    WebSocket bağlantılarını yöneten sınıf
    Gerçek zamanlı bildirimler için kullanılır
    """
    
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        """
        Yeni WebSocket bağlantısı ekle
        
        Args:
            websocket: WebSocket bağlantısı
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"BAĞLANTI EKLENDİ: {len(self.active_connections)} aktif bağlantı")

    def disconnect(self, websocket: WebSocket):
        """
        WebSocket bağlantısını kaldır
        
        Args:
            websocket: Kapatılacak WebSocket bağlantısı
        """
        self.active_connections.remove(websocket)
        print(f"BAĞLANTI KOPARILDI: {len(self.active_connections)} aktif bağlantı")

    async def broadcast(self, message: dict):
        """
        Tüm bağlı kullanıcılara mesaj gönder
        
        Args:
            message: Gönderilecek JSON mesajı
        """
        print(f"BROADCAST: {len(self.active_connections)} bağlantıya gönderiliyor")
        for connection in self.active_connections:
            await connection.send_json(message)
