from typing import Protocol, List, Optional
import httpx
from .schemas import TelepathyMessage

class TransportLayer(Protocol):
    async def send(self, message: TelepathyMessage, target_node_id: Optional[str] = None):
        """Send a telepathic message to a specific node or broadcast."""
        ...

    async def receive(self) -> TelepathyMessage:
        """Listen for incoming telepathic messages."""
        ...

class HttpTransport:
    """
    Real HTTP Mesh Transport.
    Broadcasts to a list of known peers defined in configuration.
    """
    def __init__(self, peers: List[str]):
        """
        :param peers: List of base URLs e.g. ["http://192.168.1.5:8001"]
        """
        self.peers = peers
        self.client = httpx.AsyncClient(timeout=5.0)

    async def send(self, message: TelepathyMessage, target_node_id: Optional[str] = None):
        """
        Broadcasts the message to all peers.
        In a full DHT implementation, we would route to specific target_node_id.
        """
        payload = message.model_dump()
        
        # Simple Flood/Gossip
        for peer in self.peers:
            try:
                # Avoid echoing to self if peer list contains self (naive check)
                # In prod, we check node_id.
                url = f"{peer.rstrip('/')}/v1/telepathy/receive"
                # Fire and forget (or log failure)
                print(f"[Telepathy:HTTP] Sending to {url}")
                await self.client.post(url, json=payload)
            except Exception as e:
                print(f"[Telepathy:HTTP] Failed to send to {peer}: {e}")

    async def receive(self) -> TelepathyMessage:
        # HTTP is push-based to the server endpoint, so this polling method 
        # is less relevant unless we implement a pull queue. 
        # For this architecture, the Server Endpoint calls `swarm.handle_incoming`.
        raise NotImplementedError("HttpTransport is Push-Only via Webhook")

class MeshTransport:
    """
    Bluetooth P2P Mesh Transport via TUI.
    Talks to TUI's internal bridge on localhost:8003.
    """
    def __init__(self, bridge_url: str = "http://localhost:8003/telepathy"):
        self.bridge_url = bridge_url
        self.client = httpx.AsyncClient(timeout=2.0)

    async def send(self, message: TelepathyMessage, target_node_id: Optional[str] = None):
        """
        Sends the telepathy message to the TUI for mesh broadcast.
        """
        payload = message.model_dump()
        try:
            print(f"[Telepathy:Mesh] Sharing via TUI Bridge: {self.bridge_url}")
            await self.client.post(self.bridge_url, json=payload)
        except Exception as e:
            print(f"[Telepathy:Mesh] Bridge Failure: {e}")

    async def receive(self) -> TelepathyMessage:
        # TUI pushes received mesh packets back to Brain /v1/telepathy/receive
        raise NotImplementedError("MeshTransport is Push-Only via TUI Bridge")

class TelepathySwarm:
    """
    Manages AI<->AI communication.
    Abstracts over Bluetooth, LAN, WAN.
    """
    def __init__(self, node_id: str, transports: List[TransportLayer]):
        self.node_id = node_id
        self.transports = transports # Ordered by priority: Bluetooth -> LAN -> WAN
        self.peers = {} # Reputation table

    async def broadcast_thought(self, content: str, confidence: float):
        """
        Share a thought with the swarm.
        """
        msg = TelepathyMessage(
            type="THOUGHT",
            sender=self.node_id,
            confidence=confidence,
            content=content,
            cost_hint=0.0 # Calculate actual cost
        )
        await self._dispatch(msg)

    async def share_pattern(self, pattern_id: str, success_rate: float):
        """
        Share a successful learned pattern.
        """
        msg = TelepathyMessage(
            type="PATTERN_SHARE",
            sender=self.node_id,
            pattern=pattern_id,
            success_rate=success_rate
        )
        await self._dispatch(msg)

    async def _dispatch(self, message: TelepathyMessage):
        """
        Try to send via the cheapest/nearest transport first.
        """
        # Broadcast to all transports
        for transport in self.transports:
            # We iterate all transports to ensure maximum reach (e.g. LAN + WAN)
            # In production, we might be more selective.
            try:
                await transport.send(message)
            except Exception as e:
                print(f"[Telepathy] Dispatch Error: {e}")

    async def handle_incoming(self, message: TelepathyMessage):
        """
        Process incoming messages.
        Filter by reputation, validate signature, then ingest into cortex.
        """
        print(f"[Telepathy] Received from {message.sender}: {message.content}")
        
        # 1. Validation (Signature mock)
        if not message.sender:
            return None
            
        # 2. Conversion to Signal
        # Even though this class is detached, we prepare the data structure for the Cortex to pick up.
        # This writes to a dedicated signal bus log that the LangGraph Engine monitors.
        
        signal_data = {
            "type": "telepathy",
            "source": message.sender,
            "content": message.content,
            "confidence": message.confidence,
            "pattern_id": message.pattern,
            "timestamp": "iso-now"
        }
        
        # Simulating Event Bus Push
        import json
        import asyncio

        def _write_to_bus():
            with open("ippoc_event_bus.log", "a") as bus:
                bus.write(json.dumps(signal_data) + "\n")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _write_to_bus)
            
        return signal_data
