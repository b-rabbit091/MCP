import json
import os
import re
import time

import google.generativeai as genai
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from dotenv import load_dotenv

from coding.models import ICD10, Case


class Command(BaseCommand):
    help = 'Generates realistic case scenarios for ICD10 codes using Gemini API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of cases to generate per batch'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit generation to this many ICD10 codes'
        )
        parser.add_argument(
            '--start-from',
            type=int,
            default=0,
            help='Start from this index in the ICD10 queryset'
        )

    def handle(self, *args, **options):
        load_dotenv()
        # Configure Gemini API
        api_key = os.environ.get('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            self.stderr.write(
                self.style.ERROR('GEMINI_API_KEY not found. Please set it in your environment or settings.'))
            return

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.environ.get('MODEL'))

        # Get ICD10 codes from database
        qs = ICD10.objects.all().order_by('code')

        # Apply limits if specified
        start_from = options['start_from']
        limit = options['limit']

        if limit:
            qs = qs[start_from:start_from + limit]
        else:
            qs = qs[start_from:]

        total = len(qs)

        self.stdout.write(self.style.SUCCESS(f'Generating cases for {total} ICD10 codes'))

        # Process in batches to avoid rate limiting
        batch_size = options['batch_size']
        for i in range(0, total, batch_size):
            batch = qs[i:i + batch_size]
            self.stdout.write(f'Processing batch {i // batch_size + 1} ({i} to {min(i + batch_size, total)})')

            for icd10 in batch:
                try:
                    self._generate_case_for_icd10(icd10, model)
                    # Sleep to avoid hitting rate limits
                    time.sleep(1000)

                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error generating case for {icd10.code}: {str(e)}'))

            self.stdout.write(self.style.SUCCESS(f'Completed batch {i // batch_size + 1}'))

            # Sleep between batches to avoid rate limiting
            if i + batch_size < total:
                self.stdout.write(f'Sleeping for 5 seconds before next batch...')
                time.sleep(1000)

        self.stdout.write(self.style.SUCCESS('All cases generated successfully!'))

    def _generate_case_for_icd10(self, icd10, model):
        prompt = f"""
        I need a realistic medical case scenario for the following ICD10 code:

        Code: {icd10.code}
        Description: {icd10.description}

        Please generate a JSON response with the following format:
        {{
            "title": "Brief, descriptive title for the case",
    "description": "Concise description of the case including the key symptoms and diagnosis. "
        }}
The description should be accurate, short and to the point with maximum 500 characters.
        The case should be clinically accurate, realistic, and detailed enough for medical training purposes.
        Only return the JSON, no other text.
        """

        self.stdout.write(f'Generating case for {icd10.code}: {icd10.description}')

        # Generate content using Gemini
        response = model.generate_content(prompt)
        print(response, type(response))
        print("********")
        if not response.candidates or not response.candidates[0].content.parts:
            raise ValueError("No response generated from Gemini.")

        try:
            # Extract and parse JSON from response
            cleaned = re.sub(r"^```(?:json)?|```$", "", response.text.strip(),
                             flags=re.IGNORECASE | re.MULTILINE).strip()

            case_data = json.loads(cleaned)

            # Create and save the Case
            with transaction.atomic():
                case = Case.objects.create(
                    title=case_data["title"],
                    description=case_data["description"]
                )
                case.icd10_id.add(icd10)

            self.stdout.write(self.style.SUCCESS(f'Created case: {case.title}'))
            return case

        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(f'Failed to parse JSON from Gemini response for {icd10.code}'))
            self.stderr.write(f'Raw response: {response.text}')
            raise
        except KeyError as e:
            self.stderr.write(self.style.ERROR(f'Missing key in JSON response: {str(e)}'))
            self.stderr.write(f'Raw response: {response.text}')
            raise
