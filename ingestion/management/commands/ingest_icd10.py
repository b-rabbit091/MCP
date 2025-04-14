from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from coding.models import ICD10

ICD10_CODES_RESOURCES = settings.RESOURCES


# TODO : if length >3 , then put .

class Command(BaseCommand):
    help = 'Loads ICD-10 codes from a specified file.'

    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str, help='Path to the ICD-10 code file.')
        parser.add_argument('year', type=str, help='The year associated with this ICD-10 data.')

    def handle(self, *args, **options):
        file_path = options['file_name']
        year = options['year']

        file_path = ICD10_CODES_RESOURCES + "/" + "ICD10" + "/" + year + "/" + file_path
        self.stdout.write(self.style.SUCCESS(f'Loading ICD-10 codes from "{file_path}" for year {year}...'))

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_number, line in enumerate(f, 1):
                    parts = line.strip().split(maxsplit=1)  # Split at most once by whitespace
                    if len(parts) == 2:
                        code = parts[0].strip()
                        description = parts[1].strip()

                        try:
                            # Create or update the ICD10 record
                            icd10_obj, created = ICD10.objects.update_or_create(
                                code=code,
                                defaults={'description': description}
                            )
                            if created:
                                self.stdout.write(self.style.SUCCESS(f'Successfully loaded code: {code}'))
                            else:
                                self.stdout.write(self.style.WARNING(f'Updated existing code: {code}'))
                        except Exception as db_error:
                            self.stderr.write(
                                self.style.ERROR(f'Error saving code "{code}" at line {line_number}: {db_error}'))
                    else:
                        self.stderr.write(self.style.ERROR(f'Skipping invalid line {line_number}: "{line.strip()}"'))

            self.stdout.write(self.style.SUCCESS('Successfully finished loading ICD-10 codes.'))

        except FileNotFoundError:
            raise CommandError(f'File not found at path: "{file_path}"')
        except Exception as e:
            raise CommandError(f'An error occurred: {e}')
