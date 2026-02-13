# profiles/services/ai_service.py

import json
import logging
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class CourseFilterAI:
    def __init__(self):
        self.model = "gpt-4o-mini"

    def process_student_profile(self, profile_data, course_sample):
        """
        Process student profile and generate intelligent course filters
        """

        # Extract unique values from course sample
        countries_in_data = list(set([c.get('country_name', '') for c in course_sample if c.get('country_name')]))
        levels_in_data = list(set([c.get('level', '') for c in course_sample if c.get('level')]))
        durations_in_data = list(set([c.get('duration', '') for c in course_sample if c.get('duration')]))
        intakes_in_data = list(set([c.get('intake', '') for c in course_sample if c.get('intake')]))

        # Sample course titles
        course_titles_sample = [c.get('course_title', '') for c in course_sample[:10] if c.get('course_title')]

        prompt = f"""You are an expert at matching student preferences to course data.

STUDENT PROFILE:
- Countries Wanted: {', '.join(profile_data.get('countries', []))}
- Target Degree: {profile_data.get('degree', '')}
- Field Interests: {', '.join(profile_data.get('fields', []))}
- Preferred Intakes: {', '.join(profile_data.get('intakes', []))}
- Completed Degree: {profile_data.get('completedDegree', '')}
- CGPA: {profile_data.get('cgpa', 0)}/10
- Budget: ₹{profile_data.get('budget', [0])[0]} Lakhs/year (Indian Rupees)

ACTUAL COURSE DATA:
Available Countries: {', '.join(countries_in_data)}
Available Levels: {', '.join(levels_in_data)}
Available Durations: {', '.join(durations_in_data)}
Available Intakes: {', '.join(intakes_in_data)}
Sample Course Titles: {', '.join(course_titles_sample)}

INSTRUCTIONS:

1. **countries**: Return array of ALL countries from student preferences that match Available Countries
   - Student wants ["Denmark", "USA"] → return ["Denmark", "USA"] if both are in data
   - MUST be array, not string

2. **level**: Map to exact level from Available Levels:
   - "Postgraduate" → "Master"
   - "Undergraduate" → "Bachelor"

3. **course**: Simple keyword from field interest:
   - "IT & Computer Science" → "Computer"
   - "Business & Management" → "Business"

4. **duration**: Based on completed → target:
   - Undergraduate → Postgraduate = "2 Years"
   - Use exact string from Available Durations

5. **intakes**: Return array of student's preferred intakes that match Available Intakes
   - MUST be array
   - Match exactly or find closest (e.g., "Fall 2026" → "Fall 2026")

6. **maxBudgetUSD**: Convert ₹ Lakhs to USD
   - Formula: (budget_lakhs * 100000) / 83
   - ₹20L = 24096 USD
   - Round to nearest 1000

7. **searchQuery**: Combine field keywords
   - "IT & Computer Science" → "Computer Science"

RETURN ONLY THIS JSON (no markdown):
{{
  "countries": ["array of country names"],
  "level": "exact level",
  "course": "keyword",
  "duration": "exact duration",
  "intakes": ["array of intake names"],
  "maxBudgetUSD": number,
  "searchQuery": "search terms"
}}"""

        try:
            logger.info("Calling OpenAI API...")
            logger.info(f"Student wants countries: {profile_data.get('countries')}")
            logger.info(f"Student wants intakes: {profile_data.get('intakes')}")
            logger.info(f"Budget: ₹{profile_data.get('budget', [0])[0]}L")

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You return ONLY valid JSON. No markdown, no explanation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response: {response_text}")

            filters = json.loads(response_text)
            logger.info(f"Parsed filters: {filters}")

            # Validation
            if isinstance(filters.get('countries'), str):
                filters['countries'] = [filters['countries']] if filters['countries'] else []

            if isinstance(filters.get('intakes'), str):
                filters['intakes'] = [filters['intakes']] if filters['intakes'] else []

            # Validate countries
            if filters.get('countries'):
                valid_countries = [c for c in filters['countries'] if c in countries_in_data]
                filters['countries'] = valid_countries or profile_data.get('countries', [])

            # Validate intakes
            if filters.get('intakes'):
                valid_intakes = [i for i in filters['intakes'] if i in intakes_in_data]
                filters['intakes'] = valid_intakes

            logger.info(f"Final filters: {filters}")

            return {
                'success': True,
                'filters': filters
            }

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }