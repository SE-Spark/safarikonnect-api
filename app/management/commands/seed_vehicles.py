from django.core.management.base import BaseCommand
from app.models import VehicleColor, VehicleMake, VehicleType, VehicleModel


class Command(BaseCommand):
    help = 'Seed vehicle data (colors, makes, types, and models) into the database'

    def handle(self, *args, **kwargs):
        # Seed Vehicle Colors
        self.stdout.write('Seeding vehicle colors...')
        colors = [
            'Black', 'White', 'Silver', 'Gray', 'Red', 'Blue', 'Green', 
            'Yellow', 'Orange', 'Brown', 'Beige', 'Gold', 'Navy Blue', 
            'Maroon', 'Pink', 'Purple', 'Cream', 'Bronze'
        ]
        
        for color_name in colors:
            color, created = VehicleColor.objects.get_or_create(
                name=color_name,
                defaults={'status': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created color: {color_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Color "{color_name}" already exists.'))

        # Seed Vehicle Types
        self.stdout.write('\nSeeding vehicle types...')
        vehicle_types = [
            'Sedan', 'SUV', 'Hatchback', 'Coupe', 'Convertible', 'Wagon',
            'Pickup Truck', 'Van', 'Minivan', 'Sports Car', 'Luxury Car',
            'Motorcycle', 'Tricycle', 'Bus', 'Truck'
        ]
        
        for type_name in vehicle_types:
            v_type, created = VehicleType.objects.get_or_create(
                name=type_name,
                defaults={'status': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created vehicle type: {type_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Vehicle type "{type_name}" already exists.'))

        # Seed Vehicle Makes
        self.stdout.write('\nSeeding vehicle makes...')
        makes_data = [
            'Toyota', 'Honda', 'Nissan', 'Mazda', 'Subaru', 'Mitsubishi',
            'Suzuki', 'Isuzu', 'Mercedes-Benz', 'BMW', 'Audi', 'Volkswagen',
            'Ford', 'Chevrolet', 'Jeep', 'Hyundai', 'Kia', 'Peugeot',
            'Volvo', 'Lexus', 'Land Rover', 'Range Rover', 'Porsche',
            'Ferrari', 'Lamborghini', 'Bentley', 'Rolls-Royce', 'Tesla'
        ]
        
        makes_dict = {}
        for make_name in makes_data:
            make, created = VehicleMake.objects.get_or_create(
                name=make_name,
                defaults={'status': True}
            )
            makes_dict[make_name] = make
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created make: {make_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Make "{make_name}" already exists.'))

        # Seed Vehicle Models
        self.stdout.write('\nSeeding vehicle models...')
        models_data = {
            'Toyota': [
                'Corolla', 'Camry', 'RAV4', 'Highlander', 'Land Cruiser', 
                'Hilux', 'Prius', 'Yaris', 'Avensis', 'Prado', 'Fortuner'
            ],
            'Honda': [
                'Civic', 'Accord', 'CR-V', 'Pilot', 'Fit', 'HR-V', 
                'Odyssey', 'Ridgeline', 'Passport'
            ],
            'Nissan': [
                'Altima', 'Sentra', 'Rogue', 'Pathfinder', 'Murano',
                'X-Trail', 'Navara', 'Patrol', 'Note', 'Juke'
            ],
            'Mercedes-Benz': [
                'C-Class', 'E-Class', 'S-Class', 'GLE', 'GLC', 
                'A-Class', 'B-Class', 'G-Class', 'AMG GT'
            ],
            'BMW': [
                '3 Series', '5 Series', '7 Series', 'X3', 'X5', 
                'X1', 'X6', 'M3', 'M5', 'i8'
            ],
            'Ford': [
                'Focus', 'Fiesta', 'Mustang', 'Explorer', 'Edge',
                'Ranger', 'F-150', 'Escape', 'Expedition'
            ],
            'Volkswagen': [
                'Golf', 'Jetta', 'Passat', 'Tiguan', 'Touareg',
                'Polo', 'Beetle', 'Atlas'
            ],
            'Audi': [
                'A3', 'A4', 'A6', 'A8', 'Q3', 'Q5', 'Q7', 'TT', 'R8'
            ],
            'Hyundai': [
                'Elantra', 'Sonata', 'Tucson', 'Santa Fe', 'Kona',
                'Accent', 'Veloster', 'Palisade'
            ],
            'Kia': [
                'Optima', 'Forte', 'Sorento', 'Sportage', 'Rio',
                'Soul', 'Telluride', 'Stinger'
            ],
            'Mazda': [
                'Mazda3', 'Mazda6', 'CX-5', 'CX-9', 'MX-5', 'CX-3'
            ],
            'Suzuki': [
                'Swift', 'Vitara', 'SX4', 'Grand Vitara', 'Jimny', 'Baleno'
            ],
            'Isuzu': [
                'D-Max', 'MU-X', 'Trooper', 'Rodeo'
            ],
            'Honda': [
                'Civic', 'Accord', 'CR-V', 'Pilot', 'Fit', 'HR-V'
            ],
            'Peugeot': [
                '208', '308', '508', '3008', '5008', '2008'
            ],
            'Subaru': [
                'Impreza', 'Legacy', 'Outback', 'Forester', 'BRZ', 'Ascent'
            ],
            'Mitsubishi': [
                'Outlander', 'Pajero', 'Lancer', 'Eclipse Cross', 'Triton'
            ],
            'Lexus': [
                'ES', 'GS', 'LS', 'RX', 'NX', 'GX', 'LX'
            ],
            'Land Rover': [
                'Discovery', 'Range Rover', 'Defender', 'Evoque', 'Velar'
            ],
            'Jeep': [
                'Wrangler', 'Grand Cherokee', 'Cherokee', 'Compass', 'Renegade'
            ],
            'Chevrolet': [
                'Cruze', 'Malibu', 'Equinox', 'Tahoe', 'Silverado', 'Camaro'
            ],
            'Tesla': [
                'Model S', 'Model 3', 'Model X', 'Model Y', 'Roadster'
            ]
        }
        
        for make_name, model_names in models_data.items():
            make = makes_dict.get(make_name)
            if not make:
                self.stdout.write(self.style.ERROR(f'Make "{make_name}" not found. Skipping models.'))
                continue
                
            for model_name in model_names:
                model, created = VehicleModel.objects.get_or_create(
                    name=model_name,
                    make=make,
                    defaults={'status': True}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created model: {make_name} {model_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Model "{make_name} {model_name}" already exists.'))

        self.stdout.write(self.style.SUCCESS('\n✅ Vehicle seeding completed successfully!'))

