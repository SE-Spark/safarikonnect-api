from rest_framework import viewsets, status
from rest_framework import serializers,filters
from django.utils import timezone
from datetime import timedelta,datetime, timezone
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count,Sum
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import (
    UserCreateSerializer, UserResponseSerializer, UserRoleUpdateSerializer,
    CompleteProfileSerializer, VerifyComChannelSerializer, UpdatePasswordSerializer,
    DriverAvailabilitySerializer, DriverRatingSerializer,BusinessSerializer, BidSerializer,
    VehicleColorSerializer, VehicleTypeSerializer,
    VehicleMakeSerializer, VehicleModelSerializer,WalletSerializer, RefreshTokenSerializer,
    TransactionalWalletSerializer, PaymentTransactionSerializer,ResetPasswordSerializer,
    GeofenceSerializer,FeedbackSerializer,StatisticsSerializer,VerifyPasswordResetCodeSerializer,
    UserRegistrationSerializer, UserLoginSerializer,PasswordResetRequestSerializer,
    TokenResponseSerializer, UserResponseSerializer,ChangePasswordSerializer, UserRegistrationOTPSerializer,
    RideSerializer, RideCreateSerializer, TicketSerializer, TicketCategorySerializer, RideCostSerializer
)
from .models import (
    DriverAvailability, DriverRating,Business, Bid, VehicleColor, VehicleType,
    VehicleMake, VehicleModel,Wallet, TransactionalWallet, PaymentTransaction,
    Feedback,Transaction, Geofence, Parcel, OTP, Ride, Ticket, TicketCategory
    )
from .utils import generate_verification_code, send_verification_email, send_verification_sms
from .costcalculator import CostComputationModule
from .payment import PaymentProcessingModule
from drf_yasg.utils import swagger_auto_schema
import uuid

User = get_user_model()

