# matching.py - Enhanced Job Matching Algorithm with ML and NLP
import re
import logging
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass, field
from collections import Counter
import math
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class MatchingFeatures:
    """Features extracted for job matching"""
    skill_matches: int = 0
    keyword_matches: int = 0
    title_relevance: float = 0.0
    location_match: float = 0.0
    experience_match: float = 0.0
    industry_match: float = 0.0
    company_size_match: float = 0.0
    salary_compatibility: float = 0.0
    remote_preference: float = 0.0
    education_match: float = 0.0
    
    def get_feature_vector(self) -> List[float]:
        """Get feature vector for ML algorithms"""
        return [
            self.skill_matches,
            self.keyword_matches,
            self.title_relevance,
            self.location_match,
            self.experience_match,
            self.industry_match,
            self.company_size_match,
            self.salary_compatibility,
            self.remote_preference,
            self.education_match
        ]

@dataclass
class EnhancedCandidateProfile:
    """Enhanced candidate profile with more sophisticated matching data"""
    # Basic info
    skills: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    target_roles: List[str] = field(default_factory=list)
    
    # Experience and education
    total_experience_months: int = 0
    experience_level: str = "junior"  # junior, mid, senior, executive
    education_level: str = "bachelor"  # high_school, associate, bachelor, master, phd
    industries: List[str] = field(default_factory=list)
    
    # Preferences
    preferred_locations: List[str] = field(default_factory=list)
    remote_preference: bool = False
    salary_expectation_min: Optional[float] = None
    salary_expectation_max: Optional[float] = None
    preferred_company_sizes: List[str] = field(default_factory=list)  # startup, small, medium, large
    
    # Advanced features
    skill_proficiency: Dict[str, float] = field(default_factory=dict)  # skill -> proficiency (0-1)
    career_progression: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)

