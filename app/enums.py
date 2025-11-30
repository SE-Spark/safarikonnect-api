import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    DRIVER = "driver"
    USER = "user"

class ContactMethod(enum.Enum):
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"

class Priority(enum.Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class MaximumWaitingTime(enum.Enum):
    ONE_TWENTY_MINUTES = 120 #2HRS
    NINTY_MINUTES = 90 #1.5HRS
    SIXTY_MINUTES = 60 #1HRS
    THIRTY_MINUTES = 30
    TWENTY_MINUTES = 15

class DeliveryStatus(enum.Enum):
    PENDING = 1
    INTRANSIT = 2
    DELIVERED = 3
    ONHOLD = 4

class TransactionType(enum.Enum):
    CREDIT = 'credit'
    DEBIT = 'debit'
    TRANSFER = 'transfer'
    REFUND = 'refund'
    
class DriverAvailabilityStatus(enum.Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ON_TRIP = "on_trip"
    OFFLINE = "offline"
    
class BidStatus(enum.Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    AWARDED = "awarded"
    
class BusinessStatus(enum.Enum):
    AVAILABLE = "available" # availablr for bidding
    ONHOLD = "onhold"   # set onhold by admin
    AWARDED = "awarded" # awarded to a driver by system or parcel owner
    INTRANSIT = "intransit" # set on transit by driver or system
    COMPLETED = "completed" # set completed on closing the business