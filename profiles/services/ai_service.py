# profiles/ai_service.py

import google.generativeai as genai
import json
from django.conf import settings

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


class CourseFilterAI:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def process_student_profile(self, profile_data, course_sample):
        """
        Process student profile and generate intelligent course filters
        """
        prompt = f"""You are a course filter expert. Analyze the student profile and generate appropriate course filters.

Student Profile:
- Preferred Countries: {', '.join(profile_data.get('countries', []))}
- Target Degree: {profile_data.get('degree', '')}
- Fields of Interest: {', '.join(profile_data.get('fields', []))}
- Completed Degree: {profile_data.get('completedDegree', '')}
- CGPA: {profile_data.get('cgpa', 0)}/10
- Graduation Year: {profile_data.get('gradYear', '')}
- Budget: ₹{profile_data.get('budget', [0])[0]} Lakhs per year (Indian Rupees)

Course Data Sample (to understand available options):
{json.dumps(course_sample[:20], indent=2)}

Task: Generate URL query parameters for filtering courses. Consider:

1. **Country Mapping**: Use exact country names from the course data
   - Match student's preferred countries to available countries

2. **Level Mapping**: Map target degree to course levels:
   - "Undergraduate" → "Bachelor" or "Undergraduate"
   - "Postgraduate" → "Master" or "Postgraduate" or "MSc" or "MA"
   - "Doctorate" → "PhD" or "Doctorate" or "Doctoral"
   - "Diploma" → "Diploma" or "Certificate"

3. **Field/Course Mapping**: Match interest fields to actual course titles intelligently:
   - "IT & Computer Science" → search for courses containing: "Computer", "IT", "Software", "Data", "AI", "Machine Learning", "Cyber", "Information Technology", "Computing"
   - "Business & Management" → "Business", "Management", "MBA", "Finance", "Economics", "Marketing", "Accounting"
   - "Healthcare & Medicine" → "Medicine", "Health", "Nursing", "Medical", "Clinical", "Pharmacy", "Biomedical"
   - "Psychology & Social" → "Psychology", "Social", "Sociology", "Counseling", "Behavior"

4. **Duration Mapping**: Based on completed degree and target degree:
   - High School → Undergraduate = "3 Years" or "4 Years"
   - Undergraduate → Postgraduate = "1 Year", "1.5 Years", or "2 Years"
   - Postgraduate → Doctorate = "3 Years" or "4 Years"

5. **Budget Conversion**: Convert ₹{profile_data.get('budget', [0])[0]} Lakhs to USD/Euros:
   - Conversion rates: ₹1 Lakh ≈ $1,200 USD ≈ €1,100 EUR
   - Calculate max tuition_fees threshold in USD
   - Example: ₹20L = ~$24,000 or ~€22,000

6. **Search Query**: Generate a general search term based on fields of interest that will match course titles

CRITICAL: Return ONLY a valid JSON object with NO markdown formatting, NO code blocks, NO explanation.
Just the raw JSON object with this exact structure:

{{
  "country": "exact country name from course data or empty string",
  "level": "exact level name that matches course data or empty string",
  "course": "specific search term for course title based on field of interest",
  "duration": "duration string like '2 Years' or '1 Year' or empty string",
  "maxBudgetUSD": numeric value or null,
  "searchQuery": "general search term combining field keywords"
}}

Example response format:
{{
  "country": "Denmark",
  "level": "Master",
  "course": "Computer Science Engineering",
  "duration": "2 Years",
  "maxBudgetUSD": 24000,
  "searchQuery": "Computer Science Software Engineering Technology"
}}

Remember: Return ONLY the JSON object, nothing else."""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            # Parse JSON
            filters = json.loads(response_text)

            return {
                'success': True,
                'filters': filters
            }

        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Failed to parse AI response: {str(e)}',
                'raw_response': response_text
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'AI processing failed: {str(e)}'
            }