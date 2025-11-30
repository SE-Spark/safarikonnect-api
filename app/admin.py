from django.contrib import admin
from .models import (
    User, VehicleColor, VehicleMake, VehicleType, VehicleModel,
    Profile, Business, Parcel, Bid, ChatMessage, Company,
    CompanyUser, DeliveryStatus, DriverAvailability, DriverRating,
    Feedback, Geofence, Notification, OTP, PaymentTransaction,
    Ticket, TicketCategory, Wallet, Transaction, TransactionalWallet, Ride
)
# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'name', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'name')

admin.site.register(User, UserAdmin)
admin.site.register(VehicleColor)
admin.site.register(VehicleMake)
admin.site.register(VehicleType)
admin.site.register(VehicleModel)
admin.site.register(Profile)
admin.site.register(Business)
admin.site.register(Parcel)
admin.site.register(Bid)
admin.site.register(ChatMessage)
admin.site.register(Company)
admin.site.register(CompanyUser)
admin.site.register(DeliveryStatus)
admin.site.register(DriverAvailability)
admin.site.register(DriverRating)
admin.site.register(Feedback)
admin.site.register(Geofence)
admin.site.register(Notification)
admin.site.register(OTP)
admin.site.register(PaymentTransaction)
admin.site.register(Ticket)
admin.site.register(TicketCategory)
admin.site.register(Wallet)
admin.site.register(Transaction)
admin.site.register(TransactionalWallet)
admin.site.register(Ride)