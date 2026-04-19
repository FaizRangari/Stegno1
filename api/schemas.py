from pydantic import BaseModel


class EncodeRequest(BaseModel):
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


class DecodeRequest(BaseModel):
    stego_file_path: str = ""
    password: str = ""
    technique: str = "Auto"


class OpenFolderRequest(BaseModel):
    path: str


class SaveDecodedRequest(BaseModel):
    source_path: str
    output_path: str
