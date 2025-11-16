# WebSocket Client Implementation Guide

Bu dokümantasyon, mobil uygulama için WebSocket client implementasyonu rehberidir.

## Bağlantı Kurma

```typescript
import io from "socket.io-client";

const socket = io("ws://localhost:8000/api/v1/ws", {
  auth: {
    token: "JWT_TOKEN_HERE",
  },
  query: {
    room: "hotel_1_drivers",
  },
  transports: ["websocket"],
});
```

## Reconnection Handling (Görev 10.4)

### Otomatik Yeniden Bağlanma

WebSocket bağlantısı kesildiğinde otomatik olarak yeniden bağlanma:

```typescript
class WebSocketService {
  private socket: any = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000; // 1 saniye başlangıç

  connect(url: string, token: string, room: string) {
    this.socket = io(url, {
      auth: { token },
      query: { room },
      transports: ["websocket"],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
      reconnectionDelayMax: 10000, // Max 10 saniye
      timeout: 20000,
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers() {
    // Bağlantı kuruldu
    this.socket.on("connect", () => {
      console.log("✅ WebSocket bağlandı");
      this.reconnectAttempts = 0;
      this.onConnected();
    });

    // Bağlantı kesildi
    this.socket.on("disconnect", (reason: string) => {
      console.log("🔌 WebSocket bağlantısı kesildi:", reason);
      this.onDisconnected(reason);
    });

    // Yeniden bağlanma denemesi
    this.socket.on("reconnect_attempt", (attemptNumber: number) => {
      console.log(`🔄 Yeniden bağlanma denemesi: ${attemptNumber}`);
      this.reconnectAttempts = attemptNumber;
    });

    // Yeniden bağlandı
    this.socket.on("reconnect", (attemptNumber: number) => {
      console.log(`✅ Yeniden bağlandı (${attemptNumber} deneme sonrası)`);
      this.onReconnected();
    });

    // Yeniden bağlanma başarısız
    this.socket.on("reconnect_failed", () => {
      console.log("❌ Yeniden bağlanma başarısız");
      this.onReconnectFailed();
    });

    // Hata
    this.socket.on("error", (error: any) => {
      console.error("❌ WebSocket hatası:", error);
    });
  }

  private onConnected() {
    // UI'da bağlantı durumunu güncelle
    // Gerekirse room'a yeniden katıl
  }

  private onDisconnected(reason: string) {
    // UI'da bağlantı durumunu güncelle
    // Kullanıcıya bilgi göster
  }

  private onReconnected() {
    // UI'da bağlantı durumunu güncelle
    // Kaçırılan verileri senkronize et
  }

  private onReconnectFailed() {
    // Kullanıcıya hata mesajı göster
    // Manuel yeniden bağlanma seçeneği sun
  }
}
```

### Exponential Backoff Strategy

Yeniden bağlanma denemeleri arasındaki süreyi artırarak sunucuya yük bindirmemek:

```typescript
class WebSocketService {
  private calculateReconnectDelay(attemptNumber: number): number {
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, max 30s
    const delay = Math.min(1000 * Math.pow(2, attemptNumber), 30000);

    // Jitter ekle (rastgele gecikme)
    const jitter = Math.random() * 1000;

    return delay + jitter;
  }

  private manualReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log("❌ Maksimum yeniden bağlanma denemesi aşıldı");
      return;
    }

    const delay = this.calculateReconnectDelay(this.reconnectAttempts);

    console.log(`🔄 ${delay}ms sonra yeniden bağlanılacak...`);

    setTimeout(() => {
      this.reconnectAttempts++;
      this.socket.connect();
    }, delay);
  }
}
```

### Connection Status Indicator

UI'da bağlantı durumunu gösterme:

```typescript
enum ConnectionStatus {
  CONNECTED = "connected",
  CONNECTING = "connecting",
  DISCONNECTED = "disconnected",
  RECONNECTING = "reconnecting",
  ERROR = "error",
}

class WebSocketService {
  private status: ConnectionStatus = ConnectionStatus.DISCONNECTED;
  private statusCallbacks: ((status: ConnectionStatus) => void)[] = [];

  onStatusChange(callback: (status: ConnectionStatus) => void) {
    this.statusCallbacks.push(callback);
  }

  private setStatus(status: ConnectionStatus) {
    this.status = status;
    this.statusCallbacks.forEach((cb) => cb(status));
  }

  private setupEventHandlers() {
    this.socket.on("connect", () => {
      this.setStatus(ConnectionStatus.CONNECTED);
    });

    this.socket.on("disconnect", () => {
      this.setStatus(ConnectionStatus.DISCONNECTED);
    });

    this.socket.on("reconnect_attempt", () => {
      this.setStatus(ConnectionStatus.RECONNECTING);
    });

    this.socket.on("error", () => {
      this.setStatus(ConnectionStatus.ERROR);
    });
  }
}
```

