from dataclasses import dataclass
from typing import Optional


@dataclass
class EncodeOptions:
    secret_text: str = ""
    secret_file_path: str = ""
    decoy_text: str = ""
    decoy_file_path: str = ""
    cover_media_path: str = ""
    technique: str = "LSB"
    primary_password: str = ""
    decoy_password: str = ""
    use_integrity: bool = True
    use_hint: bool = True
    output_path: str = ""


@dataclass
class DecodeOptions:
    stego_file_path: str = ""
    password: str = ""
    technique: str = "Auto"
    output_dir: Optional[str] = None


@dataclass
class PayloadResult:
    data: bytes
    filename: str
    label: str
    tag_found: bool
    tag_ok: Optional[bool]
