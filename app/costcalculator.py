import os
from decimal import Decimal
from math import radians, sin, cos, sqrt, atan2
import requests


class CostComputationModule:
    """
    Helper for estimating ride costs.

    It first tries to leverage an external “cost calculator” API (if the URL
    is configured), then falls back to a deterministic local calculation using
    the Haversine distance between pickup and dropoff coordinates.
    """

    BASE_FARE = Decimal(os.getenv('RIDE_BASE_FARE', '150'))
    COST_PER_KM = Decimal(os.getenv('RIDE_COST_PER_KM', '60'))
    MINIMUM_FARE = Decimal(os.getenv('RIDE_MINIMUM_FARE', '200'))
    EXTERNAL_API_URL = os.getenv('COST_CALCULATOR_API_URL')
    EXTERNAL_API_KEY = os.getenv('COST_CALCULATOR_API_KEY')
    EXTERNAL_TIMEOUT = int(os.getenv('COST_CALCULATOR_TIMEOUT', '5'))

    @classmethod
    def estimate(
        cls,
        pickup_latitude,
        pickup_longitude,
        dropoff_latitude,
        dropoff_longitude,
        *,
        distance_km=None,
        metadata=None,
    ):
        """
        Return an estimation payload: {'amount': Decimal, 'distance_km': float, 'source': str}
        """
        metadata = metadata or {}

        if cls.EXTERNAL_API_URL:
            try:
                return cls._estimate_via_api(
                    pickup_latitude,
                    pickup_longitude,
                    dropoff_latitude,
                    dropoff_longitude,
                    metadata=metadata,
                )
            except (requests.RequestException, ValueError):
                # Fall back to the built-in calculator if the external service fails
                pass

        if distance_km is None:
            distance_km = cls._calculate_distance_km(
                pickup_latitude, pickup_longitude, dropoff_latitude, dropoff_longitude
            )

        return {
            "amount": cls._compute_local_cost(distance_km, metadata.get('surge_multiplier')),
            "distance_km": distance_km,
            "source": "local",
        }

    @classmethod
    def _estimate_via_api(
        cls,
        pickup_latitude,
        pickup_longitude,
        dropoff_latitude,
        dropoff_longitude,
        *,
        metadata=None,
    ):
        headers = {"Content-Type": "application/json"}
        if cls.EXTERNAL_API_KEY:
            headers["Authorization"] = f"Bearer {cls.EXTERNAL_API_KEY}"

        payload = {
            "pickup": {"lat": pickup_latitude, "lng": pickup_longitude},
            "dropoff": {"lat": dropoff_latitude, "lng": dropoff_longitude},
            **(metadata or {}),
        }

        response = requests.post(
            cls.EXTERNAL_API_URL,
            json=payload,
            headers=headers,
            timeout=cls.EXTERNAL_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        amount = data.get("amount") or data.get("estimated_cost")
        distance_km = data.get("distance_km") or data.get("distance")
        if amount is None or distance_km is None:
            raise ValueError("Cost calculator response did not include amount/distance")

        return {
            "amount": Decimal(str(amount)),
            "distance_km": float(distance_km),
            "source": "external",
            "raw_response": data,
        }

    @classmethod
    def _compute_local_cost(cls, distance_km, surge_multiplier=None):
        distance_decimal = Decimal(str(distance_km))
        surge = Decimal(str(surge_multiplier)) if surge_multiplier else Decimal('1')
        amount = (cls.BASE_FARE + (distance_decimal * cls.COST_PER_KM)) * surge
        return max(amount, cls.MINIMUM_FARE)

    @staticmethod
    def _calculate_distance_km(
        pickup_latitude,
        pickup_longitude,
        dropoff_latitude,
        dropoff_longitude,
    ):
        """
        Compute the great-circle distance between two coordinates using the Haversine formula.
        """
        radius_km = 6371

        lat1 = radians(pickup_latitude)
        lon1 = radians(pickup_longitude)
        lat2 = radians(dropoff_latitude)
        lon2 = radians(dropoff_longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return round(radius_km * c, 2)