### React Component Example

```typescript
import React, { useEffect, useState } from "react";
import { View, Text } from "react-native";
import { WebSocketService, ConnectionStatus } from "./services/websocket";

const ConnectionIndicator: React.FC = () => {
  const [status, setStatus] = useState<ConnectionStatus>(
    ConnectionStatus.DISCONNECTED
  );

  useEffect(() => {
    const ws = WebSocketService.getInstance();
    ws.onStatusChange(setStatus);
  }, []);

  const getStatusColor = () => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return "green";
      case ConnectionStatus.CONNECTING:
      case ConnectionStatus.RECONNECTING:
        return "orange";
      case ConnectionStatus.DISCONNECTED:
      case ConnectionStatus.ERROR:
        return "red";
    }
  };

  const getStatusText = () => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return "Bağlı";
      case ConnectionStatus.CONNECTING:
        return "Bağlanıyor...";
      case ConnectionStatus.RECONNECTING:
        return "Yeniden bağlanıyor...";
      case ConnectionStatus.DISCONNECTED:
        return "Bağlantı kesildi";
      case ConnectionStatus.ERROR:
        return "Hata";
    }
  };

  return (
    <View style={{ flexDirection: "row", alignItems: "center" }}>
      <View
        style={{
          width: 10,
          height: 10,
          borderRadius: 5,
          backgroundColor: getStatusColor(),
          marginRight: 5,
        }}
      />
      <Text>{getStatusText()}</Text>
    </View>
  );
};
```

## Event Handling

### Event Listeners

```typescript
class WebSocketService {
  setupEventListeners() {
    // Yeni request
    this.socket.on("new_request", (data: any) => {
      console.log("📞 Yeni request:", data);
      // UI'ı güncelle, notification göster
    });

    // Request kabul edildi
    this.socket.on("request_accepted", (data: any) => {
      console.log("✅ Request kabul edildi:", data);
      // UI'ı güncelle
    });

    // Request tamamlandı
    this.socket.on("request_completed", (data: any) => {
      console.log("🎉 Request tamamlandı:", data);
      // UI'ı güncelle
    });

    // Shuttle durumu değişti
    this.socket.on("shuttle_status_changed", (data: any) => {
      console.log("🚐 Shuttle durumu değişti:", data);
      // UI'ı güncelle
    });
  }
}
```

## Best Practices

1. **Heartbeat/Ping-Pong**: Bağlantının canlı olduğunu kontrol etmek için periyodik ping mesajları gönder

```typescript
setInterval(() => {
  if (this.socket.connected) {
    this.socket.emit("ping", { timestamp: Date.now() });
  }
}, 30000); // Her 30 saniyede bir
```

2. **Message Queue**: Bağlantı kesildiğinde mesajları kuyruğa al, yeniden bağlandığında gönder

```typescript
private messageQueue: any[] = [];

sendMessage(message: any) {
  if (this.socket.connected) {
    this.socket.emit('message', message);
  } else {
    this.messageQueue.push(message);
  }
}

private onReconnected() {
  // Kuyruktaki mesajları gönder
  while (this.messageQueue.length > 0) {
    const message = this.messageQueue.shift();
    this.socket.emit('message', message);
  }
}
```

3. **Network State Monitoring**: Cihazın internet bağlantısını kontrol et

```typescript
import NetInfo from "@react-native-community/netinfo";

NetInfo.addEventListener((state) => {
  if (state.isConnected && !this.socket.connected) {
    console.log("📶 İnternet bağlantısı geri geldi, yeniden bağlanılıyor...");
    this.socket.connect();
  }
});
```

## Requirements

- Requirements: 10.5
- Exponential backoff strategy ile yeniden bağlanma
- Connection status indicator
- Network state monitoring
- Message queue for offline messages
