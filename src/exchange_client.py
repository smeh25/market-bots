"""
Network communication with the C++ exchange via ZeroMQ.
"""
import threading
import zmq

from .enums import Side, OrdType, TimeInForce, MsgType
from .messages import Envelope, Ack, Reject, Fill, create_new_order, create_cancel


class ExchangeClient:
    """Client for communicating with the C++ exchange."""
    
    def __init__(self, client_id, host="localhost", send_port=5555, recv_port=5556):
        self.client_id = client_id
        self.host = host
        self.send_port = send_port
        self.recv_port = recv_port
        self._context = None
        self._send_socket = None
        self._recv_socket = None
        self._running = False
        self._listener_thread = None
        self._lock = threading.Lock()
        self._next_order_id = 1
        self._next_seq = 1
        self._pending_orders = {}
        self._order_id_map = {}
        self._callbacks = {MsgType.ACK: [], MsgType.REJECT: [], MsgType.FILL: []}
    
    def connect(self):
        self._context = zmq.Context()
        self._send_socket = self._context.socket(zmq.PUSH)
        self._send_socket.connect(f"tcp://{self.host}:{self.send_port}")
        self._recv_socket = self._context.socket(zmq.PULL)
        self._recv_socket.connect(f"tcp://{self.host}:{self.recv_port}")
    
    def disconnect(self):
        self.stop()
        if self._send_socket:
            self._send_socket.close()
        if self._recv_socket:
            self._recv_socket.close()
        if self._context:
            self._context.term()
    
    def start(self):
        if self._running:
            return
        self._running = True
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listener_thread.start()
    
    def stop(self):
        self._running = False
        if self._listener_thread:
            self._listener_thread.join(timeout=1.0)
    
    def send_order(self, envelope):
        self._send_socket.send_string(envelope.to_json())
        if hasattr(envelope.body, 'client_order_id'):
            with self._lock:
                self._pending_orders[envelope.body.client_order_id] = {
                    "symbol": getattr(envelope.body, 'symbol', ''),
                    "side": getattr(envelope.body, 'side', None),
                    "qty": getattr(envelope.body, 'qty', 0)
                }
    
    def send_limit_order(self, symbol, side, qty, price, tif=TimeInForce.DAY):
        with self._lock:
            client_order_id = self._next_order_id
            self._next_order_id += 1
            seq = self._next_seq
            self._next_seq += 1
        envelope = create_new_order(self.client_id, client_order_id, symbol, side, qty, price, OrdType.LIMIT, tif, seq)
        self.send_order(envelope)
        return client_order_id
    
    def send_market_order(self, symbol, side, qty):
        with self._lock:
            client_order_id = self._next_order_id
            self._next_order_id += 1
            seq = self._next_seq
            self._next_seq += 1
        envelope = create_new_order(self.client_id, client_order_id, symbol, side, qty, 0, OrdType.MARKET, TimeInForce.DAY, seq)
        self.send_order(envelope)
        return client_order_id
    
    def cancel_order(self, symbol, client_order_id):
        with self._lock:
            order_id = self._order_id_map.get(client_order_id, 0)
            seq = self._next_seq
            self._next_seq += 1
        envelope = create_cancel(self.client_id, symbol, order_id, client_order_id, seq)
        self.send_order(envelope)
    
    def _listen_loop(self):
        while self._running:
            try:
                if self._recv_socket.poll(timeout=100):
                    self._handle_message(self._recv_socket.recv_string())
            except Exception as e:
                if self._running:
                    print(f"[ERROR] Listener: {e}")
    
    def _handle_message(self, json_string):
        try:
            envelope = Envelope.from_json(json_string)
            if isinstance(envelope.body, Ack):
                with self._lock:
                    self._order_id_map[envelope.body.client_order_id] = envelope.body.order_id
                for cb in self._callbacks[MsgType.ACK]:
                    cb(envelope.body)
            elif isinstance(envelope.body, Reject):
                with self._lock:
                    self._pending_orders.pop(envelope.body.client_order_id, None)
                for cb in self._callbacks[MsgType.REJECT]:
                    cb(envelope.body)
            elif isinstance(envelope.body, Fill):
                if envelope.body.complete:
                    with self._lock:
                        for cid, oid in self._order_id_map.items():
                            if oid == envelope.body.order_id:
                                self._pending_orders.pop(cid, None)
                                break
                for cb in self._callbacks[MsgType.FILL]:
                    cb(envelope.body)
        except Exception as e:
            print(f"[ERROR] Parse: {e}")
    
    def on_ack(self, callback):
        self._callbacks[MsgType.ACK].append(callback)
    
    def on_reject(self, callback):
        self._callbacks[MsgType.REJECT].append(callback)
    
    def on_fill(self, callback):
        self._callbacks[MsgType.FILL].append(callback)
    
    def get_pending_orders(self):
        with self._lock:
            return dict(self._pending_orders)
    
    def get_order_id(self, client_order_id):
        with self._lock:
            return self._order_id_map.get(client_order_id)
