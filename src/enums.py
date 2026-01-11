"""
Enums matching the exchange types
"""
from enum import IntEnum


class Side(IntEnum):
    """Order side, Buy side or Sell side"""
    BUY = 1
    SELL = 2
    
    def as_string(self):
        """Convert to JSON format"""
        if self == Side.BUY:
            return "B"
        else:
            return "S"
    
    @classmethod
    def parse(cls, code):
        """Parse from JSON format"""
        if code in ("B", "Buy", "BUY", "bid", "BID"):
            return cls.BUY
        elif code in ("S", "SELL", "ASK"):
            return cls.SELL
        else:
            raise ValueError(f"{code} is an Invalid Side")

class OrdType(IntEnum):
    """Order type, Market or Limit"""
    MARKET = 1
    LIMIT = 2
    
    def as_string(self):
        """ Convert to JSON wire format """
        if self == OrdType.MARKET:
            return "MKT"
        else:
            return "LMT"
    
    @classmethod
    def parse(cls, code):
        """Parse from JSON wire format"""
        code = code.upper()
        if code in ("MKT", "MARKET"):
            return cls.MARKET
        elif code in ("LMT", "LIMIT"):
            return cls.LIMIT
        else:
            raise ValueError(f"{code} is an Invalid OrdType")


class TimeInForce(IntEnum):
    """How Long Should the Order Stay Active"""
    DAY = 1
    IOC = 2  # Immediate or Cancel
    
    def as_string(self):
        """Convert to JSON format"""
        if self == TimeInForce.DAY:
            return "DAY"
        else:
            return "IOC"
    
    @classmethod
    def parse(cls, code):
        """Parse from JSON format"""
        code = code.upper()
        if code == "DAY":
            return cls.DAY
        elif code == "IOC":
            return cls.IOC
        else:
            raise ValueError(f"{code} is an Invalid TimeInForce")


class MsgType(IntEnum):
    """Message type"""
    # Bot -> Exchange
    NEW_ORDER = 1
    CANCEL = 2
    
    # Exchange -> Bot
    ACK = 100
    REJECT = 101
    FILL = 102
    
    # System
    HEARTBEAT = 900
