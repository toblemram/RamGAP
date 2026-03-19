from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional

class SignatureVariant(BaseModel):
    args: List[str]
    returns: str

class PlaxisDoc(BaseModel):
    id: str
    object: str
    method: str
    synopsis: str = ""
    signature_variants: List[SignatureVariant] = Field(default_factory=list)
    preconditions: List[str] = Field(default_factory=list)
    minimal_examples: List[str] = Field(default_factory=list)
    common_errors: List[Dict[str, str]] = Field(default_factory=list)
    aliases: List[str] = Field(default_factory=list)

    @validator("id", "object", "method")
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v.strip()
