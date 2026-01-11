"""
Message structures matching the C++ exchange protocol 
These dataclasses represent the JSON messages sent to/from the exchange.
"""
from dataclasses import dataclass, field
from typing import Union, Any
import json

from .enums import Side, OrdType, TimeInForce, MsgType


# =============================================================================
# Message Header (common to all messages)
# =============================================================================

@dataclass
class MessageHeader:
    version: int = 1
    type: MsgType 
    seq: int = 0 
    client_id: int = 0
    
    def to_dict(self):
        return {
            "version": self.version,
            "type": int(self.type),  # JSON doesn't understand enums, convert to plain integer
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


# =============================================================================
# Bot -> Exchange
# =============================================================================

@dataclass
class NewOrderRequest:
    """ Request to place a new order """

    client_order_id: int
    symbol: str
    side: Side
    ord_type: OrdType
    qty: int
    limit_price: int = 0  # Only for LIMIT orders
    tif: TimeInForce = TimeInForce.DAY
    
    def to_dict(self):
        result = {
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
    """ Request to cancel an existing order """

    symbol: str
    order_id: int = 0
    client_order_id: int = 0    # Cancel Order can use Either ID, so default for both is zero
    
    def to_dict(self) -> dict:
        result = {}
        if self.order_id != 0:
            result["order_id"] = self.order_id
        if self.client_order_id != 0:
            result["client_order_id"] = self.client_order_id
        if self.symbol:
            result["symbol"] = self.symbol
        return result
    

# =============================================================================
# Outbound Messages (Exchange -> Bot)
# =============================================================================

@dataclass
class RejectInfo:
    """Rejection details"""
    reason: str = ""
    code: int = 0
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return cls()
        else:
            return cls(
                reason = data.get("reason", ""),
                code = data.get("code", 0)
            )


@dataclass
class Ack:
    """ Order acknowledgment """

    client_order_id: int = 0
    order_id: int = 0  # Venue-assigned ID
    symbol: str = ""
    # All fields have been given defaults in the case JSON might not have all fields

    
    @classmethod
    def from_dict(cls, data):
        return cls(
            client_order_id=data.get("client_order_id", 0),
            order_id=data.get("order_id", 0),
            symbol=data.get("symbol", "")
        )


@dataclass
class Reject:
    """ Order rejection, sent by exchange when order is rejected. """

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
    """
    Order fill notification, sent by exchange when order is (partially or fully) filled.
    """
    order_id: int = 0
    symbol: str = ""
    side: Side = Side.BUY
    fill_qty: int = 0
    fill_price: int = 0
    complete: bool = False  # True if order is fully filled
    
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


# =============================================================================
# Envelope (complete message wrapper)
# =============================================================================

# Type alias for inbound/outbound message bodies
MessageBody = Union[NewOrderRequest, CancelRequest, Ack, Reject, Fill, dict]


@dataclass
class Envelope:
    """Complete message envelope with header and body"""

    header: MessageHeader
    body: MessageBody
    
    def to_json(self):
        """Serialize to JSON string for sending over ZMQ"""
        body_dict = self.body.to_dict() if hasattr(self.body, 'to_dict') else self.body
        return json.dumps({
            "header": self.header.to_dict(),
            "body": body_dict
        })
    
    @classmethod
    def from_json(cls, json_string):
        """Create from JSON string received from exchange."""
        data = json.loads(json_string)
        header = MessageHeader.from_dict(data["header"])
        body_data = data["body"]
        
        # Parse body based on message type
        if header.type == MsgType.ACK:
            body = Ack.from_dict(body_data)
        elif header.type == MsgType.REJECT:
            body = Reject.from_dict(body_data)
        elif header.type == MsgType.FILL:
            body = Fill.from_dict(body_data)
        else:
            body = body_data  # Unknown type, keep as dictionary
        
        return cls(header=header, body=body)


# =============================================================================
# Helper functions for creating messages
# =============================================================================

def create_new_order(client_id, client_order_id, symbol, side, qty, 
                     price=0, ord_type=OrdType.LIMIT, tif=TimeInForce.DAY, seq=0):
    """
    Convenience function to create a new order envelope.
    
    Args:
        client_id: Bot's ID
        client_order_id: Bot's order ID (for tracking)
        symbol: Stock symbol (e.g., "AAPL")
        side: Side.BUY or Side.SELL
        qty: Number of shares
        price: Limit price (default 0 for market orders)
        ord_type: OrdType.LIMIT or OrdType.MARKET
        tif: TimeInForce.DAY or TimeInForce.IOC
        seq: Sequence number
    
    Returns:
        Envelope ready to send
    """
    header = MessageHeader(
        type=MsgType.NEW_ORDER,
        seq=seq,
        client_id=client_id
    )
    body = NewOrderRequest(
        client_order_id=client_order_id,
        symbol=symbol,
        side=side,
        ord_type=ord_type,
        qty=qty,
        limit_price=price,
        tif=tif
    )
    return Envelope(header=header, body=body)


def create_cancel(client_id, symbol, order_id=0, client_order_id=0, seq=0):
    """
    Convenience function to create a cancel request envelope.
    
    Args:
        client_id: Bot's ID
        symbol: Stock symbol
        order_id: Exchange's order ID (preferred)
        client_order_id: Bot's order ID (alternative)
        seq: Sequence number
    
    Returns:
        Envelope ready to send
    """
    header = MessageHeader(
        type=MsgType.CANCEL,
        seq=seq,
        client_id=client_id
    )
    body = CancelRequest(
        symbol=symbol,
        order_id=order_id,
        client_order_id=client_order_id
    )
    return Envelope(header=header, body=body)