# auth routes

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=UserRegistrationOTPSerializer, responses={200: "OTP sent successfully", 400: "Invalid phone number"})
    @action(detail=False, methods=['post'])
    def registration_otp(self, request):
        serializer = UserRegistrationOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email_or_phone = serializer.validated_data['email_or_phone_number']
        contact_method = serializer.validated_data['contact_method']

        # Check if user exists
        if User.objects.filter(email=email_or_phone).exists() or User.objects.filter(phone_number=email_or_phone).exists():
            channel = "Email" if contact_method == 'EMAIL' else "Phone number"
            return Response(
                {"detail": f"{channel} already taken"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not contact_method:
            return Response(
                {"detail": "Verification failed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Send verification code
        otp_code = generate_verification_code()
        OTP.objects.create(contact_info=email_or_phone,otp_code=otp_code,expires_at=datetime.now(timezone.utc) + timedelta(seconds=300))
        
        if "@" in email_or_phone:
            send_verification_email(email_or_phone, otp_code)
        else:
            send_verification_sms(email_or_phone, otp_code)
        return Response({"message": "Verification code sent"})

    @swagger_auto_schema(request_body=UserRegistrationSerializer, responses={200: "User Registered successfully", 400: "Invalid phone number"})
    @action(detail=False, methods=['post'])
    def verify_register_user(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email_or_phone = serializer.validated_data['email_or_phone_number']
        now = datetime.now(timezone.utc)
        code = serializer.validated_data['verification_code']
        if not OTP.objects.filter(contact_info=email_or_phone,otp_code=code, expires_at__gt = now).exists():
            return Response(
                {"detail": "Invalid verification code"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Invalidate OTP
        OTP.objects.filter(contact_info=email_or_phone,otp_code=code).delete()
        # Register user
        user = User.register_user(serializer.validated_data)
        if not user:
            return Response(
                {"detail": "User registration failed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate token
        refresh = RefreshToken.for_user(user)
        

        return Response({
            "message": "User registered successfully",
            "user": UserResponseSerializer(user).data,
            "refresh": str(refresh),
            "access_token": str(refresh.access_token),
            "token_type": "bearer"
        })

    @swagger_auto_schema(request_body=UserLoginSerializer, responses={200: "Login successfully", 400: "Invalid phone number"})
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username=serializer.validated_data['email_or_phone_number']
        password=serializer.validated_data['password']
        user = None
        if "@" in username:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                pass
        else:
            try:
                user = User.objects.get(phone_number=username)
            except User.DoesNotExist:
                pass
                    
        if user is None or not user.check_password(password):
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            "access_token": str(refresh.access_token),
            'refresh': str(refresh),
            "token_type": "bearer",
            "user": UserResponseSerializer(user).data,
            "message": "Login successfully",
        })

    @swagger_auto_schema(request_body=RefreshTokenSerializer, responses={200: "OTP sent successfully", 400: "Invalid phone number"})
    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out"})
        except Exception:
            return Response(
                {"detail": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(request_body=ChangePasswordSerializer, responses={200: "OTP sent successfully", 400: "Invalid phone number"})
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({"message": "Password changed successfully"})
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserResponseSerializer(request.user)
        return Response(serializer.data)
    
    @swagger_auto_schema(request_body=PasswordResetRequestSerializer, responses={200: "OTP sent successfully", 400: "User not found"})
    @action(detail=False, methods=['post'])
    def forget_password(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email_or_phone = serializer.validated_data['email_or_phone_number']
        
        # Check if user exists
        user = None
        if "@" in email_or_phone:
            try:
                user = User.objects.get(email=email_or_phone)
            except User.DoesNotExist:
                pass
        else:
            try:
                user = User.objects.get(phone_number=email_or_phone)
            except User.DoesNotExist:
                pass
        
        if not user:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate and send OTP
        otp_code = generate_verification_code()
        OTP.objects.create(
            contact_info=email_or_phone,
            otp_code=otp_code,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=300)
        )
        
        if "@" in email_or_phone:
            send_verification_email(email_or_phone, otp_code)
        else:
            send_verification_sms(email_or_phone, otp_code)
        
        return Response({"message": "Password reset code sent successfully"})
    
    @swagger_auto_schema(request_body=ResetPasswordSerializer, responses={200: "Password reset successfully", 400: "Invalid verification code"})
    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email_or_phone = serializer.validated_data['email_or_phone_number']
        verification_code = serializer.validated_data['verification_code']
        new_password = serializer.validated_data['new_password']
        now = datetime.now(timezone.utc)
        
        # Verify OTP
        if not OTP.objects.filter(
            contact_info=email_or_phone,
            otp_code=verification_code,
            expires_at__gt=now
        ).exists():
            return Response(
                {"detail": "Invalid or expired verification code"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user
        user = None
        if "@" in email_or_phone:
            try:
                user = User.objects.get(email=email_or_phone)
            except User.DoesNotExist:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            try:
                user = User.objects.get(phone_number=email_or_phone)
            except User.DoesNotExist:
                return Response(
                    {"detail": "User not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Invalidate OTP
        OTP.objects.filter(contact_info=email_or_phone, otp_code=verification_code).delete()
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        return Response({"message": "Password reset successfully"})

# user
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'complete_profile':
            return CompleteProfileSerializer
        elif self.action == 'update_role':
            return UserRoleUpdateSerializer
        return UserResponseSerializer

    def create(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response(
                {"detail": "Only administrators can create users"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_serializer = UserResponseSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response(
                {"detail": "Only administrators can list users"},
                status=status.HTTP_403_FORBIDDEN
            )
        queryset = self.get_queryset()
        serializer = UserResponseSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = UserResponseSerializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def complete_profile(self, request):
        user = request.user
        serializer = CompleteProfileSerializer(
            user, 
            data=request.data,
            context={'profile_data': request.data}
        )
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        
        # Check if profile is complete
        if self._is_profile_complete(updated_user):
            updated_user.is_completed = True
            updated_user.save()
        
        response_serializer = UserResponseSerializer(updated_user)
        return Response(response_serializer.data)

    @action(detail=True, methods=['put'])
    def update_role(self, request, pk=None):
        user = self.get_object()
        current_user = request.user

        # Check if current user is admin
        if current_user.role != 'ADMIN':
            return Response(
                {"detail": "Only administrators can update user roles"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Prevent admin from changing their own role
        if current_user.id == user.id:
            return Response(
                {"detail": "Administrators cannot change their own role"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UserRoleUpdateSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        response_serializer = UserResponseSerializer(updated_user)
        return Response(response_serializer.data)

    @action(detail=False, methods=['post'])
    def verify_email_phonenumber(self, request):
        serializer = VerifyComChannelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contact_info = serializer.validated_data['email_or_phone_number']
        code = generate_verification_code()
        
        # Send verification code
        if '@' in contact_info:
            send_verification_email(contact_info, code)
        else:
            send_verification_sms(contact_info, code)
            
        return Response({"message": "OTP sent successfully"})

    @action(detail=False, methods=['post'])
    def update_password(self, request):
        serializer = UpdatePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            return Response(
                {"detail": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user.set_password(serializer.validated_data['password'])
        user.save()
        return Response({"message": "Password updated successfully"})

    def _is_profile_complete(self, user):
        if user.role == 'DRIVER':
            profile = user.profile
            return all([
                user.name,
                user.phone_number,
                profile.driver_license_number,
                profile.driver_id,
                profile.vehicle_color_id,
                profile.vehicle_plate_number,
                profile.vehicle_type_id
            ])
        return bool(user.name)
    
    
# add for driver 

class DriverViewSet(viewsets.GenericViewSet):
    queryset = DriverAvailability.objects.all()
    serializer_class = DriverAvailabilitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'update_availability':
            return DriverAvailabilitySerializer
        return DriverAvailabilitySerializer
    
    def get_queryset(self):
        return DriverAvailability.objects.all()
    
    
    @action(detail=False, methods=['post'])
    def update_availability(self, request):
        """Update driver's availability status"""
        driver = request.user
        
        availability, created = DriverAvailability.objects.get_or_create(
            driver=driver,
            defaults={'status': request.data.get('status', 'UNAVAILABLE')}
        )
        
        if not created:
            availability.status = request.data.get('status', 'UNAVAILABLE')
            availability.save()
            
        serializer = DriverAvailabilitySerializer(availability)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_availability(self, request):
        """Get current driver's availability"""
        driver = request.user
        availability = DriverAvailability.objects.filter(driver=driver).first()
        
        if not availability:
            return Response(
                {"detail": "No availability record found"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = DriverAvailabilitySerializer(availability)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Get specific driver's availability"""
        try:
            availability = DriverAvailability.objects.get(driver_id=pk)
            serializer = DriverAvailabilitySerializer(availability)
            return Response(serializer.data)
        except DriverAvailability.DoesNotExist:
            return Response(
                {"detail": "No availability record found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def rate_driver(self, request, pk=None):
        """Rate a driver"""
        data = {
            'user': request.user.id,
            'driver': pk,
            'rating': request.data.get('rating'),
            'comments': request.data.get('comments')
        }
        
        serializer = DriverRatingSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def ratings(self, request, pk=None):
        """Get all ratings for a specific driver"""
        ratings = DriverRating.objects.filter(driver_id=pk)
        
        # Calculate average rating
        avg_rating = ratings.aggregate(Avg('rating'))['rating__avg']
        
        serializer = DriverRatingSerializer(ratings, many=True)
        response_data = {
            'ratings': serializer.data,
            'average_rating': round(avg_rating, 2) if avg_rating else None,
            'total_ratings': ratings.count()
        }
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def my_ratings(self, request):
        """Get current driver's ratings"""
        driver = request.user
        ratings = DriverRating.objects.filter(driver=driver)
        
        # Calculate average rating
        avg_rating = ratings.aggregate(Avg('rating'))['rating__avg']
        
        serializer = DriverRatingSerializer(ratings, many=True)
        response_data = {
            'ratings': serializer.data,
            'average_rating': round(avg_rating, 2) if avg_rating else None,
            'total_ratings': ratings.count()
        }
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def available_drivers(self, request):
        """Get list of all available drivers"""
        available_drivers = DriverAvailability.objects.filter(
            status='AVAILABLE'
        ).select_related('driver')
        
        response_data = []
        for availability in available_drivers:
            driver_data = {
                'driver_id': availability.driver.id,
                'name': availability.driver.name,
                'last_updated': availability.last_updated,
                'average_rating': DriverRating.objects.filter(
                    driver=availability.driver
                ).aggregate(Avg('rating'))['rating__avg']
            }
            response_data.append(driver_data)
            
        return Response(response_data)
    
# add business and bid

class BusinessViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Business.objects.all()
        
        # Get query parameters
        priority = self.request.query_params.getlist('priority')
        max_waiting_time = self.request.query_params.get('maximum_waiting_time')
        delivery_fee_min = self.request.query_params.get('delivery_fee_min')
        delivery_fee_max = self.request.query_params.get('delivery_fee_max')
        bid_status = self.request.query_params.get('bid_status')
        
        # Apply filters based on user role
        if user.role == 'DRIVER':
            if bid_status == 'ACCEPTED':
                queryset = queryset.filter(
                    status='AVAILABLE',
                    bids__status='ACCEPTED',
                    bids__driver=user
                )
            elif bid_status == 'AWARDED':
                queryset = queryset.filter(
                    Q(status='AVAILABLE') | Q(status='COMPLETED'),
                    bids__status='AWARDED',
                    bids__driver=user
                )
            else:
                queryset = queryset.filter(status='AVAILABLE')
        elif user.role == 'USER':
            queryset = queryset.filter(owner=user)

        # Apply additional filters
        if priority:
            queryset = queryset.filter(priority__in=priority)
        if max_waiting_time:
            queryset = queryset.filter(maximum_waiting_time__lte=max_waiting_time)
        if delivery_fee_min:
            queryset = queryset.filter(delivery_fee__gte=delivery_fee_min)
        if delivery_fee_max:
            queryset = queryset.filter(delivery_fee__lte=delivery_fee_max)

        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        business = self.get_object()
        new_status = request.data.get('status')
        if new_status:
            business.status = new_status
            business.save()
            serializer = self.get_serializer(business)
            return Response(serializer.data)
        return Response(
            {"detail": "Status not provided"},
            status=status.HTTP_400_BAD_REQUEST
        )

class BidViewSet(viewsets.ModelViewSet):
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bid.objects.all()

    def perform_create(self, serializer):
        business_id = self.request.data.get('business')
        business = Business.objects.get(id=business_id)
        
        # Check if user already has a bid for this business
        existing_bid = Bid.objects.filter(
            business=business,
            driver=self.request.user
        ).first()
        
        if existing_bid:
            raise serializers.ValidationError(
                "You already have a bid for this business"
            )
            
        serializer.save(driver=self.request.user)

    @action(detail=True, methods=['post'])
    def award_bid(self, request, pk=None):
        bid = self.get_object()
        if bid.business.owner != request.user:
            return Response(
                {"detail": "Only business owner can award bids"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        bid.status = 'AWARDED'
        bid.awarded_at = datetime.now(timezone.utc)
        bid.save()
        
        # Update other bids for this business
        Bid.objects.filter(business=bid.business).exclude(id=bid.id).update(
            status='REJECTED'
        )
        
        serializer = self.get_serializer(bid)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel_bid(self, request, pk=None):
        bid = self.get_object()
        if bid.driver != request.user:
            return Response(
                {"detail": "Only bid owner can cancel the bid"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        reason = request.data.get('reason')
        if not reason:
            return Response(
                {"detail": "Cancellation reason is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        bid.status = 'CANCELLED'
        bid.cancelled_by = request.user
        bid.cancel_reason = reason
        bid.cancelled_at = datetime.now(timezone.utc)
        bid.save()
        
        serializer = self.get_serializer(bid)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_bids(self, request):
        bids = Bid.objects.filter(driver=request.user)
        serializer = self.get_serializer(bids, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def business_bids(self, request):
        business_id = request.query_params.get('business_id')
        if not business_id:
            return Response(
                {"detail": "Business ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        bids = Bid.objects.filter(business_id=business_id)
        serializer = self.get_serializer(bids, many=True)
        return Response(serializer.data)
    
# add vehicle color, type, model and make

class VehicleColorViewSet(viewsets.ModelViewSet):
    queryset = VehicleColor.objects.all()
    serializer_class = VehicleColorSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if VehicleColor.objects.filter(name=serializer.validated_data['name']).exists():
            raise serializers.ValidationError("A color with this name already exists")
        serializer.save()

class VehicleTypeViewSet(viewsets.ModelViewSet):
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if VehicleType.objects.filter(name=serializer.validated_data['name']).exists():
            raise serializers.ValidationError("A vehicle type with this name already exists")
        serializer.save()

class VehicleMakeViewSet(viewsets.ModelViewSet):
    queryset = VehicleMake.objects.all()
    serializer_class = VehicleMakeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if VehicleMake.objects.filter(name=serializer.validated_data['name']).exists():
            raise serializers.ValidationError("A vehicle make with this name already exists")
        serializer.save()

class VehicleModelViewSet(viewsets.ModelViewSet):
    queryset = VehicleModel.objects.all()
    serializer_class = VehicleModelSerializer    
    permission_classes = [IsAuthenticated]
    # filter by make_id using filterbackend
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name','make__name','make_id']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        make_id = self.request.query_params.get('make_id', None)
        if make_id is not None:
            queryset = queryset.filter(make_id=make_id)
        return queryset

    def perform_create(self, serializer):
        make_id = serializer.validated_data.get('make_id')
        name = serializer.validated_data.get('name')
        
        # Check if model name exists for the same make
        if VehicleModel.objects.filter(make_id=make_id, name=name).exists():
            raise serializers.ValidationError(
                "A model with this name already exists for this make"
            )
        serializer.save()
        
# add wallet and transaction endpoints

class WalletViewSet(viewsets.GenericViewSet):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """Get current user's wallet"""
        wallet = self.get_queryset().first()
        if not wallet:
            wallet = Wallet.objects.create(user=request.user)
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)

class TransactionalWalletViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionalWalletSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return TransactionalWallet.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        ).order_by('-created_at')

    # Disable default CUD and allow R
    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )    

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['post'])
    def pay(self, request):
        serializer = TransactionalWalletSerializer(data=request.data)        
        from_user = self.request.user
        from_wallet = Wallet.objects.get(user=from_user)
        
        # Validate sufficient balance
        amount = serializer.validated_data['amount']
        if from_wallet.active_balance < amount:
            raise serializers.ValidationError(
                "Insufficient balance for this transaction"
            )
        if serializer.is_valid():
            serializer.save()    
        # Create transaction and update balances
        transaction = serializer.save(from_user=from_user)
        
        # Update wallet balances
        from_wallet.active_balance -= amount
        from_wallet.transactional_balance += amount
        from_wallet.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def top_up_wallet(self, request):
        # we shall implement a payment gateway
        pass

    # @action(detail=True, methods=['post'])
    def release_funds(self, request, pk=None):
        """Release funds for a transaction"""
        transaction = self.get_object()
        
        if transaction.status != 'PENDING':
            return Response(
                {"detail": "Transaction is not in pending state"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if transaction.scheduled_release_date and transaction.scheduled_release_date > datetime.now(timezone.utc):
            return Response(
                {"detail": "Cannot release funds before scheduled date"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update transaction status
        transaction.status = 'COMPLETED'
        transaction.save()
        
        # Update wallet balances
        from_wallet = transaction.from_user.wallet
        to_wallet = transaction.to_user.wallet
        
        from_wallet.transactional_balance -= transaction.amount
        to_wallet.active_balance += transaction.amount
        
        from_wallet.save()
        to_wallet.save()
        
        return Response({"detail": "Funds released successfully"})

class PaymentTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentTransaction.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    # def perform_create(self, serializer):
    #     user = self.request.user
    #     wallet = Wallet.objects.get(user=user)
        
    #     transaction = serializer.save(user=user)
        
    #     # Update wallet balance based on transaction type
    #     amount = transaction.amount
    #     if transaction.transaction_type == 'DEPOSIT':
    #         wallet.active_balance += amount
    #     elif transaction.transaction_type == 'WITHDRAWAL':
    #         if wallet.active_balance < amount:
    #             raise serializers.ValidationError("Insufficient balance")
    #         wallet.active_balance -= amount
            
    #     wallet.save()
    
    # disable create method
    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        ) 
    # disable update method
    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        ) 
    # disable delete method
    def delete(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        ) 
    
    @action(detail=False, methods=['get'])
    def transaction_history(self, request):
        """Get user's transaction history with optional filters"""
        queryset = self.get_queryset()
        
        # Apply filters
        transaction_type = request.query_params.get('type')
        status = request.query_params.get('status')
        
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        if status:
            queryset = queryset.filter(status=status)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    # withdraw from wallet
    @action(detail=False, methods=['post'])
    def withdraw(self,request):
        user = request.user
        account_number = request.data.get("account_number",0)
        bank_code = request.data.get("bank_code",0)
        channelType = request.data.get("type","nuban")
        currency =  request.data.get("currency","kes")

        wallet = Wallet.objects.get(user=user)
        if wallet.active_balance < request.data.get("amount",0):
            return Response({'detail': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
        
        transaction = PaymentTransaction.objects.create(
            user=user,
            amount=request.data.get("amount",0),
            transaction_type='WITHDRAWAL',
            status='PENDING',
            transaction_reference=str(uuid.uuid4()),
        )
        recipient = PaymentProcessingModule.create_recipient(name=user.name, account= account_number, bank_code= bank_code, type=channelType,currency=currency)
        if recipient.get('status') == True:
            withdrawal = PaymentProcessingModule.withdraw_from_wallet(amount=request.data.get("amount",0), recipient_code=recipient.get('data').get('recipient_code'), reason='Withdrawal from wallet')
            if withdrawal.get('status') == True:
                transaction.status = 'COMPLETED'
                transaction.save()
                wallet.active_balance -= request.data.get("amount",0)
                wallet.save()
                return Response({'detail': 'Withdrawal successful'}, status=status.HTTP_200_OK)
        # failed case
        transaction.status = 'FAILED'
        transaction.save()
        return Response({'detail': 'Withdrawal failed'}, status=status.HTTP_400_BAD_REQUEST)
    # top up wallet
    @action(detail=False, methods=['post'])
    def top_up(self,request):
        user = request.user
        paymentInfo = {
            "email": user.email,
            "amount": request.data.get("amount",100),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone_number,
            "currency": request.data.get("currency",None),
        }
        # i will use paystack to initiate payment
        try:
            initializePaymentRes = PaymentProcessingModule.initiatePayment(**paymentInfo)
        except Exception as e:
            print(e)
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        print(initializePaymentRes)
        if initializePaymentRes.get('status') == True:
            transaction = PaymentTransaction.objects.create(
                user=user,
                amount=paymentInfo.get('amount'),
                transaction_type='DEPOSIT',
                transaction_reference=initializePaymentRes.get('data').get('reference'),
                status='PENDING',
            )
            return Response(initializePaymentRes)
        return Response({'detail': 'Payment failed'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify_payment(self,request):
        reference = request.data.get('reference')
        transaction = PaymentTransaction.objects.filter(transaction_reference=reference).first()
        if not reference or not transaction:
            return Response({'detail': 'Reference is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payment = PaymentProcessingModule.verifyPayment(reference)
            print(payment)
            if payment.get('data').get('status') == 'success':
                transaction.status = 'SUCCESS'
                transaction.save()
                wallet = Wallet.objects.get(user=transaction.user)
                wallet.active_balance += transaction.amount
                wallet.save()
                return Response({'detail': 'Payment verified'}, status=status.HTTP_200_OK)                
        except Exception as ex:
            pass
        transaction.status = 'Failed'
        transaction.save()
        return Response({'detail': 'Payment not verified'}, status=status.HTTP_400_BAD_REQUEST)

# add feedback, geofence, ticket and statistics

class FeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'DRIVER':
            return Feedback.objects.filter(driver=user)
        return Feedback.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def driver_feedback(self, request):
        """Get all feedback for a specific driver"""
        driver_id = request.query_params.get('driver_id')
        if not driver_id:
            return Response(
                {"detail": "Driver ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        feedback = Feedback.objects.filter(driver_id=driver_id)
        average_rating = feedback.aggregate(Avg('rating'))['rating__avg']
        
        serializer = self.get_serializer(feedback, many=True)
        return Response({
            'feedback': serializer.data,
            'average_rating': round(average_rating, 2) if average_rating else None,
            'total_feedback': feedback.count()
        })

class TicketCategoryViewSet(viewsets.ModelViewSet):
    queryset = TicketCategory.objects.all()
    serializer_class = TicketCategorySerializer
    permission_classes = [IsAuthenticated]

class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.select_related('raised_by', 'category').order_by('-created_at')
        if user.role == 'ADMIN':
            return queryset
        return queryset.filter(raised_by=user)

    def perform_create(self, serializer):
        serializer.save(raised_by=self.request.user)

class GeofenceViewSet(viewsets.ModelViewSet):
    queryset = Geofence.objects.all()
    serializer_class = GeofenceSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def check_point(self, request, pk=None):
        """Check if a point is within the geofence"""
        geofence = self.get_object()
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        
        if not all([lat, lng]):
            return Response(
                {"detail": "Latitude and longitude are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Implement point-in-polygon check here
        is_inside = self._check_point_in_geofence(geofence, float(lat), float(lng))
        
        return Response({
            "is_inside": is_inside,
            "geofence_name": geofence.name
        })

    def _check_point_in_geofence(self, geofence, lat, lng):
        # Implement your geofence checking logic here
        # This is a simplified example
        from math import radians, sin, cos, sqrt, atan2
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371  # Earth's radius in kilometers
            
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            return distance
            
        # Parse center coordinates from geofence.coordinates
        center_lat, center_lng = map(float, geofence.coordinates.split(','))
        
        # Calculate distance between point and center
        distance = haversine_distance(lat, lng, center_lat, center_lng)
        
        # Check if point is within radius
        return distance <= geofence.radius

class StatisticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get overall statistics"""
        stats = {
            'total_transactions': Transaction.objects.count(),
            'total_amount': Transaction.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(
                last_active__gte=datetime.now(timezone.utc) - timedelta(days=30)
            ).count(),
            'new_users': User.objects.filter(
                created_at__gte=datetime.now(timezone.utc) - timedelta(days=30)
            ).count(),
            'total_feedback': Feedback.objects.count(),
            'average_driver_rating': Feedback.objects.aggregate(
                Avg('rating')
            )['rating__avg'] or 0,
            'total_parcels': Parcel.objects.count(),
            'total_wallets': Wallet.objects.count(),
            'completed_transactions': Transaction.objects.filter(
                status='COMPLETED'
            ).count(),
            'pending_transactions': Transaction.objects.filter(
                status='PENDING'
            ).count(),
            'failed_transactions': Transaction.objects.filter(
                status='FAILED'
            ).count(),
            'average_transaction_amount': Transaction.objects.aggregate(
                Avg('amount')
            )['amount__avg'] or 0
        }
        
        serializer = StatisticsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_statistics(self, request):
        """Get user-specific statistics"""
        user = request.user
        user_stats = {
            'total_transactions': Transaction.objects.filter(
                Q(from_user=user) | Q(to_user=user)
            ).count(),
            'total_amount': Transaction.objects.filter(
                Q(from_user=user) | Q(to_user=user)
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_feedback': Feedback.objects.filter(
                Q(user=user) | Q(driver=user)
            ).count(),
            'average_rating': Feedback.objects.filter(
                driver=user
            ).aggregate(Avg('rating'))['rating__avg'] or 0,
            'completed_transactions': Transaction.objects.filter(
                Q(from_user=user) | Q(to_user=user),
                status='COMPLETED'
            ).count(),
            'pending_transactions': Transaction.objects.filter(
                Q(from_user=user) | Q(to_user=user),
                status='PENDING'
            ).count()
        }
        
        return Response(user_stats)

# Ride booking functionality
class RideViewSet(viewsets.ModelViewSet):
    serializer_class = RideSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Ride.objects.all()
        
        # Filter based on user role
        if user.role == 'DRIVER':
            # Drivers see rides they've accepted or available rides
            status_filter = self.request.query_params.get('status')
            if status_filter == 'available':
                # Show only pending rides that haven't been accepted
                queryset = Ride.objects.filter(status='PENDING', driver__isnull=True)
            elif status_filter == 'my_rides':
                # Show rides accepted by this driver
                queryset = Ride.objects.filter(driver=user)
            else:
                # Default: show all rides (for drivers to see available and their own)
                queryset = Ride.objects.filter(
                    Q(status='PENDING', driver__isnull=True) | Q(driver=user)
                )
        else:
            # Customers see only their own rides
            queryset = Ride.objects.filter(customer=user)
        
        # Additional filtering
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return RideCreateSerializer
        return RideSerializer

    def perform_create(self, serializer):
        # Automatically set customer to current user
        serializer.save(customer=self.request.user)

    @action(detail=False, methods=['post'])
    def cost_of_ride(self, request):
        serializer = RideCostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        coords = {
            'pickup_latitude': float(serializer.validated_data['pickup_latitude']),
            'pickup_longitude': float(serializer.validated_data['pickup_longitude']),
            'dropoff_latitude': float(serializer.validated_data['dropoff_latitude']),
            'dropoff_longitude': float(serializer.validated_data['dropoff_longitude']),
        }

        try:
            cost_response = CostComputationModule.estimate(**coords)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(cost_response)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Driver accepts a ride request"""
        ride = self.get_object()
        driver = request.user
        
        # Check if user is a driver
        if driver.role != 'DRIVER':
            return Response(
                {"detail": "Only drivers can accept rides"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if ride is available
        if ride.status != 'PENDING':
            return Response(
                {"detail": "Ride is not available for acceptance"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if driver already has an active ride
        active_rides = Ride.objects.filter(
            driver=driver,
            status__in=['PENDING', 'ACCEPTED', 'DRIVER_ARRIVED', 'IN_PROGRESS']
        ).exclude(id=ride.id)
        
        if active_rides.exists():
            return Response(
                {"detail": "You already have an active ride"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check driver availability
        driver_availability = DriverAvailability.objects.filter(driver=driver).first()
        if not driver_availability or driver_availability.status != 'AVAILABLE':
            return Response(
                {"detail": "Driver is not available"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Accept the ride
        ride.driver = driver
        ride.status = 'ACCEPTED'
        ride.accepted_at = datetime.now(timezone.utc)
        ride.save()
        
        # Update driver availability to BUSY
        driver_availability.status = 'BUSY'
        driver_availability.save()
        
        serializer = self.get_serializer(ride)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Driver starts the ride (driver has arrived and ride begins)"""
        ride = self.get_object()
        
        # Check if user is the assigned driver
        if ride.driver != request.user:
            return Response(
                {"detail": "Only the assigned driver can start the ride"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if ride can be started
        if ride.status not in ['ACCEPTED', 'DRIVER_ARRIVED']:
            return Response(
                {"detail": f"Ride cannot be started from {ride.status} status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ride.status = 'IN_PROGRESS'
        ride.started_at = datetime.now(timezone.utc)
        ride.save()
        
        serializer = self.get_serializer(ride)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def driver_arrived(self, request, pk=None):
        """Driver marks that they have arrived at pickup location"""
        ride = self.get_object()
        
        # Check if user is the assigned driver
        if ride.driver != request.user:
            return Response(
                {"detail": "Only the assigned driver can mark arrival"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if ride is in correct status
        if ride.status != 'ACCEPTED':
            return Response(
                {"detail": "Ride must be accepted before marking arrival"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ride.status = 'DRIVER_ARRIVED'
        ride.save()
        
        serializer = self.get_serializer(ride)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete the ride"""
        ride = self.get_object()
        
        # Check if user is the assigned driver
        if ride.driver != request.user:
            return Response(
                {"detail": "Only the assigned driver can complete the ride"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if ride can be completed
        if ride.status not in ['IN_PROGRESS', 'DRIVER_ARRIVED']:
            return Response(
                {"detail": f"Ride cannot be completed from {ride.status} status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update fare if provided
        fare = request.data.get('fare')
        if fare is not None:
            ride.fare = fare
        
        ride.status = 'COMPLETED'
        ride.completed_at = datetime.now(timezone.utc)
        ride.save()
        
        # Update driver availability back to AVAILABLE
        driver_availability = DriverAvailability.objects.filter(driver=ride.driver).first()
        if driver_availability:
            driver_availability.status = 'AVAILABLE'
            driver_availability.save()
        
        serializer = self.get_serializer(ride)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel the ride"""
        ride = self.get_object()
        user = request.user
        
        # Check if user is customer or driver
        if ride.customer != user and ride.driver != user:
            return Response(
                {"detail": "Only the customer or driver can cancel the ride"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if ride can be cancelled
        if ride.status in ['COMPLETED', 'CANCELLED']:
            return Response(
                {"detail": "Ride cannot be cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cancel_reason = request.data.get('cancel_reason', '')
        
        ride.status = 'CANCELLED'
        ride.cancelled_by = user
        ride.cancel_reason = cancel_reason
        ride.cancelled_at = datetime.now(timezone.utc)
        ride.save()
        
        # If driver cancelled, update their availability
        if ride.driver and ride.driver == user:
            driver_availability = DriverAvailability.objects.filter(driver=ride.driver).first()
            if driver_availability:
                driver_availability.status = 'AVAILABLE'
                driver_availability.save()
        
        serializer = self.get_serializer(ride)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def available_rides(self, request):
        """Get all available rides for drivers"""
        if request.user.role != 'DRIVER':
            return Response(
                {"detail": "Only drivers can view available rides"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        rides = Ride.objects.filter(status='PENDING', driver__isnull=True)
        serializer = self.get_serializer(rides, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_rides(self, request):
        """Get current user's rides"""
        user = request.user
        
        if user.role == 'DRIVER':
            rides = Ride.objects.filter(driver=user)
        else:
            rides = Ride.objects.filter(customer=user)
        
        serializer = self.get_serializer(rides, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active_ride(self, request):
        """Get current user's active ride (if any)"""
        user = request.user
        
        if user.role == 'DRIVER':
            active_ride = Ride.objects.filter(
                driver=user,
                status__in=['PENDING', 'ACCEPTED', 'DRIVER_ARRIVED', 'IN_PROGRESS']
            ).first()
        else:
            active_ride = Ride.objects.filter(
                customer=user,
                status__in=['PENDING', 'ACCEPTED', 'DRIVER_ARRIVED', 'IN_PROGRESS']
            ).first()
        
        if not active_ride:
            return Response(
                {"detail": "No active ride found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(active_ride)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def rate_ride(self, request, pk=None):
        """Rate the ride"""
        ride = self.get_object()
        rating = request.data.get('rating')
        review = request.data.get('review')
        reviewTags = request.data.get('reviewTags')
        ride.rating = rating
        ride.review = review
        ride.reviewTags = reviewTags
        ride.save()
        return Response({'detail': 'Ride rated successfully'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def payment_webhook(request):
    signature = request.headers.get('X-Paystack-Signature')
    if not signature:
        return Response({'detail': 'Signature is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not PaymentProcessingModule.verifyPayloadHashmac(request.body, signature):
        return Response({'detail': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
    data = request.data
    event = data.get('event')
    if event == 'charge.success':        
        reference = data.get('data').get('reference')
        payment = PaymentProcessingModule.verifyPayment(reference)
        if payment.get('status') == 'success':            
            transaction = PaymentTransaction.objects.filter(transaction_reference=reference).first()
            if transaction:
                transaction.status = 'SUCCESS'
                transaction.save()
                wallet = Wallet.objects.get(user=transaction.user)
                wallet.active_balance += transaction.amount
                wallet.save()
                return Response({'detail': 'Payment received'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Payment failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Invalid event'}, status=status.HTTP_400_BAD_REQUEST)



