"""
Message structures for communication between Python bots and C++ exchange.
Handles serialization to/from JSON format.
"""
import json
from dataclasses import dataclass
from typing import Union

from .enums import Side, OrdType, TimeInForce, MsgType


@dataclass
class MessageHeader:
    """Header included in every message."""
    version: int = 1
    type: MsgType = MsgType.HEARTBEAT
    seq: int = 0
    client_id: int = 0
    
    def to_dict(self):
        return {
            "version": self.version,
            "type": int(self.type),
            "seq": self.seq,
            "client_id": self.client_id
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            version=data.get("version", 1),
            type=MsgType(data["type"]),
            seq=data.get("seq", 0),
            client_id=data.get("client_id", 0)
        )


@dataclass
class NewOrderRequest:
    """Request to place a new order. Bot sends to exchange."""
    client_order_id: int
    symbol: str
    side: Side
    ord_type: OrdType
    qty: int
    limit_price: int = 0
    tif: TimeInForce = TimeInForce.DAY
    
    def to_dict(self):
        return {
            "client_order_id": self.client_order_id,
            "symbol": self.symbol,
            "side": self.side.as_string(),
            "ord_type": self.ord_type.as_string(),
            "qty": self.qty,
            "limit_price": self.limit_price,
            "tif": self.tif.as_string()
        }


@dataclass
class CancelRequest:
    """Request to cancel an existing order. Bot sends to exchange."""
    symbol: str
    order_id: int = 0
    client_order_id: int = 0
    
    def to_dict(self):
        result = {"symbol": self.symbol}
        if self.order_id:
            result["order_id"] = self.order_id
        if self.client_order_id:
            result["client_order_id"] = self.client_order_id
        return result


@dataclass
class Ack:
    """Acknowledgment that order was accepted. Exchange sends to bot."""
    client_order_id: int = 0
    order_id: int = 0
    symbol: str = ""
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            client_order_id=data.get("client_order_id", 0),
            order_id=data.get("order_id", 0),
            symbol=data.get("symbol", "")
        )


@dataclass
class RejectInfo:
    """Details about why an order was rejected."""
    reason: str = ""
    code: int = 0
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return cls()
        return cls(reason=data.get("reason", ""), code=data.get("code", 0))


@dataclass
class Reject:
    """Notification that order was rejected. Exchange sends to bot."""
    client_order_id: int = 0
    symbol: str = ""
    info: RejectInfo = None
    
    def __post_init__(self):
        if self.info is None:
            self.info = RejectInfo()
    
    @classmethod
    def from_dict(cls, data):
        info_data = data.get("info")
        return cls(
            client_order_id=data.get("client_order_id", 0),
            symbol=data.get("symbol", ""),
            info=RejectInfo.from_dict(info_data) if info_data else RejectInfo()
        )


@dataclass
class Fill:
    """Notification that order was matched. Exchange sends to bot."""
    order_id: int = 0
    symbol: str = ""
    side: Side = Side.BUY
    fill_qty: int = 0
    fill_price: int = 0
    complete: bool = False
    
    @classmethod
    def from_dict(cls, data):
        side_value = data.get("side", "B")
        if isinstance(side_value, str):
            side = Side.parse(side_value)
        else:
            side = Side(side_value)
        return cls(
            order_id=data.get("order_id", 0),
            symbol=data.get("symbol", ""),
            side=side,
            fill_qty=data.get("fill_qty", 0),
            fill_price=data.get("fill_price", 0),
            complete=data.get("complete", False)
        )


MessageBody = Union[NewOrderRequest, CancelRequest, Ack, Reject, Fill, dict]


@dataclass
class Envelope:
    """Complete message with header and body."""
    header: MessageHeader
    body: MessageBody
    
    def to_json(self):
        body_dict = self.body.to_dict() if hasattr(self.body, 'to_dict') else self.body
        return json.dumps({"header": self.header.to_dict(), "body": body_dict})
    
    @classmethod
    def from_json(cls, json_string):
        data = json.loads(json_string)
        header = MessageHeader.from_dict(data["header"])
        body_data = data["body"]
        
        if header.type == MsgType.ACK:
            body = Ack.from_dict(body_data)
        elif header.type == MsgType.REJECT:
            body = Reject.from_dict(body_data)
        elif header.type == MsgType.FILL:
            body = Fill.from_dict(body_data)
        else:
            body = body_data
        
        return cls(header=header, body=body)


def create_new_order(client_id, client_order_id, symbol, side, qty, 
                     price=0, ord_type=OrdType.LIMIT, tif=TimeInForce.DAY, seq=0):
    header = MessageHeader(type=MsgType.NEW_ORDER, seq=seq, client_id=client_id)
    body = NewOrderRequest(
        client_order_id=client_order_id, symbol=symbol, side=side,
        ord_type=ord_type, qty=qty, limit_price=price, tif=tif
    )
    return Envelope(header=header, body=body)


def create_cancel(client_id, symbol, order_id=0, client_order_id=0, seq=0):
    header = MessageHeader(type=MsgType.CANCEL, seq=seq, client_id=client_id)
    body = CancelRequest(symbol=symbol, order_id=order_id, client_order_id=client_order_id)
    return Envelope(header=header, body=body)
