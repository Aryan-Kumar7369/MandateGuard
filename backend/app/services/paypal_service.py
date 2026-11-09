import os
from decimal import Decimal
import httpx
from fastapi import HTTPException, status

class PayPalService:
    @staticmethod
    def _get_config() -> tuple[str, str, str]:
        client_id = os.getenv("PAYPAL_CLIENT_ID", "")
        client_secret = os.getenv("PAYPAL_CLIENT_SECRET", "")
        base_url = os.getenv("PAYPAL_API_BASE", "https://api-m.sandbox.paypal.com")
        return client_id, client_secret, base_url

    @classmethod
    def get_access_token(cls) -> str:
        client_id, client_secret, base_url = cls._get_config()
        url = f"{base_url}/v1/oauth2/token"
        headers = {"Accept": "application/json", "Accept-Language": "en_US"}
        data = {"grant_type": "client_credentials"}

        with httpx.Client() as client:
            response = client.post(
                url,
                auth=(client_id, client_secret),
                headers=headers,
                data=data,
                timeout=10.0
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"PayPal OAuth failed: {response.text}"
                )
            return response.json()["access_token"]

    @classmethod
    def get_order_details(cls, order_id: str) -> dict:
        _, _, base_url = cls._get_config()
        token = cls.get_access_token()
        url = f"{base_url}/v2/checkout/orders/{order_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"PayPal Order '{order_id}' not found: {response.text}"
                )
            data = response.json()
            purchase_unit = data["purchase_units"][0]
            amount_val = purchase_unit["amount"]["value"]
            currency_code = purchase_unit["amount"]["currency_code"]
            
            return {
                "id": data["id"],
                "status": data["status"],
                "amount": Decimal(amount_val),
                "currency": currency_code
            }

    @classmethod
    def capture_order(cls, order_id: str) -> dict:
        _, _, base_url = cls._get_config()
        token = cls.get_access_token()
        url = f"{base_url}/v2/checkout/orders/{order_id}/capture"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        with httpx.Client() as client:
            response = client.post(url, headers=headers, timeout=10.0)
            if response.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PayPal Capture failed: {response.text}"
                )
            return response.json()

    @classmethod
    def list_disputes(cls, page_size: int = 10) -> dict:
        _, _, base_url = cls._get_config()
        token = cls.get_access_token()
        url = f"{base_url}/v1/customer/disputes?page_size={page_size}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"PayPal Disputes fetch failed: {response.text}"
                )
            return response.json()

    @classmethod
    def get_dispute_details(cls, dispute_id: str) -> dict:
        _, _, base_url = cls._get_config()
        token = cls.get_access_token()
        url = f"{base_url}/v1/customer/disputes/{dispute_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"PayPal Dispute '{dispute_id}' not found: {response.text}"
                )
            return response.json()