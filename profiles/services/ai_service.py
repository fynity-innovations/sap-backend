# profiles/services/ai_service.py

import json
import logging
from django.conf import settings
from openai import OpenAI
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class CourseFilterAI:
    def __init__(self):
        self.model = "gpt-4o-mini"

        # Enhanced predefined mappings for better accuracy
        self.level_mappings = {
            "Undergraduate": ["Bachelor", "Bachelors", "Undergraduate", "UG"],
            "Postgraduate": ["Master", "Masters", "Postgraduate", "PG", "Graduate"],
            "Doctorate": ["PhD", "Doctorate", "Doctoral", "Doctor of Philosophy"],
            "Diploma": ["Diploma", "Certificate", "Certification"]
        }

        # Enhanced duration mappings
        self.duration_mappings = {
            "1 Year": ["1 Year", "12 months", "1 year"],
            "2 Years": ["2 Years", "24 months", "2 year"],
            "3 Years": ["3 Years", "36 months", "3 year"],
            "4 Years": ["4 Years", "48 months", "4 year"],
            "5 Years": ["5 Years", "60 months", "5 year"]
        }

        self.field_keywords = {
            "IT & Computer Science": ["computer", "it", "software", "programming", "coding", "artificial", "ai",
                                      "machine learning", "data science", "cybersecurity", "information technology"],
            "Artificial Intelligence": ["artificial", "ai", "machine learning", "ml", "deep learning",
                                        "neural networks", "automation"],
            "Data Science": ["data", "analytics", "statistics", "big data", "visualization", "machine learning"],
            "Business & Management": ["business", "management", "mba", "finance", "marketing", "entrepreneurship",
                                      "leadership"],
            "Healthcare & Medicine": ["health", "medicine", "medical", "nursing", "pharmacy", "healthcare", "clinical"],
            "Psychology & Social": ["psychology", "social", "sociology", "counseling", "mental health", "behavior"],
            "Engineering": ["engineering", "mechanical", "electrical", "civil", "chemical", "aerospace"],
            "Arts & Design": ["art", "design", "graphic", "fashion", "interior", "visual", "creative"],
            "Science & Research": ["science", "research", "biology", "chemistry", "physics", "environmental"],
            "Mathematics": ["mathematics", "math", "statistics", "applied math", "pure math"],
            "Biotechnology": ["biotechnology", "biology", "genetics", "molecular", "bioinformatics"],
            "International Relations": ["international", "relations", "politics", "diplomacy", "global"],
            "Economics & Finance": ["economics", "finance", "accounting", "banking", "investment"]
        }

    def find_best_match(self, target: str, options: List[str], threshold: float = 0.6) -> str:
        """
        Find the best matching option from a list of options
        """
        if not target or not options:
            return ""

        target_lower = target.lower()

        # First try exact match (case-insensitive)
        for option in options:
            if option.lower() == target_lower:
                return option

        # Try partial match
        for option in options:
            if target_lower in option.lower() or option.lower() in target_lower:
                return option

        # Try keyword matching
        for option in options:
            option_words = option.lower().split()
            target_words = target_lower.split()

            # Check if any words match
            for t_word in target_words:
                for o_word in option_words:
                    if t_word == o_word:
                        return option

        return ""

    def map_ai_to_data_level(self, ai_level: str, available_levels: List[str]) -> str:
        """
        Map AI level to actual data level with improved logic
        """
        logger.info(f"Mapping AI level '{ai_level}' to available levels: {available_levels}")

        # Get all possible mappings for the AI level
        possible_levels = self.level_mappings.get(ai_level, [ai_level])

        # Find exact matches first
        for level in possible_levels:
            if level in available_levels:
                logger.info(f"Exact match found: {level}")
                return level

        # Find partial matches
        for level in possible_levels:
            best_match = self.find_best_match(level, available_levels)
            if best_match:
                logger.info(f"Partial match found: {ai_level} -> {best_match}")
                return best_match

        # If no match found, return the original AI level
        logger.warning(f"No match found for level '{ai_level}', returning original")
        return ai_level

    def map_ai_to_data_duration(self, ai_duration: str, available_durations: List[str]) -> str:
        """
        Map AI duration to actual data duration with improved logic
        """
        logger.info(f"Mapping AI duration '{ai_duration}' to available durations: {available_durations}")

        # Get all possible mappings for the AI duration
        possible_durations = self.duration_mappings.get(ai_duration, [ai_duration])

        # Find exact matches first
        for duration in possible_durations:
            if duration in available_durations:
                logger.info(f"Exact match found: {duration}")
                return duration

        # Find partial matches
        for duration in possible_durations:
            best_match = self.find_best_match(duration, available_durations)
            if best_match:
                logger.info(f"Partial match found: {ai_duration} -> {best_match}")
                return best_match

        # If no match found, return the original AI duration
        logger.warning(f"No match found for duration '{ai_duration}', returning original")
        return ai_duration

    def process_student_profile(self, profile_data: Dict[str, Any], course_sample: List[Dict[str, Any]]) -> Dict[
        str, Any]:
        """
        Process student profile and generate intelligent course filters
        """
        try:
            # Extract unique values from course sample with better normalization
            countries_in_data = list(set([
                c.get('country_name', '').strip()
                for c in course_sample
                if c.get('country_name')
            ]))

            levels_in_data = list(set([
                c.get('level', '').strip()
                for c in course_sample
                if c.get('level')
            ]))

            durations_in_data = list(set([
                c.get('duration', '').strip()
                for c in course_sample
                if c.get('duration')
            ]))

            intakes_in_data = list(set([
                c.get('intake', '').strip()
                for c in course_sample
                if c.get('intake')
            ]))

            # Sample course titles with more variety
            course_titles_sample = [
                c.get('course_title', '').strip()
                for c in course_sample[:20]
                if c.get('course_title')
            ]

            # Get price ranges from the data
            prices_in_data = [
                float(c.get('annual_fee_usd', 0))
                for c in course_sample
                if c.get('annual_fee_usd') and c.get('annual_fee_usd') != ''
            ]
            min_price = min(prices_in_data) if prices_in_data else 0
            max_price = max(prices_in_data) if prices_in_data else 50000

            # Convert budget from INR to USD with more flexibility
            budget_inr = profile_data.get('budget', [0])[0] * 100000  # Convert lakhs to rupees
            budget_usd = round(budget_inr / 83, -3)  # Convert to USD and round to nearest 1000

            # Make sure budget is reasonable but more flexible
            budget_usd = max(1000, budget_usd)  # Minimum $1000
            budget_usd = min(100000, budget_usd)  # Increased cap to $100,000 for more options

            # In ai_service.py, update the prompt to be more flexible:

            prompt = f"""You are an expert at matching student preferences to course data.

            STUDENT PROFILE:
            - Countries Wanted: {', '.join(profile_data.get('countries', []))}
            - Target Degree: {profile_data.get('degree', '')}
            - Field Interests: {', '.join(profile_data.get('fields', []))}
            - Preferred Intakes: {', '.join(profile_data.get('intakes', []))}
            - Completed Degree: {profile_data.get('completedDegree', '')}
            - CGPA: {profile_data.get('cgpa', 0)}/10
            - Budget: ₹{profile_data.get('budget', [0])[0]} Lakhs/year (approximately ${budget_usd})

            ACTUAL COURSE DATA:
            Available Countries: {', '.join(countries_in_data)}
            Available Levels: {', '.join(levels_in_data)}
            Available Durations: {', '.join(durations_in_data)}
            Available Intakes: {', '.join(intakes_in_data)}
            Price Range: ${min_price} - ${max_price} USD per year
            Sample Course Titles: {', '.join(course_titles_sample[:10])}

            INSTRUCTIONS:

            1. **countries**: Return array of countries from student preferences that BEST MATCH available countries
            - Use fuzzy matching if exact match not found
            - Example: Student wants "USA" → return ["United States"] if that's in data
            - MUST be array, not string
            - If no matches, return empty array

            2. **level**: Map student's degree to BEST MATCH in available levels
            - "Postgraduate" → "Master" or "Masters"
            - "Undergraduate" → "Bachelor" or "Bachelors"
            - Use exact match if available, otherwise use closest match

            3. **course**: Generate 2-3 relevant keywords from field interests AS A SINGLE STRING
            - For "IT & Computer Science": return "Computer IT Software" (NOT an array)
            - For "Business & Management": return "Business Management MBA" (NOT an array)
            - These will be used for partial matching in course titles

            4. **duration**: Select a duration that's within the reasonable range for the degree
            - For Undergraduate: look for durations between 3-4 years
            - For Postgraduate: look for durations between 1-2 years
            - Return just the number with "Years" (e.g., "3 Years", "1.5 Years")

            5. **intakes**: Return array of student's preferred intakes that BEST MATCH available intakes
            - Be more flexible with matching - "Fall 2026" could match "Fall 2026", "September 2026", or just "Fall"
            - If no exact matches, try to match just the season (Fall, Spring, etc.)
            - MUST be array

            6. **maxBudgetUSD**: Use the calculated budget (${budget_usd})
            - Increase by 20% if needed based on price range in data to provide more options
            - Round to nearest 1000

            7. **searchQuery**: Combine 2-3 most relevant keywords from field interests
            - For "IT & Computer Science": "Computer Science"
            - For "Artificial Intelligence": "AI Machine Learning"
            - For "Business & Management": "Business Management"

            IMPORTANT: Be flexible with matching to ensure results are found. If a filter is too restrictive and would return 0 results, relax it slightly.

            RETURN ONLY THIS JSON (no markdown):
            {{
            "countries": ["array of country names"],
            "level": "exact level from available levels",
            "course": "single string with space-separated keywords",
            "duration": "duration in years (e.g., '3 Years')",
            "intakes": ["array of intake names"],
            "maxBudgetUSD": {budget_usd * 1.2},
            "searchQuery": "2-3 relevant search terms"
            }}"""

            logger.info("Calling OpenAI API...")
            logger.info(f"Student wants countries: {profile_data.get('countries')}")
            logger.info(f"Student wants intakes: {profile_data.get('intakes')}")
            logger.info(f"Budget: ₹{profile_data.get('budget', [0])[0]}L (${budget_usd})")

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You return ONLY valid JSON. No markdown, no explanation. Use the exact mappings provided. Ensure all returned values exist in the available data."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Lower temperature for more consistent results
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response: {response_text}")

            filters = json.loads(response_text)
            logger.info(f"Parsed filters: {filters}")

            # Post-processing and validation
            # Ensure countries is an array
            if isinstance(filters.get('countries'), str):
                filters['countries'] = [filters['countries']] if filters['countries'] else []

            # Ensure intakes is an array
            if isinstance(filters.get('intakes'), str):
                filters['intakes'] = [filters['intakes']] if filters['intakes'] else []

            # Validate and improve country matching
            if filters.get('countries'):
                validated_countries = []
                for country in filters['countries']:
                    best_match = self.find_best_match(country, countries_in_data)
                    if best_match:
                        validated_countries.append(best_match)

                # If no valid countries found, try with original preferences
                if not validated_countries and profile_data.get('countries'):
                    for country in profile_data['countries']:
                        best_match = self.find_best_match(country, countries_in_data)
                        if best_match:
                            validated_countries.append(best_match)

                filters['countries'] = validated_countries

            # Validate and improve level matching using the new mapping function
            if filters.get('level'):
                mapped_level = self.map_ai_to_data_level(filters['level'], levels_in_data)
                if mapped_level != filters['level']:
                    logger.info(f"Level mapped: {filters['level']} -> {mapped_level}")
                    filters['level'] = mapped_level

            # Validate and improve duration matching using the new mapping function
            if filters.get('duration'):
                mapped_duration = self.map_ai_to_data_duration(filters['duration'], durations_in_data)
                if mapped_duration != filters['duration']:
                    logger.info(f"Duration mapped: {filters['duration']} -> {mapped_duration}")
                    filters['duration'] = mapped_duration

            # Validate and improve intake matching
            if filters.get('intakes'):
                validated_intakes = []
                for intake in filters['intakes']:
                    best_match = self.find_best_match(intake, intakes_in_data)
                    if best_match:
                        validated_intakes.append(best_match)

                # If no valid intakes found, try with original preferences
                if not validated_intakes and profile_data.get('intakes'):
                    for intake in profile_data['intakes']:
                        best_match = self.find_best_match(intake, intakes_in_data)
                        if best_match:
                            validated_intakes.append(best_match)

                filters['intakes'] = validated_intakes

            # Ensure maxBudgetUSD is reasonable with increased flexibility
            if filters.get('maxBudgetUSD'):
                try:
                    budget = float(filters['maxBudgetUSD'])
                    # Adjust budget if it's outside the price range
                    if budget < min_price:
                        filters['maxBudgetUSD'] = min_price * 1.5  # 50% above minimum for more options
                    elif budget > max_price:
                        filters['maxBudgetUSD'] = max_price * 1.2  # 20% above maximum if needed
                except (ValueError, TypeError):
                    filters['maxBudgetUSD'] = budget_usd * 1.2  # Default to 20% above calculated

            logger.info(f"Final filters after validation: {filters}")

            return {
                'success': True,
                'filters': filters
            }

        except Exception as e:
            logger.error(f"Error in AI service: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

            # Fallback to basic filters if AI fails
            return self._fallback_filters(profile_data, course_sample)

    def _fallback_filters(self, profile_data: Dict[str, Any], course_sample: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback method to generate basic filters if AI service fails
        """
        logger.info("Using fallback filter generation")

        # Extract unique values from course sample
        countries_in_data = list(set([
            c.get('country_name', '').strip()
            for c in course_sample
            if c.get('country_name')
        ]))

        levels_in_data = list(set([
            c.get('level', '').strip()
            for c in course_sample
            if c.get('level')
        ]))

        intakes_in_data = list(set([
            c.get('intake', '').strip()
            for c in course_sample
            if c.get('intake')
        ]))

        # Enhanced basic mappings
        student_degree = profile_data.get('degree', '')
        level = ""

        if student_degree == "Postgraduate":
            # Look for Master or Masters
            for l in levels_in_data:
                if "master" in l.lower():
                    level = l
                    break
        elif student_degree == "Undergraduate":
            # Look for Bachelor or Bachelors
            for l in levels_in_data:
                if "bachelor" in l.lower():
                    level = l
                    break

        # Country matching
        countries = []
        for country in profile_data.get('countries', []):
            match = self.find_best_match(country, countries_in_data)
            if match:
                countries.append(match)

        # Intake matching
        intakes = []
        for intake in profile_data.get('intakes', []):
            match = self.find_best_match(intake, intakes_in_data)
            if match:
                intakes.append(match)

        # Budget conversion with more flexibility
        budget_inr = profile_data.get('budget', [20])[0] * 100000
        budget_usd = round(budget_inr / 83, -3)
        budget_usd = budget_usd * 1.3  # Add 30% flexibility

        # Field keywords
        fields = profile_data.get('fields', [])
        search_query = " ".join(fields[:2]) if fields else ""

        return {
            'success': True,
            'filters': {
                'countries': countries,
                'level': level,
                'course': fields[0] if fields else "",
                'duration': "",
                'intakes': intakes,
                'maxBudgetUSD': budget_usd,
                'searchQuery': search_query
            }
        }