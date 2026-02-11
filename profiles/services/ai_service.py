import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI profile evaluation using OpenAI API"""
    
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured")
    
    def evaluate_profile(self, profile_data):
        """Evaluate student profile using AI"""
        if not self.openai_api_key:
            logger.error("OpenAI API key not available")
            return self._get_mock_evaluation(profile_data)
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            prompt = self._build_evaluation_prompt(profile_data)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert education counselor and career advisor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"AI evaluation completed for profile: {profile_data.get('phone')}")
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fallback to mock evaluation
            return self._get_mock_evaluation(profile_data)
    
    def _build_evaluation_prompt(self, profile_data):
        """Build comprehensive evaluation prompt"""
        countries_str = ', '.join(profile_data.get('countries', []))
        fields_str = ', '.join(profile_data.get('fields', []))
        
        prompt = f"""
        You are an expert education counselor. Evaluate the following student profile and provide detailed recommendations:

        Student Profile:
        - Name: {profile_data.get('name', 'N/A')}
        - Target Countries: {countries_str or 'N/A'}
        - Degree: {profile_data.get('degree', 'N/A')}
        - Fields of Study: {fields_str or 'N/A'}
        - CGPA: {profile_data.get('cgpa', 'N/A')}
        - Graduation Year: {profile_data.get('grad_year', 'N/A')}
        - Budget (Lakhs): {profile_data.get('budget_lakh', 'N/A')}

        Please provide a JSON response with the following structure:
        {{
            "score": <int 0-100>,
            "best_countries": [<list of top 5 suitable countries>],
            "recommended_programs": [<list of 5 specific program recommendations>],
            "improvement_tips": [<list of 3-5 actionable improvement suggestions>],
            "assessment_summary": "<brief summary of profile strengths and weaknesses>"
        }}

        Consider:
        1. Academic performance (CGPA)
        2. Budget constraints
        3. Target countries and study fields
        4. Market demand and job prospects
        5. University admission competitiveness

        Be realistic, encouraging, and provide actionable advice.
        """
        
        return prompt
    
    def _get_mock_evaluation(self, profile_data):
        """Fallback mock evaluation for development/testing"""
        logger.info("Using mock AI evaluation")
        
        # Simple scoring logic based on CGPA and budget
        cgpa = float(profile_data.get('cgpa', 0))
        budget = int(profile_data.get('budget_lakh', 0))
        
        # Base score from CGPA (scaled to 60%)
        cgpa_score = min(cgpa * 12, 60)  # 5.0 CGPA = 60 points
        
        # Budget score (scaled to 40%)
        budget_score = min(budget / 2, 40)  # 80 Lakhs = 40 points
        
        total_score = int(cgpa_score + budget_score)
        
        mock_result = {
            "score": min(total_score, 100),
            "best_countries": [
                "United States", "Canada", "United Kingdom", 
                "Australia", "Germany"
            ][:3],
            "recommended_programs": [
                "Computer Science MS", "Data Science MSc",
                "MBA", "Engineering Management",
                "Business Analytics"
            ][:3],
            "improvement_tips": [
                "Improve English proficiency test scores",
                "Gain relevant internship experience",
                "Stronger statement of purpose",
                "Obtain strong recommendation letters"
            ][:3],
            "assessment_summary": f"Profile evaluation completed for {profile_data.get('name', 'student')} with score {min(total_score, 100)}/100."
        }
        
        return {
            'success': True,
            'data': mock_result
        }