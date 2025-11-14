import csv
import random
import os
from django.core.management.base import BaseCommand, CommandError

# List of example names for different store types
GROCERY_NAMES = [
    "Migros", "CarrefourSA", "Şok", "BİM", "A101", "Macrocenter", "File", "Metro",
    "Local Market", "Farmer's Stand", "Özdilek", "Happy Center"
]
CLOTHING_NAMES = [
    "Zara", "H&M", "Mango", "Pull&Bear", "Stradivarius", "Flo", "Defacto",
    "LCWaikiki", "Mavi", "Colin's", "Adidas Outlet", "Nike Store"
]

# Define a bounding box for Istanbul, Turkey (approximate values)
# We will generate coordinates within this range for realism.
MIN_LAT = 40.8
MAX_LAT = 41.2
MIN_LON = 28.5
MAX_LON = 29.5

class Command(BaseCommand):
    help = 'Generates random store data (name, lat, lon) and saves it to a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('output_file', type=str, help='The path and name of the output CSV file.')
        parser.add_argument('--model', type=str, required=True, choices=['grocery', 'clothing'],
                            help='The type of store data to generate (grocery or clothing).')
        parser.add_argument('--count', type=int, default=50,
                            help='The number of records to generate (default: 50).')

    def handle(self, *args, **options):
        file_path = options['output_file']
        model_type = options['model']
        count = options['count']

        if count <= 0:
            raise CommandError('Count must be a positive number.')

        # 1. Select the name pool based on the model flag
        if model_type == 'grocery':
            name_pool = GROCERY_NAMES
        elif model_type == 'clothing':
            name_pool = CLOTHING_NAMES

        self.stdout.write(self.style.NOTICE(f'Generating {count} records for {model_type} stores...'))

        data = []
        for i in range(count):
            # 2. Randomly pick a name and append a unique identifier
            base_name = random.choice(name_pool)
            store_name = f"{base_name} #{i+1}"

            # 3. Generate random coordinates within the defined bounding box
            latitude = round(random.uniform(MIN_LAT, MAX_LAT), 6)
            longitude = round(random.uniform(MIN_LON, MAX_LON), 6)

            # 4. Append to the data list
            data.append({
                'name': store_name,
                'latitude': latitude,
                'longitude': longitude
            })

        # 5. Write the data to the specified CSV file
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'latitude', 'longitude']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                writer.writerows(data)

            self.stdout.write(self.style.SUCCESS(f'Successfully generated {count} records and saved to: {file_path}'))

        except Exception as e:
            raise CommandError(f'An error occurred while writing the file: {e}')
