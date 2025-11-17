# utils_profile.py - Enhanced Profile Extraction with Better Error Handling
import json
import logging
import re
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from utils import retry_with_exponential_backoff, safe_execute
from config import api_config

logger = logging.getLogger(__name__)

ENHANCED_PROFILE_SYSTEM_PROMPT = """
Extract a comprehensive candidate profile as pure JSON with the following structure:

{
  "target_roles": ["Software Engineer", "Data Scientist"],
  "skills": ["Python", "JavaScript", "Machine Learning"],
  "experience_level": "junior|mid|senior|executive|student|intern",
  "total_experience_months": 24,
  "education_level": "high_school|associate|bachelor|master|phd",
  "locations": ["New York", "San Francisco", "Remote"],
  "remote_preference": true,
  "industries": ["Technology", "Healthcare"],
  "keywords": ["API", "Database", "Agile", "Team Lead"],
  "salary_expectation": {
    "min": 80000,
    "max": 120000,
    "currency": "USD"
  },
  "certifications": ["AWS Certified", "PMP"],
  "languages": ["English", "Spanish"],
  "soft_skills": ["Leadership", "Communication"]
}

Guidelines:
- Extract ALL technical skills mentioned
- Infer experience level from work history and skills
- Estimate total experience in months based on work history
- Include both hard and soft skills
- Identify preferred locations from the resume
- Determine remote work preference from experience or statements
- Extract salary information if mentioned
- Include certifications, courses, and relevant training
- Return only valid JSON, no commentary

RESUME:
"""

