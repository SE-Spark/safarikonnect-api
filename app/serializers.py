from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import (
    DriverAvailability, DriverRating,Business, Bid, Parcel,
    VehicleColor, VehicleType, VehicleMake, VehicleModel,
    Wallet, TransactionalWallet, PaymentTransaction,Feedback,Geofence,Ride,
    Ticket, TicketCategory
    )
from .models import Profile
from .enums import ContactMethod

User = get_user_model()

class PasswordResetRequestSerializer(serializers.Serializer):
    email_or_phone_number = serializers.CharField(required=True)

class VerifyPasswordResetCodeSerializer(serializers.Serializer):
    email_or_phone_number = serializers.CharField(required=True)
    verification_code = serializers.CharField(required=True)

class ResetPasswordSerializer(serializers.Serializer):
    email_or_phone_number = serializers.CharField(required=True)
    verification_code = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """
        Check that the two password fields match
        """
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match"
            })

        # Add password validation rules
        if len(data['new_password']) < 8:
            raise serializers.ValidationError({
                "new_password": "Password must be at least 8 characters long"
            })

        # You can add more password validation rules here
        # For example, checking for numbers, special characters, etc.

        return data

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """
        Check that the two password fields match
        """
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match"
            })

        if len(data['new_password']) < 8:
            raise serializers.ValidationError({
                "new_password": "Password must be at least 8 characters long"
            })

        return data

    def validate_current_password(self, value):
        """
        Check if the current password is correct
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value

class UserRegistrationOTPSerializer(serializers.Serializer):
    email_or_phone_number = serializers.CharField()
    contact_method = serializers.ChoiceField(choices=['EMAIL', 'PHONE'])
       
class UserRegistrationSerializer(serializers.Serializer):
    email_or_phone_number = serializers.CharField()
    contact_method = serializers.ChoiceField(choices=['EMAIL', 'PHONE'])
    verification_code = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)
    name = serializers.CharField()
    role = serializers.ChoiceField(choices=['USER', 'DRIVER', 'ADMIN'])

class UserLoginSerializer(serializers.Serializer):
    email_or_phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)
    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone_number')
        password = attrs.get('password')

        if not email_or_phone or not password:
            raise serializers.ValidationError("Both fields are required.")

        return attrs

class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    
class TokenResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    token_type = serializers.CharField()
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['vehicle_color_id', 'vehicle_plate_number', 'vehicle_type_id', 
                 'driver_license_number', 'driver_id', 'vehicle_make_id', 'vehicle_model_id']

class ProfileResponseSerializer(serializers.ModelSerializer):
    vehicle_color = serializers.SerializerMethodField()
    vehicle_type = serializers.SerializerMethodField()
    vehicle_make = serializers.SerializerMethodField()
    vehicle_model = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = ['vehicle_color', 'vehicle_plate_number', 'vehicle_type', 
                 'driver_license_number', 'driver_id', 'vehicle_make', 'vehicle_model']
    def get_vehicle_color(self, obj):
        if obj.vehicle_color:
            return {
                'id': obj.vehicle_color.id,
                'name': obj.vehicle_color.name
            }
        else:
            return None
    def get_vehicle_type(self, obj):
        if obj.vehicle_type:
            return {
                'id': obj.vehicle_type.id,
                'name': obj.vehicle_type.name
            }
        else:
            return None
    def get_vehicle_make(self, obj):
        if obj.vehicle_make:
            return {
                'id': obj.vehicle_make.id,
                'name': obj.vehicle_make.name
            }
        else:
            return None
    def get_vehicle_model(self, obj):
        if obj.vehicle_model:
            return {
                'id': obj.vehicle_model.id,
                'name': obj.vehicle_model.name
            }
        else:
            return None

class UserResponseSerializer(serializers.ModelSerializer):
    profile = ProfileResponseSerializer(read_only=True)
    formatted_created_at = serializers.SerializerMethodField()
    formatted_updated_at = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'phone_number', 'email', 'email_verified',
                 'phone_number_verified', 'is_completed', 'formatted_created_at',
                 'formatted_updated_at', 'role', 'profile']

    def get_formatted_created_at(self, obj):
        return obj.formatted_created_at

    def get_formatted_updated_at(self, obj):
        return obj.formatted_updated_at

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['name', 'phone_number', 'email', 'password']

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        return super().create(validated_data)

class CompleteProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['name', 'phone_number', 'email', 'profile']

    def update(self, instance, validated_data):
        profile_data = self.context.get('profile_data', {}).copy()
        try:
            profile = instance.profile
        except Profile.DoesNotExist:
            profile = None
        
        # Update user data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update profile data if user is a driver
        if instance.role == 'DRIVER' and profile_data:
            # Only extract valid Profile fields
            valid_profile_fields = {
                'vehicle_color_id', 'vehicle_color',
                'vehicle_type_id', 'vehicle_type',
                'vehicle_make_id','vehicle_make',
                'vehicle_model_id','vehicle_model',
                'vehicle_plate_number',
                'driver_license_number',
                'driver_id'
            }
            
            # Filter profile_data to only include valid Profile fields
            filtered_profile_data = {
                k: v for k, v in profile_data.items() 
                if k in valid_profile_fields and v is not None and v != ''
            }
            
            # Handle foreign key fields - convert IDs to instances
            if 'vehicle_color_id' in filtered_profile_data:
                vehicle_color_id = filtered_profile_data.pop('vehicle_color_id')
                if vehicle_color_id:
                    try:
                        filtered_profile_data['vehicle_color'] = VehicleColor.objects.get(id=int(vehicle_color_id))
                    except (ValueError, VehicleColor.DoesNotExist):
                        filtered_profile_data['vehicle_color'] = None
            elif 'vehicle_color' in filtered_profile_data:
                vehicle_color_id = filtered_profile_data.pop('vehicle_color')
                if vehicle_color_id:
                    try:
                        filtered_profile_data['vehicle_color'] = VehicleColor.objects.get(id=int(vehicle_color_id))
                    except (ValueError, VehicleColor.DoesNotExist):
                        filtered_profile_data['vehicle_color'] = None
            
            if 'vehicle_type_id' in filtered_profile_data:
                vehicle_type_id = filtered_profile_data.pop('vehicle_type_id')
                if vehicle_type_id:
                    try:
                        filtered_profile_data['vehicle_type'] = VehicleType.objects.get(id=int(vehicle_type_id))
                    except (ValueError, VehicleType.DoesNotExist):
                        filtered_profile_data['vehicle_type'] = None
            elif 'vehicle_type' in filtered_profile_data:
                vehicle_type_id = filtered_profile_data.pop('vehicle_type')
                if vehicle_type_id:
                    try:
                        filtered_profile_data['vehicle_type'] = VehicleType.objects.get(id=int(vehicle_type_id))
                    except (ValueError, VehicleType.DoesNotExist):
                        filtered_profile_data['vehicle_type'] = None
            
            if 'vehicle_make_id' in filtered_profile_data:
                vehicle_make_id = filtered_profile_data.pop('vehicle_make_id')
                if vehicle_make_id:
                    try:
                        filtered_profile_data['vehicle_make'] = VehicleMake.objects.get(id=int(vehicle_make_id))
                    except (ValueError, VehicleMake.DoesNotExist):
                        filtered_profile_data['vehicle_make'] = None
            elif 'vehicle_make' in filtered_profile_data:
                vehicle_make_id = filtered_profile_data.pop('vehicle_make')
                if vehicle_make_id:
                    try:
                        filtered_profile_data['vehicle_make'] = VehicleMake.objects.get(id=int(vehicle_make_id))
                    except (ValueError, VehicleMake.DoesNotExist):
                        filtered_profile_data['vehicle_make'] = None
            if 'vehicle_model_id' in filtered_profile_data:
                vehicle_model_id = filtered_profile_data.pop('vehicle_model_id')
                if vehicle_model_id:
                    try:
                        filtered_profile_data['vehicle_model'] = VehicleModel.objects.get(id=int(vehicle_model_id))
                    except (ValueError, VehicleModel.DoesNotExist):
                        filtered_profile_data['vehicle_model'] = None
            elif 'vehicle_model' in filtered_profile_data:
                vehicle_model_id = filtered_profile_data.pop('vehicle_model')
                if vehicle_model_id:
                    try:
                        filtered_profile_data['vehicle_model'] = VehicleModel.objects.get(id=int(vehicle_model_id))
                    except (ValueError, VehicleModel.DoesNotExist):
                        filtered_profile_data['vehicle_model'] = None
                        
            if filtered_profile_data:
                if not profile:
                    profile = Profile.objects.create(user=instance, **filtered_profile_data)
                else:
                    for attr, value in filtered_profile_data.items():
                        setattr(profile, attr, value)
                    profile.save()
        
        instance.save()
        return instance

class UserRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = "__all__"
        fields = ['role']

class VerifyComChannelSerializer(serializers.Serializer):
    contact_method = serializers.ChoiceField(choices=['EMAIL', 'PHONE_NUMBER'])
    email_or_phone_number = serializers.CharField()
    verification_code = serializers.CharField(required=False)

class UpdatePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    password = serializers.CharField()
    
# driver 
# Add these serializers to your existing serializers.py

class DriverAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverAvailability
        fields = ['id', 'driver', 'status', 'last_updated']

class DriverRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverRating
        fields = ['id', 'user', 'driver', 'rating', 'comments']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

# business and bid
# Add these serializers to your existing serializers.py

class ParcelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parcel
        fields = ['id', 'business', 'parcel_details', 'dropoff_point', 'status', 
                 'created_at', 'updated_at']

# class BidSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Bid
#         fields = ['id', 'business', 'driver', 'bid_amount', 'status', 'awarded_at',
#                  'cancelled_by', 'cancel_reason', 'cancelled_at']

#     def validate_bid_amount(self, value):
#         if value <= 0:
#             raise serializers.ValidationError("Bid amount must be positive")
#         return value

class BidSerializer(serializers.ModelSerializer):
    formatted_created_at = serializers.SerializerMethodField()
    formatted_updated_at = serializers.SerializerMethodField()
    driver_name = serializers.SerializerMethodField()
    business_code = serializers.SerializerMethodField()
    
    class Meta:
        model = Bid
        fields = [
            'id', 
            'business',
            'business_code', 
            'driver',
            'driver_name',
            'bid_amount',
            'status',
            'formatted_created_at',
            'formatted_updated_at'
        ]
        read_only_fields = ['driver', 'business_code', 'driver_name']

    def validate_bid_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Bid amount must be greater than zero")
        return value

    def validate(self, data):
        # Check if a bid already exists for this business and driver
        request = self.context.get('request')
        if request and request.method == 'POST':
            driver = request.user
            business = data.get('business')
            
            existing_bid = Bid.objects.filter(
                business=business,
                driver=driver
            ).exists()
            
            if existing_bid:
                raise serializers.ValidationError(
                    "You have already placed a bid for this business"
                )
        return data

    def get_formatted_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S") if obj.created_at else ""

    def get_formatted_updated_at(self, obj):
        return obj.updated_at.strftime("%Y-%m-%d %H:%M:%S") if obj.updated_at else ""

    def get_driver_name(self, obj):
        return obj.driver.name if obj.driver else None

    def get_business_code(self, obj):
        return obj.business.new_business_code if obj.business else None
    

class BusinessSerializer(serializers.ModelSerializer):
    parcels = ParcelSerializer(many=True, read_only=True)
    bids = BidSerializer(many=True, read_only=True)
    has_awarded_bid = serializers.SerializerMethodField()
    formatted_created_at = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = ['id', 'new_business_code', 'status', 'priority', 
                 'maximum_waiting_time', 'pickup_point', 'delivery_fee', 
                 'owner', 'formatted_created_at', 'has_awarded_bid', 
                 'parcels', 'bids']

    def get_has_awarded_bid(self, obj):
        return obj.bids.filter(status='AWARDED').exists()

    def get_formatted_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S") if obj.created_at else ""
    
# vehicle color , make ,type, model

class VehicleColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleColor
        fields = ['id', 'name', 'status']

class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ['id', 'name', 'status']

class VehicleMakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleMake
        fields = ['id', 'name', 'status']

class VehicleModelSerializer(serializers.ModelSerializer):
    make_name = serializers.SerializerMethodField()

    class Meta:
        model = VehicleModel
        fields = ['id', 'name', 'make_id', 'make_name', 'status']

    def get_make_name(self, obj):
        return obj.make.name if obj.make else None

    def validate_make_id(self, value):
        if not VehicleMake.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid vehicle make ID")
        return value
    

#  transaction and wallet 

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'user_id', 'active_balance', 'transactional_balance']
        read_only_fields = ['active_balance', 'transactional_balance']

class TransactionalWalletSerializer(serializers.ModelSerializer):
    from_user_name = serializers.SerializerMethodField()
    to_user_name = serializers.SerializerMethodField()
    formatted_scheduled_release_date = serializers.SerializerMethodField()

    class Meta:
        model = TransactionalWallet
        fields = [
            'id', 'from_user_id', 'to_user_id', 'amount', 
            'transaction_type', 'status', 'scheduled_release_date',
            'from_user_name', 'to_user_name', 'formatted_scheduled_release_date'
        ]

    def get_from_user_name(self, obj):
        return obj.from_user.name if obj.from_user else None

    def get_to_user_name(self, obj):
        return obj.to_user.name if obj.to_user else None

    def get_formatted_scheduled_release_date(self, obj):
        return obj.scheduled_release_date.strftime("%Y-%m-%d %H:%M:%S") if obj.scheduled_release_date else None

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

class PaymentTransactionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    formatted_created_at = serializers.SerializerMethodField()

    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'user_id', 'user_name', 'amount', 
            'transaction_type', 'status', 'formatted_created_at', 'transaction_reference'
        ]
        read_only_fields = ['user_id', 'user_name', 'formatted_created_at']

    def get_user_name(self, obj):
        return obj.user.name if obj.user else None

    def get_formatted_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S") if obj.created_at else None

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    

# feedback, geofence ans statistics

class FeedbackSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    driver_name = serializers.SerializerMethodField()
    formatted_created_at = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            'id', 'user_id', 'user_name', 'driver_id', 'driver_name',
            'rating', 'comments', 'formatted_created_at'
        ]

    def get_user_name(self, obj):
        return obj.user.name if obj.user else None

    def get_driver_name(self, obj):
        return obj.driver.name if obj.driver else None

    def get_formatted_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S") if obj.created_at else None

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

class TicketCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCategory
        fields = ['id', 'name', 'description', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class TicketSerializer(serializers.ModelSerializer):
    raised_by_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'raised_by', 'raised_by_name',
            'title', 'category', 'category_name',
            'details', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['raised_by', 'raised_by_name', 'created_at', 'updated_at']

    def get_raised_by_name(self, obj):
        return obj.raised_by.name if obj.raised_by else None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

class GeofenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geofence
        fields = ['id', 'name', 'coordinates', 'radius']

    def validate_radius(self, value):
        if value <= 0:
            raise serializers.ValidationError("Radius must be greater than zero")
        return value

class StatisticsSerializer(serializers.Serializer):
    total_transactions = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    new_users = serializers.IntegerField()
    total_feedback = serializers.IntegerField()
    average_driver_rating = serializers.FloatField()
    total_parcels = serializers.IntegerField()
    total_wallets = serializers.IntegerField()
    completed_transactions = serializers.IntegerField()
    pending_transactions = serializers.IntegerField()
    failed_transactions = serializers.IntegerField()
    average_transaction_amount = serializers.DecimalField(max_digits=10, decimal_places=2)

# Ride booking serializers
class RideSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    driver = UserResponseSerializer(read_only=True)
    driver_id = serializers.SerializerMethodField()
    driver_name = serializers.SerializerMethodField()
    formatted_requested_at = serializers.SerializerMethodField()
    formatted_accepted_at = serializers.SerializerMethodField()
    formatted_completed_at = serializers.SerializerMethodField()
    formatted_started_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Ride
        fields = [
            'id', 'customer', 'customer_name', 'driver','driver_id', 'driver_name',
            'pickup_location', 'dropoff_location', 'pickup_latitude', 'pickup_longitude',
            'dropoff_latitude', 'dropoff_longitude', 'fare', 'estimated_fare',
            'distance', 'estimated_distance', 'estimated_duration', 'status',
            'requested_at', 'formatted_requested_at', 'accepted_at', 'formatted_accepted_at',
            'started_at', 'formatted_started_at', 'completed_at', 'formatted_completed_at',
            'cancelled_at', 'cancelled_by', 'cancel_reason', 'notes',
            'created_at', 'updated_at', 'rating', 'review', 'reviewTags'
        ]
        read_only_fields = ['customer', 'driver', 'accepted_at', 'started_at', 'completed_at', 'cancelled_at']
    def get_driver_id(self, obj):
        return obj.driver.id if obj.driver else None

    def get_customer_name(self, obj):
        return obj.customer.name if obj.customer else None

    def get_driver_name(self, obj):
        return obj.driver.name if obj.driver else None

    def get_formatted_requested_at(self, obj):
        return obj.formatted_requested_at

    def get_formatted_accepted_at(self, obj):
        return obj.formatted_accepted_at

    def get_formatted_completed_at(self, obj):
        return obj.formatted_completed_at

    def get_formatted_started_at(self, obj):
        return obj.started_at.strftime("%Y-%m-%d %H:%M:%S") if obj.started_at else None

    def validate_fare(self, value):
        if value < 0:
            raise serializers.ValidationError("Fare must be greater than or equal to zero")
        return value

    def validate_estimated_fare(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Estimated fare must be greater than or equal to zero")
        return value

class RideCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new ride request"""
    class Meta:
        model = Ride
        fields = [
            'pickup_location', 'dropoff_location', 'pickup_latitude', 'pickup_longitude',
            'dropoff_latitude', 'dropoff_longitude', 'estimated_fare', 'estimated_distance',
            'estimated_duration', 'notes', 'rating', 'review', 'reviewTags'
        ]

    def validate(self, data):
        # Ensure at least pickup and dropoff locations are provided
        if not data.get('pickup_location') or not data.get('dropoff_location'):
            raise serializers.ValidationError("Both pickup and dropoff locations are required")
        return data

class RideCostSerializer(serializers.Serializer):
    pickup_latitude = serializers.CharField(max_length=255)
    pickup_longitude = serializers.CharField(max_length=255)
    dropoff_latitude = serializers.CharField(max_length=255)
    dropoff_longitude = serializers.CharField(max_length=255)
