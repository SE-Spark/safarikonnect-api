from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import hashlib
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password

# Enum replacements as choices
class MaximumWaitingTime(models.TextChoices):
    FIFTEEN_MINUTES = 'FIFTEEN_MINUTES', 'Fifteen Minutes'
    THIRTY_MINUTES = 'THIRTY_MINUTES', 'Thirty Minutes'
    ONE_HOUR = 'ONE_HOUR', 'One Hour'
    TWO_HOURS = 'TWO_HOURS', 'Two Hours'

class Priority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'

class BusinessStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class DeliveryStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PICKED_UP = 'PICKED_UP', 'Picked Up'
    IN_TRANSIT = 'IN_TRANSIT', 'In Transit'
    DELIVERED = 'DELIVERED', 'Delivered'
    CANCELLED = 'CANCELLED', 'Cancelled'

class BidStatus(models.TextChoices):
    ACCEPTED = 'ACCEPTED', 'Accepted'
    PENDING = 'PENDING', 'Pending'
    REJECTED = 'REJECTED', 'Rejected'
    CANCELLED = 'CANCELLED', 'Cancelled'

class DriverAvailabilityStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    UNAVAILABLE = 'UNAVAILABLE', 'Unavailable'
    BUSY = 'BUSY', 'Busy'
    
class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    USER = 'USER', 'User'
    DRIVER = 'DRIVER', 'Driver'
    BUSINESS = 'BUSINESS', 'Business'
    
# Models

class User(AbstractUser):
    # Override username to make it optional
    username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Add custom fields
    name = models.CharField(max_length=100, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER
    )
    email_verified = models.BooleanField(default=False)
    phone_number_verified = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    last_active = models.DateTimeField(default=timezone.now)

    # Fields already provided by AbstractUser:
    # password
    # last_login
    # is_superuser
    # first_name
    # last_name
    # email
    # is_staff
    # is_active
    # date_joined

    class Meta:
        swappable = 'AUTH_USER_MODEL'

    @property
    def formatted_created_at(self):
        """Return the created_at date as a formatted string."""
        return self.date_joined.strftime("%Y-%m-%d %H:%M:%S") if self.date_joined else ""

    @property
    def formatted_updated_at(self):
        """Return the updated_at date as a formatted string."""
        return self.last_active.strftime("%Y-%m-%d %H:%M:%S") if self.last_active else ""

    def verify_password(self, password: str) -> bool:
        """Verify password using Django's built-in password hasher."""
        return check_password(password, self.password)

    def set_password(self, raw_password):
        """Override set_password to use Django's built-in password hasher."""
        self.password = make_password(raw_password)
        self._password = raw_password

    def update_last_active(self):
        """Update the last_active timestamp to the current time."""
        self.last_active = timezone.now()
        self.save(update_fields=['last_active'])

    def __str__(self):
        identifier = self.username or self.email or self.phone_number or self.id
        return f"<User(id={self.id}, identifier={identifier})>"

