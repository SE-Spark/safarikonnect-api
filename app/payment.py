import os
import json
import hmac
import hashlib
from decimal import Decimal

import requests


class PaymentProcessingModule:
    """
    Thin wrapper around the Paystack REST API.
    """

    BASE_URL = os.getenv('PAYSTACK_BASE_URL', 'https://api.paystack.co')
    SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY') or os.getenv('PAYSTACK_API_KEY')
    WEBHOOK_SECRET = os.getenv('PAYSTACK_WEBHOOK_SECRET') or SECRET_KEY
    DEFAULT_CURRENCY = os.getenv('PAYSTACK_DEFAULT_CURRENCY', 'KES')

    @classmethod
    def _headers(cls):
        if not cls.SECRET_KEY:
            raise ValueError("PAYSTACK_SECRET_KEY or PAYSTACK_API_KEY is not configured")
        return {
            "Authorization": f"Bearer {cls.SECRET_KEY}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _to_subunit(amount):
        # Paystack expects the smallest currency unit (kobo, pesewas, etc.)
        return int(Decimal(str(amount)) * 100)

    @classmethod
    def initiatePayment(cls, amount, email, first_name=None, last_name=None, phone=None, currency=None, metadata=None):
        payload = {
            "amount": cls._to_subunit(amount),
            "email": email,
            "currency": (currency or cls.DEFAULT_CURRENCY).upper(),
        }

        meta = metadata.copy() if metadata else {}
        custom_fields = list(meta.get("custom_fields", []))

        def add_custom_field(value, display_name, variable_name):
            if value:
                custom_fields.append(
                    {
                        "value": value,
                        "display_name": display_name,
                        "variable_name": variable_name,
                    }
                )

        add_custom_field(first_name, "First Name", "first_name")
        add_custom_field(last_name, "Last Name", "last_name")
        add_custom_field(phone, "Phone Number", "phone_number")

        if custom_fields:
            meta["custom_fields"] = custom_fields

        if meta:
            payload["metadata"] = meta

        response = requests.post(
            f"{cls.BASE_URL}/transaction/initialize",
            headers=cls._headers(),
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def createCustomer(cls, email, first_name=None, last_name=None, phone=None, metadata=None):
        payload = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "metadata": metadata or {},
        }
        response = requests.post(
            f"{cls.BASE_URL}/customer",
            headers=cls._headers(),
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    
    @classmethod
    def verifyPayment(cls, transReference):
        response = requests.get(
            f"{cls.BASE_URL}/transaction/verify/{transReference}",
            headers=cls._headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def chargeCustomer(cls, amount, email, authorization_code, currency=None, metadata=None):
        payload = {
            "email": email,
            "amount": cls._to_subunit(amount),
            "authorization_code": authorization_code,
            "currency": (currency or cls.DEFAULT_CURRENCY).upper(),
        }
        if metadata:
            payload["metadata"] = metadata

        response = requests.post(
            f"{cls.BASE_URL}/transaction/charge_authorization",
            headers=cls._headers(),
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def verifyPayloadHashmac(cls, raw_body, signature):
        """
        Validate Paystack webhook payload signature.
        """
        if not cls.WEBHOOK_SECRET:
            raise ValueError("PAYSTACK_WEBHOOK_SECRET (or secret key) must be configured for webhook validation")

        computed = hmac.new(
            cls.WEBHOOK_SECRET.encode('utf-8'),
            msg=raw_body if isinstance(raw_body, bytes) else json.dumps(raw_body).encode('utf-8'),
            digestmod=hashlib.sha512,
        ).hexdigest()
        return hmac.compare_digest(computed, signature or "")
        
    # -------------------------------------------------
    # 3. Generic recipient resolver (bank OR mobile)
    # -------------------------------------------------
    @classmethod
    def create_recipient(cls, name, account, bank_code, type="nuban", currency=None, metadata=None):
        """
        Universal creator to handle bank or mobile money.

        type = "nuban" or "mobile_money"
        name = name of the recipient/customer
        account_number = account number of the bank or mobile money provider
        bank_code = bank code of the bank or mobile money provider
        currency = currency of the transaction; only kes is supported by default
        """

        payload = {
            "type": type,
            "name": name,
            "account_number": account,
            "bank_code": bank_code,
            "currency": (currency or cls.DEFAULT_CURRENCY).upper(),
        }

        if metadata:
            payload["metadata"] = metadata

        response = requests.post(
            f"{cls.BASE_URL}/transferrecipient",
            headers=cls._headers(),
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    # withdraw from wallet(b to c from paystack to customer bank or mobile money)    
    @classmethod
    def withdraw_from_wallet(cls, amount, recipient_code, reason=None, currency=None, metadata=None):
        payload = {
            "source": "balance",
            "amount": cls._to_subunit(amount),
            "recipient": recipient_code,
            "currency": (currency or cls.DEFAULT_CURRENCY).upper(),
        }
        if reason:
            payload["reason"] = reason
        if metadata:
            payload["metadata"] = metadata

        response = requests.post(
            f"{cls.BASE_URL}/transfer",
            headers=cls._headers(),
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    