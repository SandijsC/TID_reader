from dataclasses import dataclass, field
from BE.rfid_decode import decode_epc

@dataclass(slots=True)
class RFIDEvent:
    """
    Represents a single RFID read event coming from the XML reader.
    """
    epc: str
    tid: str | None
    event: str | None
    antenna: str | None
    rssi: float
    timestamp: float


@dataclass(slots=True)
class RFIDTag:
    crate_id:str
    epc: str
    barcode: str
    first_seen_at: float
    last_seen_at: float
    is_rejected: bool
    tids: set[str] = field(default_factory=set)

    def update(self, tid: str | None, timestamp: float):
        self.last_seen_at = timestamp
        if tid:
            self.tids.add(tid)

    @property
    def reading_time(self) -> float:
        return self.last_seen_at - self.first_seen_at

    @property
    def tid_count(self) -> int:
        return len(self.tids)

    @property
    def status(self) -> str:
        return "PASSED" if self.tid_count >= 2 else "FAILED"

    @classmethod
    def from_event(cls, event: RFIDEvent):
        epc_info = decode_epc(event.epc)

        return cls(
            epc=event.epc,
            barcode=epc_info.barcode,
            first_seen_at=event.timestamp,
            last_seen_at=event.timestamp,
            crate_id=0,
            is_rejected=True
        )
        
    @classmethod
    def empty(cls, crate_id: str):
        return cls(
               crate_id=crate_id if crate_id else "NOT_AVAILABLE",
               epc="NOT_AVAILABLE",
               barcode="NOT_AVAILABLE",
               first_seen_at=0,
               last_seen_at=0,
               is_rejected=True
        )
    
