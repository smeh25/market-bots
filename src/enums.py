"""
Enum definitions matching the C++ exchange types.
These define the shared vocabulary between Python bots and C++ exchange.
"""
from enum import IntEnum


class Side(IntEnum):
    """Buy or sell direction. Matches ex::Side in C++ exchange."""
    BUY = 1
    SELL = 2
    
    def as_string(self):
        """Convert to JSON format used in message body."""
        if self == Side.BUY:
            return "B"
        return "S"
    
    @classmethod
    def parse(cls, code):
        """Convert from JSON format back to enum."""
        code = code.upper()
        if code in ("B", "BUY", "BID"):
            return cls.BUY
        elif code in ("S", "SELL", "ASK"):
            return cls.SELL
        raise ValueError(f"Invalid Side: {code}")


class OrdType(IntEnum):
    """Order type. Matches ex::OrdType in C++ exchange."""
    MARKET = 1
    LIMIT = 2
    
    def as_string(self):
        """Convert to JSON format used in message body."""
        if self == OrdType.MARKET:
            return "MKT"
        return "LMT"
    
    @classmethod
    def parse(cls, code):
        """Convert from JSON format back to enum."""
        code = code.upper()
        if code in ("MKT", "MARKET"):
            return cls.MARKET
        elif code in ("LMT", "LIMIT"):
            return cls.LIMIT
        raise ValueError(f"Invalid OrdType: {code}")


class TimeInForce(IntEnum):
    """How long order stays active. Matches ex::TimeInForce in C++ exchange."""
    DAY = 1
    IOC = 2  # Immediate Or Cancel
    
    def as_string(self):
        """Convert to JSON format used in message body."""
        if self == TimeInForce.DAY:
            return "DAY"
        return "IOC"
    
    @classmethod
    def parse(cls, code):
        """Convert from JSON format back to enum."""
        code = code.upper()
        if code == "DAY":
            return cls.DAY
        elif code == "IOC":
            return cls.IOC
        raise ValueError(f"Invalid TimeInForce: {code}")


class MsgType(IntEnum):
    """Message type identifier. Matches ex::MsgType in C++ exchange."""
    # Bot → Exchange (outbound)
    NEW_ORDER = 1
    CANCEL = 2
    
    # Exchange → Bot (inbound)
    ACK = 100
    REJECT = 101
    FILL = 102
    
    # System
    HEARTBEAT = 900