class ProfileExtractor:
    """Enhanced profile extraction with better error handling and validation"""
    
    def __init__(self):
        self.model = None
        self._initialize_model()
        
        # Skill categories for better classification
        self.skill_categories = {
            "programming": [
                "python", "java", "javascript", "c++", "c#", "go", "rust", "kotlin", 
                "swift", "php", "ruby", "scala", "r", "matlab", "typescript"
            ],
            "web": [
                "html", "css", "react", "angular", "vue", "node.js", "express", 
                "django", "flask", "spring", "laravel", "bootstrap"
            ],
            "mobile": [
                "android", "ios", "react native", "flutter", "xamarin", "ionic"
            ],
            "database": [
                "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", 
                "cassandra", "oracle", "sqlite"
            ],
            "cloud": [
                "aws", "azure", "gcp", "docker", "kubernetes", "terraform", 
                "ansible", "jenkins", "circleci"
            ],
            "data_science": [
                "machine learning", "deep learning", "tensorflow", "pytorch", 
                "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn", 
                "jupyter", "tableau", "power bi"
            ],
            "soft_skills": [
                "leadership", "communication", "teamwork", "project management",
                "problem solving", "analytical thinking", "creativity", "adaptability"
            ]
        }
    
    def _initialize_model(self):
        """Initialize the Gemini model"""
        try:
            if not api_config.google_api_key:
                logger.error("Google API key not configured")
                return
                
            genai.configure(api_key=api_config.google_api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            logger.info("Gemini model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.model = None
    
    def _clean_json_response(self, response_text: str) -> str:
        """Clean and extract JSON from AI response"""
        if not response_text:
            return "{}"
        
        # Remove markdown code blocks if present
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        # Find JSON content between braces
        start = response_text.find("{")
        end = response_text.rfind("}")
        
        if start != -1 and end != -1 and end > start:
            json_str = response_text[start:end+1]
        else:
            logger.warning("No valid JSON structure found in response")
            return "{}"
        
        return json_str
    
    def _validate_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted profile"""
        validated_profile = {}
        
        # Required fields with defaults
        validated_profile["target_roles"] = profile.get("target_roles", [])[:10]  # Limit to 10
        validated_profile["skills"] = profile.get("skills", [])[:50]  # Limit to 50 skills
        validated_profile["experience_level"] = profile.get("experience_level", "junior")
        
        # Validate experience level
        valid_exp_levels = ["student", "intern", "junior", "mid", "senior", "executive"]
        if validated_profile["experience_level"] not in valid_exp_levels:
            validated_profile["experience_level"] = "junior"
        
        # Validate total experience
        total_exp = profile.get("total_experience_months", 0)
        validated_profile["total_experience_months"] = max(0, min(total_exp, 600))  # Max 50 years
        
        # Education level
        education = profile.get("education_level", "bachelor")
        valid_edu_levels = ["high_school", "associate", "bachelor", "master", "phd"]
        validated_profile["education_level"] = education if education in valid_edu_levels else "bachelor"
        
        # Optional fields
        validated_profile["locations"] = profile.get("locations", [])[:10]
        validated_profile["remote_preference"] = bool(profile.get("remote_preference", False))
        validated_profile["industries"] = profile.get("industries", [])[:10]
        validated_profile["keywords"] = profile.get("keywords", [])[:20]
        validated_profile["certifications"] = profile.get("certifications", [])[:20]
        validated_profile["languages"] = profile.get("languages", [])[:10]
        validated_profile["soft_skills"] = profile.get("soft_skills", [])[:15]
        
        # Salary expectations
        salary = profile.get("salary_expectation", {})
        if isinstance(salary, dict) and salary:
            validated_profile["salary_expectation"] = {
                "min": salary.get("min"),
                "max": salary.get("max"),
                "currency": salary.get("currency", "USD")
            }
        else:
            validated_profile["salary_expectation"] = None
        
        return validated_profile
    
    def _enhance_skills(self, skills: List[str]) -> List[str]:
        """Enhance skills list by categorizing and normalizing"""
        enhanced_skills = set()
        
        for skill in skills:
            skill_lower = skill.lower().strip()
            if len(skill_lower) < 2:  # Skip too short skills
                continue
            
            # Normalize common variations
            skill_normalized = self._normalize_skill(skill_lower)
            enhanced_skills.add(skill_normalized)
        
        return list(enhanced_skills)
    
    def _normalize_skill(self, skill: str) -> str:
        """Normalize skill names for consistency"""
        normalizations = {
            "js": "javascript",
            "ts": "typescript", 
            "py": "python",
            "ml": "machine learning",
            "ai": "artificial intelligence",
            "db": "database",
            "html5": "html",
            "css3": "css",
            "reactjs": "react",
            "nodejs": "node.js",
            "vuejs": "vue",
            "angularjs": "angular"
        }
        
        return normalizations.get(skill.lower(), skill)
    
    def _infer_missing_data(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Infer missing profile data based on available information"""
        # Infer target roles from skills
        if not profile.get("target_roles") and profile.get("skills"):
            profile["target_roles"] = self._infer_roles_from_skills(profile["skills"])
        
        # Infer experience level from total experience months
        if profile.get("total_experience_months", 0) == 0 and profile.get("experience_level"):
            exp_mapping = {
                "student": 0,
                "intern": 6,
                "junior": 24,
                "mid": 60,
                "senior": 120,
                "executive": 180
            }
            profile["total_experience_months"] = exp_mapping.get(profile["experience_level"], 24)
        
        # Infer keywords from skills and target roles
        if not profile.get("keywords"):
            keywords = set()
            keywords.update(profile.get("skills", [])[:10])  # Add top skills as keywords
            keywords.update(profile.get("target_roles", []))
            profile["keywords"] = list(keywords)
        
        return profile
    
    def _infer_roles_from_skills(self, skills: List[str]) -> List[str]:
        """Infer potential job roles from skills"""
        skill_set = set(skill.lower() for skill in skills)
        role_mappings = {
            "software engineer": ["python", "java", "javascript", "c++", "programming"],
            "data scientist": ["python", "machine learning", "tensorflow", "pandas", "statistics"],
            "web developer": ["html", "css", "javascript", "react", "angular", "node.js"],
            "mobile developer": ["android", "ios", "react native", "flutter", "kotlin", "swift"],
            "devops engineer": ["docker", "kubernetes", "aws", "jenkins", "terraform"],
            "data analyst": ["sql", "excel", "tableau", "power bi", "python", "r"],
            "product manager": ["product management", "agile", "scrum", "roadmap"],
            "project manager": ["project management", "pmp", "scrum", "agile"]
        }
        
        potential_roles = []
        for role, required_skills in role_mappings.items():
            matches = sum(1 for req_skill in required_skills if req_skill in skill_set)
            if matches >= 2:  # Require at least 2 matching skills
                potential_roles.append(role.title())
        
        return potential_roles[:5]  # Return top 5 roles
    
    @retry_with_exponential_backoff(max_retries=3)
    def extract_candidate_profile(self, resume_text: str) -> Dict[str, Any]:
        """Extract enhanced candidate profile from resume text"""
        if not resume_text or not resume_text.strip():
            logger.warning("Empty resume text provided")
            return self._get_default_profile("Empty resume text")
        
        if not self.model:
            logger.error("Gemini model not available")
            return self._get_default_profile("Model not available")
        
        try:
            prompt = f"{ENHANCED_PROFILE_SYSTEM_PROMPT}\n{resume_text}\n"
            
            logger.info("Sending profile extraction request to Gemini")
            response = self.model.generate_content(prompt)


            
            if not response or not response.text:
                logger.warning("Empty response from Gemini")
                return self._get_default_profile("Empty AI response")
            
            # Clean and parse JSON
            json_str = self._clean_json_response(response.text)
            profile = json.loads(json_str)
            
            # Validate and enhance profile
            profile = self._validate_profile(profile)
            profile = self._infer_missing_data(profile)
            
            # Enhance skills
            if profile.get("skills"):
                profile["skills"] = self._enhance_skills(profile["skills"])
            
            logger.info(f"Successfully extracted profile with {len(profile.get('skills', []))} skills")
            return profile
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return self._get_default_profile("JSON parsing error")
        
        except Exception as e:
            logger.error(f"Profile extraction failed: {e}")
            return self._get_default_profile(f"Extraction error: {str(e)}")
    
    def _get_default_profile(self, error_reason: str) -> Dict[str, Any]:
        """Return default profile when extraction fails"""
        return {
            "target_roles": [],
            "skills": [],
            "experience_level": "junior",
            "total_experience_months": 0,
            "education_level": "bachelor",
            "locations": [],
            "remote_preference": False,
            "industries": [],
            "keywords": [],
            "certifications": [],
            "languages": ["English"],
            "soft_skills": [],
            "salary_expectation": None,
            "error": f"Profile extraction failed: {error_reason}"
        }
    
    def get_profile_summary(self, profile: Dict[str, Any]) -> str:
        """Generate a readable summary of the extracted profile"""
        if profile.get("error"):
            return f"❌ {profile['error']}"
        
        summary_parts = []
        
        # Experience level
        exp_level = profile.get("experience_level", "Unknown").title()
        exp_months = profile.get("total_experience_months", 0)
        exp_years = exp_months / 12 if exp_months > 0 else 0
        summary_parts.append(f"**Experience:** {exp_level} level")
        if exp_years > 0:
            summary_parts.append(f"({exp_years:.1f} years)")
        
        # Skills
        skills = profile.get("skills", [])
        if skills:
            top_skills = skills[:5]
            summary_parts.append(f"**Top Skills:** {', '.join(top_skills)}")
        
        # Target roles
        roles = profile.get("target_roles", [])
        if roles:
            summary_parts.append(f"**Target Roles:** {', '.join(roles[:3])}")
        
        # Location preferences
        locations = profile.get("locations", [])
        remote_pref = profile.get("remote_preference", False)
        location_text = "Remote preferred" if remote_pref else ", ".join(locations[:2])
        if location_text:
            summary_parts.append(f"**Location:** {location_text}")
        
        return " | ".join(summary_parts)

# Global instance for backward compatibility
profile_extractor = ProfileExtractor()

def extract_candidate_profile(resume_text: str) -> Dict[str, Any]:
    """Backward compatible function"""
    return profile_extractor.extract_candidate_profile(resume_text)