class TextProcessor:
    """Enhanced text processing for better matching"""
    
    @staticmethod
    def tokenize_advanced(text: str) -> List[str]:
        """Advanced tokenization that preserves technical terms"""
        if not text:
            return []
        
        # Patterns for technical terms, programming languages, etc.
        patterns = [
            r'[A-Za-z0-9+#\.]{2,}',  # Technical terms like C++, .NET, Node.js
            r'\b[A-Z]{2,}\b',        # Acronyms like AWS, API, SQL
            r'\b[A-Za-z]+(?:-[A-Za-z]+)*\b'  # Hyphenated terms
        ]
        
        tokens = set()
        for pattern in patterns:
            tokens.update(re.findall(pattern, text, re.IGNORECASE))
        
        return list(tokens)
    
    @staticmethod
    def extract_skills(text: str, skill_database: List[str] = None) -> List[str]:
        """Extract skills from text using a skill database"""
        if skill_database is None:
            # Default technical skills database
            skill_database = [
                # Programming languages
                "python", "java", "javascript", "c++", "c#", "go", "rust", "kotlin", "swift",
                "php", "ruby", "scala", "r", "matlab", "sql", "html", "css",
                
                # Frameworks and libraries
                "react", "angular", "vue", "django", "flask", "spring", "node.js", "express",
                "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
                
                # Tools and platforms
                "aws", "azure", "gcp", "docker", "kubernetes", "git", "jenkins", "terraform",
                "ansible", "linux", "windows", "macos",
                
                # Databases
                "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra",
                
                # Soft skills
                "leadership", "communication", "teamwork", "problem-solving", "project management",
                "agile", "scrum", "devops", "machine learning", "data analysis", "data science",
                "artificial intelligence", "cybersecurity"
            ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in skill_database:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        return found_skills

class AdvancedJobMatcher:
    """Advanced job matching with multiple algorithms"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
        
        # Weights for different matching criteria
        self.weights = {
            'skills': 0.25,
            'keywords': 0.15,
            'title': 0.20,
            'location': 0.10,
            'experience': 0.15,
            'industry': 0.05,
            'salary': 0.05,
            'remote': 0.05
        }
    
    def calculate_tf_idf_similarity(self, profile_text: str, job_text: str) -> float:
        """Calculate TF-IDF similarity between profile and job"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform([profile_text, job_text])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except ImportError:
            logger.warning("sklearn not available, using basic similarity")
            return self._basic_text_similarity(profile_text, job_text)
    
    def _basic_text_similarity(self, text1: str, text2: str) -> float:
        """Basic text similarity using Jaccard index"""
        tokens1 = set(self.text_processor.tokenize_advanced(text1))
        tokens2 = set(self.text_processor.tokenize_advanced(text2))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def extract_features(self, job: Dict[str, Any], profile: EnhancedCandidateProfile) -> MatchingFeatures:
        """Extract matching features between job and profile"""
        features = MatchingFeatures()
        
        # Job text for analysis
        job_text = " ".join([
            job.get("title", ""),
            job.get("description", ""),
            job.get("company", "")
        ]).lower()
        
        job_title = job.get("title", "").lower()
        job_location = job.get("location", "").lower()
        
        # 1. Skill matching
        job_skills = self.text_processor.extract_skills(job_text)
        profile_skills_lower = [skill.lower() for skill in profile.skills]
        
        matched_skills = set(job_skills).intersection(set(profile_skills_lower))
        features.skill_matches = len(matched_skills)
        
        # Weight by skill proficiency if available
        if profile.skill_proficiency:
            weighted_skill_score = sum(
                profile.skill_proficiency.get(skill, 0.5) 
                for skill in matched_skills
            )
            features.skill_matches = weighted_skill_score
        
        # 2. Keyword matching
        keywords_lower = [kw.lower() for kw in profile.keywords]
        keyword_matches = sum(1 for kw in keywords_lower if kw in job_text)
        features.keyword_matches = keyword_matches
        
        # 3. Title relevance
        target_roles_lower = [role.lower() for role in profile.target_roles]
        title_matches = sum(1 for role in target_roles_lower if role in job_title)
        features.title_relevance = min(title_matches / max(len(target_roles_lower), 1), 1.0)
        
        # 4. Location matching
        if profile.preferred_locations:
            location_matches = sum(
                1 for loc in profile.preferred_locations 
                if loc.lower() in job_location
            )
            features.location_match = min(location_matches / len(profile.preferred_locations), 1.0)
        
        # 5. Experience matching
        job_exp_keywords = ["junior", "senior", "lead", "manager", "director", "entry", "experienced"]
        job_exp_level = "mid"  # default
        
        for keyword in job_exp_keywords:
            if keyword in job_text:
                if keyword in ["junior", "entry"]:
                    job_exp_level = "junior"
                elif keyword in ["senior", "lead"]:
                    job_exp_level = "senior"
                elif keyword in ["manager", "director"]:
                    job_exp_level = "executive"
                break
        
        exp_compatibility = {
            ("junior", "junior"): 1.0,
            ("junior", "mid"): 0.8,
            ("mid", "junior"): 0.6,
            ("mid", "mid"): 1.0,
            ("mid", "senior"): 0.8,
            ("senior", "mid"): 0.9,
            ("senior", "senior"): 1.0,
            ("senior", "executive"): 0.7,
            ("executive", "senior"): 0.8,
            ("executive", "executive"): 1.0
        }
        
        features.experience_match = exp_compatibility.get(
            (profile.experience_level, job_exp_level), 0.5
        )
        
        # 6. Remote work preference
        remote_indicators = ["remote", "work from home", "wfh", "telecommute", "distributed"]
        job_is_remote = any(indicator in job_text for indicator in remote_indicators)
        
        if profile.remote_preference and job_is_remote:
            features.remote_preference = 1.0
        elif not profile.remote_preference and not job_is_remote:
            features.remote_preference = 0.8
        elif profile.remote_preference and not job_is_remote:
            features.remote_preference = 0.3
        else:
            features.remote_preference = 0.6
        
        # 7. Salary compatibility
        job_salary_min = job.get("salary", (None, None))[0] if job.get("salary") else None
        job_salary_max = job.get("salary", (None, None))[1] if job.get("salary") else None
        
        if (job_salary_min and profile.salary_expectation_min and 
            job_salary_max and profile.salary_expectation_max):
            
            # Check salary overlap
            overlap_start = max(job_salary_min, profile.salary_expectation_min)
            overlap_end = min(job_salary_max, profile.salary_expectation_max)
            
            if overlap_start <= overlap_end:
                features.salary_compatibility = 1.0
            else:
                # Calculate how far apart they are
                gap = min(
                    abs(job_salary_max - profile.salary_expectation_min),
                    abs(profile.salary_expectation_max - job_salary_min)
                )
                max_salary = max(job_salary_max, profile.salary_expectation_max)
                features.salary_compatibility = max(0, 1 - (gap / max_salary))
        else:
            features.salary_compatibility = 0.5  # Neutral if salary info missing
        
        return features
    
    def calculate_composite_score(self, features: MatchingFeatures) -> float:
        """Calculate weighted composite matching score"""
        feature_scores = {
            'skills': min(features.skill_matches / 10, 1.0),  # Normalize to 0-1
            'keywords': min(features.keyword_matches / 5, 1.0),
            'title': features.title_relevance,
            'location': features.location_match,
            'experience': features.experience_match,
            'industry': features.industry_match,
            'salary': features.salary_compatibility,
            'remote': features.remote_preference
        }
        
        weighted_score = sum(
            score * self.weights.get(criterion, 0)
            for criterion, score in feature_scores.items()
        )
        
        return min(weighted_score * 100, 100)  # Scale to 0-100
    
    def score_job(self, job: Dict[str, Any], profile: EnhancedCandidateProfile) -> Tuple[float, MatchingFeatures]:
        """Score a single job against candidate profile"""
        features = self.extract_features(job, profile)
        score = self.calculate_composite_score(features)
        
        logger.debug(f"Job '{job.get('title', 'Unknown')}' scored {score:.1f}")
        return score, features
    
    def rank_jobs(self, jobs: List[Dict[str, Any]], profile: EnhancedCandidateProfile, 
                  top_k: int = 20) -> List[Tuple[float, Dict[str, Any], MatchingFeatures]]:
        """Rank jobs by relevance to candidate profile"""
        scored_jobs = []
        
        for job in jobs:
            try:
                score, features = self.score_job(job, profile)
                scored_jobs.append((score, job, features))
            except Exception as e:
                logger.warning(f"Error scoring job {job.get('title', 'Unknown')}: {e}")
                continue
        
        # Sort by score (descending)
        scored_jobs.sort(key=lambda x: x[0], reverse=True)
        
        logger.info(f"Ranked {len(scored_jobs)} jobs, returning top {min(top_k, len(scored_jobs))}")
        return scored_jobs[:top_k]

def create_enhanced_profile_from_basic(basic_profile: Dict[str, Any]) -> EnhancedCandidateProfile:
    """Convert basic profile to enhanced profile with intelligent defaults"""
    enhanced = EnhancedCandidateProfile()
    
    # Copy basic fields
    enhanced.skills = basic_profile.get("skills", [])
    enhanced.keywords = basic_profile.get("keywords", [])
    enhanced.target_roles = basic_profile.get("target_roles", [])
    
    # Set intelligent defaults based on experience level
    experience_level = basic_profile.get("experience_level", "junior")
    enhanced.experience_level = experience_level
    
    # Estimate experience in months based on level
    experience_mapping = {
        "student": 0,
        "intern": 6,
        "junior": 24,
        "mid": 60,
        "senior": 120,
        "executive": 180
    }
    enhanced.total_experience_months = experience_mapping.get(experience_level, 24)
    
    # Set location preferences
    enhanced.preferred_locations = basic_profile.get("locations", [])
    enhanced.remote_preference = basic_profile.get("remote_preference", False)
    
    return enhanced

# Backward compatibility functions
def score_job(job: Dict[str, Any], profile: Dict[str, Any]) -> int:
    """Backward compatible scoring function"""
    matcher = AdvancedJobMatcher()
    enhanced_profile = create_enhanced_profile_from_basic(profile)
    score, _ = matcher.score_job(job, enhanced_profile)
    return int(score)

def rank_jobs(jobs: List[Dict[str, Any]], profile: Dict[str, Any], top_k: int = 20) -> List[Tuple[int, Dict[str, Any]]]:
    """Backward compatible ranking function"""
    matcher = AdvancedJobMatcher()
    enhanced_profile = create_enhanced_profile_from_basic(profile)
    ranked = matcher.rank_jobs(jobs, enhanced_profile, top_k)
    
    # Convert to old format
    return [(int(score), job) for score, job, _ in ranked]