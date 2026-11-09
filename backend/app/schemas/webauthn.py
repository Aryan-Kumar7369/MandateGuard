from pydantic import BaseModel

class PasskeyRegisterResponse(BaseModel):
    credential_id: str
    public_key_pem: str
    user_id: str

class PasskeySignRequest(BaseModel):
    mandate_id: str
    credential_id: str
    client_data_json: str
    authenticator_data: str
    signature: str