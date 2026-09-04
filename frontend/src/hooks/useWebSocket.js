import { useState, useEffect, useRef } from "react";

/**
 * Resilient WebSocket Hook for Razorpay Dispute Defender.
 * Safely falls back to local simulation when backend WebSocket is offline.
 */
export function useWebSocket(url = (import.meta.env.VITE_WS_URL || "ws://localhost:8000/api/ws")) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState("connecting"); // connecting, live, fallback
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    let isMounted = true;

    function connect() {
      try {
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          setIsConnected(true);
          setConnectionStatus("live");
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const data = JSON.parse(event.data);
            setLastMessage(data);
          } catch (e) {
            setLastMessage(event.data);
          }
        };

        ws.onerror = () => {
          // Gracefully handle backend absence without console panic
          if (isMounted) {
            setIsConnected(false);
            setConnectionStatus("fallback");
          }
        };

        ws.onclose = () => {
          if (!isMounted) return;
          setIsConnected(false);
          setConnectionStatus("fallback");
          // Attempt retry every 15 seconds
          reconnectTimeoutRef.current = setTimeout(connect, 15000);
        };
      } catch (err) {
        if (isMounted) {
          setIsConnected(false);
          setConnectionStatus("fallback");
          reconnectTimeoutRef.current = setTimeout(connect, 15000);
        }
      }
    }

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [url]);

  return {
    isConnected,
    connectionStatus,
    lastMessage,
  };
}