class VehicleColor(models.Model):
    name = models.CharField(max_length=50, unique=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<VehicleColor(id={self.id}, name={self.name})>"

class VehicleMake(models.Model):
    name = models.CharField(max_length=50, unique=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<VehicleMake(id={self.id}, name={self.name})>"

class VehicleType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<VehicleType(id={self.id}, name={self.name})>"

class VehicleModel(models.Model):
    name = models.CharField(max_length=50)
    make = models.ForeignKey(VehicleMake, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<VehicleModel(id={self.id}, name={self.name})>"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    vehicle_color = models.ForeignKey(VehicleColor, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle_plate_number = models.CharField(max_length=255, unique=True, null=True, blank=True)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.SET_NULL, null=True, blank=True)
    driver_license_number = models.CharField(max_length=255, unique=True, null=True, blank=True)
    driver_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    def sync(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __str__(self):
        return f"<Profile(id={self.id}, user_id={self.user.id}, vehicle_plate_number={self.vehicle_plate_number})>"

class Business(models.Model):
    new_business_code = models.CharField(max_length=12, unique=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.LOW)
    maximum_waiting_time = models.CharField(max_length=20, choices=MaximumWaitingTime.choices, 
                                           default=MaximumWaitingTime.THIRTY_MINUTES)
    pickup_point = models.CharField(max_length=255)
    delivery_fee = models.IntegerField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=BusinessStatus.choices, default=BusinessStatus.AVAILABLE)

    @property
    def formatted_created_at(self):
        """Return the created_at date as a formatted string."""
        return self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else ""

    @property
    def has_awarded_bid(self):
        """Check if any bid has been awarded."""
        return self.bid_set.filter(awarded_at__isnull=False).exists()

    @staticmethod
    def generate_business_code(owner_id):
        # Get the current timestamp
        timestamp = int(datetime.now().timestamp())
        
        # Create a unique string by combining the timestamp and owner_id
        unique_string = f"{timestamp}{owner_id}"
        
        # Generate a hash of the unique string
        hash_object = hashlib.sha256(unique_string.encode())
        hash_hex = hash_object.hexdigest()
        
        # Take the first 12 characters of the hash and convert to alphanumeric
        alphanumeric_code = ''.join(c for c in hash_hex if c.isalnum())[:12]
        
        return alphanumeric_code

    def save(self, *args, **kwargs):
        if self.published and not self.published_at:
            self.published_at = timezone.now()
        elif not self.published:
            self.published_at = None
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"<Business(id={self.id}, new_business_code={self.new_business_code})>"

class Parcel(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='parcels')
    parcel_details = models.CharField(max_length=255)
    dropoff_point = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (f"<Parcel(id={self.id}, "
                f"business_id={self.business.id}, "
                f"parcel_details='{self.parcel_details}', "
                f"dropoff_point='{self.dropoff_point}', "
                f"status='{self.status}', "
                f"created_at={self.created_at}, "
                f"updated_at={self.updated_at})>")

    def to_dict(self):
        """Convert the Parcel instance to a dictionary."""
        return {
            "id": self.id,
            "business_id": self.business.id,
            "parcel_details": self.parcel_details,
            "dropoff_point": self.dropoff_point,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

class Bid(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='bids')
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='driver_bids')
    bid_amount = models.IntegerField()
    awarded_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_bids')
    cancel_reason = models.CharField(max_length=255, null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=BidStatus.choices, default=BidStatus.ACCEPTED)

    def __str__(self):
        return f"<Bid(id={self.id}, business_id={self.business.id})>"

class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<ChatMessage(id={self.id}, sender_id={self.sender.id}, receiver_id={self.receiver.id})>"

class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    registration_number = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    contact_email = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<Company(id={self.id}, name={self.name})>"

class CompanyUser(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<CompanyUser(id={self.id}, company_id={self.company.id}, user_id={self.user.id})>"

class DeliveryStatus(models.Model):
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE)
    status = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"<DeliveryStatus(id={self.id}, parcel_id={self.parcel.id})>"

class DriverAvailability(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=DriverAvailabilityStatus.choices, 
                             default=DriverAvailabilityStatus.UNAVAILABLE)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<DriverAvailability(id={self.id}, driver_id={self.driver.id})>"

class DriverRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_received')
    rating = models.IntegerField()
    comments = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<DriverRating(id={self.id}, user_id={self.user.id}, driver_id={self.driver.id})>"

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_given')
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_received')
    rating = models.IntegerField()
    comments = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<Feedback(id={self.id}, user_id={self.user.id}, driver_id={self.driver.id})>"

class Geofence(models.Model):
    name = models.CharField(max_length=255)
    coordinates = models.CharField(max_length=255)
    radius = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<Geofence(id={self.id}, name={self.name})>"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<Notification(id={self.id}, user_id={self.user.id})>"

class OTP(models.Model):
    contact_info = models.CharField(max_length=255, db_index=True)  # Email or phone number
    otp_code = models.CharField(max_length=10, db_index=True)  # The OTP code
    created_at = models.DateTimeField(default=timezone.now)  # Timestamp of when the OTP was created
    expires_at = models.DateTimeField()  # Timestamp of when the OTP expires

    def to_dict(self):
        return {
            "id": self.id,
            "contact_info": self.contact_info,
            "otp_code": self.otp_code,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }

class PaymentTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<PaymentTransaction(id={self.id}, user_id={self.user.id})>"

class Role(models.Model):
    role_name = models.CharField(max_length=255, unique=True)
    permissions = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<Role(id={self.id}, role_name={self.role_name})>"

class Ticket(models.Model):
    raised_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    category = models.ForeignKey('TicketCategory', on_delete=models.CASCADE)
    details = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<Ticket(id={self.id}, raised_by={self.raised_by.id})>"

class TicketCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<TicketCategory(id={self.id}, name={self.name})>"

class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    active_balance = models.IntegerField(default=0)
    transactional_balance = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<Wallet(id={self.id}, user_id={self.user.id})>"

class Transaction(models.Model):
    from_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions_sent')
    to_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions_received')
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_release_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"<Transaction(id={self.id})>"

class TransactionalWallet(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions_received')
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_release_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"<TransactionalWallet(id={self.id})>"