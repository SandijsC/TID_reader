# rfid_decode.py
from dataclasses import dataclass


@dataclass
class TIDInfo:
    manufacturer: str
    model: str
    serial: str


def decode_tid(tid: str) -> TIDInfo:
    tid = tid.upper()

    if tid.startswith("E2806894"):
        return TIDInfo(
            manufacturer="NXP",
            model="0x894",
            serial=tid[8:],
        )

    if tid.startswith("E2801100"):
        return TIDInfo(
            manufacturer="Impinj",
            model="0x100",
            serial=tid[8:],
        )

    return TIDInfo(
        manufacturer="Unknown",
        model="Unknown",
        serial=tid[8:],
    )

@dataclass
class EPCInfo:
    scheme: str
    barcode: str
    company_prefix: str
    asset_type: str
    serial: int


def _bits(value: int, start: int, length: int, total: int = 96):
    shift = total - start - length
    mask = (1 << length) - 1
    return (value >> shift) & mask


def decode_epc(epc_hex: str) -> EPCInfo:
    epc_hex = epc_hex.upper()

    header = int(epc_hex[:2], 16)

    if header != 0x33:
        return EPCInfo(
            scheme="UNKNOWN",
            barcode=epc_hex,
            company_prefix="",
            asset_type="",
            serial=0,
        )

    epc = int(epc_hex, 16)

    partition = _bits(epc, 11, 3)

    partition_table = {
        0: (40, 12, 4, 0),
        1: (37, 11, 7, 1),
        2: (34, 10, 10, 2),
        3: (30, 9, 14, 3),
        4: (27, 8, 17, 4),
        5: (24, 7, 20, 5),
        6: (20, 6, 24, 6),
    }

    cp_bits, cp_digits, asset_bits, asset_digits = partition_table[
        partition
    ]

    company_prefix = _bits(
        epc,
        14,
        cp_bits,
    )

    asset_type = _bits(
        epc,
        14 + cp_bits,
        asset_bits,
    )

    serial = _bits(
        epc,
        14 + cp_bits + asset_bits,
        38,
    )

    company_prefix_str = str(company_prefix).zfill(cp_digits)
    asset_type_str = str(asset_type).zfill(asset_digits)

    grai = (
        "0"
        + company_prefix_str
        + asset_type_str
        + "9"
        + str(serial)
    )
    
    return EPCInfo(
        scheme="GRAI-96",
        barcode=grai,
        company_prefix=company_prefix_str,
        asset_type=asset_type_str,
        serial=serial,
    )