# jobs_api_improved.py - Enhanced Job Search APIs with Error Handling and Rate Limiting

import os
import time
import requests
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
import streamlit as st
from config import api_config, app_config
from utils import retry_with_exponential_backoff, cache_key_generator

logger = logging.getLogger(__name__)

@dataclass
class JobResult:
    """Standardized job result structure"""
    title: str
    company: str
    location: str
    description: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    apply_url: Optional[str] = None
    source: str = ""
    date_posted: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description[:500] + "..." if len(self.description) > 500 else self.description,
            "salary": (self.salary_min, self.salary_max) if self.salary_min or self.salary_max else None,
            "apply_url": self.apply_url,
            "source": self.source,
            "date_posted": self.date_posted,
            "job_type": self.job_type,
            "experience_level": self.experience_level
        }

class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, max_calls: int = 60, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def can_make_call(self) -> bool:
        now = datetime.now()
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < timedelta(seconds=self.time_window)]
        return len(self.calls) < self.max_calls

    def record_call(self):
        self.calls.append(datetime.now())

    def wait_if_needed(self):
        if not self.can_make_call():
            wait_time = self.time_window - (datetime.now() - min(self.calls)).total_seconds()
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)

# Rate limiters for different APIs
rate_limiters = {
    "adzuna": RateLimiter(100, 3600),  # 100 calls per hour
    "remotive": RateLimiter(60, 60),   # 60 calls per minute
    "jsearch": RateLimiter(50, 60)     # 50 calls per minute
}

def with_rate_limiting(api_name: str):
    """Decorator to add rate limiting to API calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if api_name in rate_limiters:
                rate_limiters[api_name].wait_if_needed()
                rate_limiters[api_name].record_call()
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_search_params(query: str, location: str = None) -> bool:
    """Validate search parameters"""
    if not query or len(query.strip()) < 2:
        raise ValueError("Search query must be at least 2 characters long")
    if query and len(query) > 100:
        raise ValueError("Search query too long (max 100 characters)")
    if location and len(location) > 50:
        raise ValueError("Location query too long (max 50 characters)")
    return True

class JobSearchCache:
    """Simple in-memory cache for job search results"""
    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[List[JobResult]]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                logger.info(f"Cache hit for key: {key[:20]}...")
                return data
            else:
                del self.cache[key]
        return None

    def set(self, key: str, data: List[JobResult]):
        self.cache[key] = (data, time.time())
        logger.info(f"Cached results for key: {key[:20]}...")

# Global cache instance
job_cache = JobSearchCache(ttl=app_config.cache_ttl)

@with_rate_limiting("adzuna")
@retry_with_exponential_backoff(max_retries=3)
def search_adzuna(query: str, location: str, country_code: str = "in",
                 page: int = 1, results: int = 25) -> List[JobResult]:
    """Search jobs using Adzuna API with enhanced error handling"""
    try:
        validate_search_params(query, location)

        if not api_config.adzuna_app_id or not api_config.adzuna_app_key:
            logger.warning("Adzuna API credentials not configured")
            return []

        cache_key = cache_key_generator("adzuna", query, location, country_code, page, results)
        cached_results = job_cache.get(cache_key)
        if cached_results:
            return cached_results

        base_url = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
        url = base_url.format(country=country_code, page=page)

        params = {
            "app_id": api_config.adzuna_app_id,
            "app_key": api_config.adzuna_app_key,
            "what": query.strip(),
            "where": location.strip() if location else "",
            "results_per_page": min(results, app_config.max_jobs_per_search),
            "content-type": "application/json",
        }

        logger.info(f"Searching Adzuna for '{query}' in '{location}'")

        response = requests.get(
            url,
            params=params,
            timeout=app_config.api_timeout,
            headers={'User-Agent': 'ResumeAnalyzer/1.0'}
        )

        response.raise_for_status()
        data = response.json()

        jobs = []
        for item in data.get("results", []):
            try:
                job = JobResult(
                    title=item.get("title", "N/A"),
                    company=(item.get("company") or {}).get("display_name", "N/A"),
                    location=(item.get("location") or {}).get("display_name", "N/A"),
                    description=item.get("description", "")[:1000],  # Limit description length
                    salary_min=item.get("salary_min"),
                    salary_max=item.get("salary_max"),
                    apply_url=item.get("redirect_url", ""),
                    source="Adzuna",
                    date_posted=item.get("created"),
                    job_type=item.get("contract_type")
                )
                jobs.append(job)
            except Exception as e:
                logger.warning(f"Error parsing Adzuna job item: {e}")
                continue

        logger.info(f"Retrieved {len(jobs)} jobs from Adzuna")
        job_cache.set(cache_key, jobs)
        return jobs

    except requests.exceptions.Timeout:
        logger.error("Adzuna API timeout")
        raise Exception("Adzuna search timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Adzuna API request failed: {e}")
        raise Exception(f"Adzuna search failed: {str(e)}")
    except Exception as e:
        logger.error(f"Adzuna search error: {e}")
        raise Exception(f"Adzuna search encountered an error: {str(e)}")

@with_rate_limiting("remotive")
@retry_with_exponential_backoff(max_retries=3)
def search_remotive(query: str, category: str = None) -> List[JobResult]:
    """Search remote jobs using Remotive API with enhanced error handling"""
    try:
        validate_search_params(query)

        cache_key = cache_key_generator("remotive", query, category or "")
        cached_results = job_cache.get(cache_key)
        if cached_results:
            return cached_results

        base_url = "https://remotive.com/api/remote-jobs"
        params = {"search": query.strip()}
        if category:
            params["category"] = category.strip()

        logger.info(f"Searching Remotive for '{query}'")

        response = requests.get(
            base_url,
            params=params,
            timeout=app_config.api_timeout,
            headers={'User-Agent': 'ResumeAnalyzer/1.0'}
        )

        response.raise_for_status()
        data = response.json()

        jobs = []
        for item in data.get("jobs", []):
            try:
                job = JobResult(
                    title=item.get("title", "N/A"),
                    company=item.get("company_name", "N/A"),
                    location=item.get("candidate_required_location", "Remote"),
                    description=(item.get("description") or "")[:1000],
                    apply_url=item.get("url", ""),
                    source="Remotive",
                    date_posted=item.get("publication_date"),
                    job_type="Remote"
                )
                jobs.append(job)
            except Exception as e:
                logger.warning(f"Error parsing Remotive job item: {e}")
                continue

        logger.info(f"Retrieved {len(jobs)} jobs from Remotive")
        job_cache.set(cache_key, jobs)
        return jobs

    except requests.exceptions.Timeout:
        logger.error("Remotive API timeout")
        raise Exception("Remotive search timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Remotive API request failed: {e}")
        raise Exception(f"Remotive search failed: {str(e)}")
    except Exception as e:
        logger.error(f"Remotive search error: {e}")
        raise Exception(f"Remotive search encountered an error: {str(e)}")

@with_rate_limiting("jsearch")
@retry_with_exponential_backoff(max_retries=3)
def search_jsearch(query: str, location: str = None, page: int = 1,
                  results: int = 25) -> List[JobResult]:
    """Search jobs using JSearch API via RapidAPI with enhanced error handling"""
    try:
        validate_search_params(query, location)

        if not api_config.rapidapi_key:
            logger.warning("JSearch/RapidAPI key not configured")
            return []

        cache_key = cache_key_generator("jsearch", query, location or "", page, results)
        cached_results = job_cache.get(cache_key)
        if cached_results:
            return cached_results

        # FIXED: Consistent variable naming
        base_url = "https://jsearch.p.rapidapi.com/search"

        params = {
            "query": query.strip(),
            "page": str(page),
            "num_pages": "1",
            "results_per_page": str(min(results, app_config.max_jobs_per_search))
        }

        if location:
            params["location"] = location.strip()

        headers = {
            "X-RapidAPI-Key": api_config.rapidapi_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
            "User-Agent": "ResumeAnalyzer/1.0"
        }

        logger.info(f"Searching JSearch for '{query}' in '{location or 'any location'}'")

        response = requests.get(
            base_url,
            params=params,
            headers=headers,
            timeout=app_config.api_timeout
        )

        # Enhanced error handling for JSearch specific issues
        if response.status_code == 403:
            logger.error("JSearch API returned 403 Forbidden - check API key and subscription")
            raise Exception("JSearch API access denied. Please verify API credentials and subscription.")
        elif response.status_code == 429:
            logger.error("JSearch API rate limit exceeded")
            raise Exception("JSearch API rate limit exceeded. Please try again later.")

        response.raise_for_status()
        data = response.json()

        jobs = []
        for item in data.get("data", []):
            try:
                job = JobResult(
                    title=item.get("job_title", "N/A"),
                    company=item.get("employer_name", "N/A"),
                    location=item.get("job_city") or item.get("job_country", "N/A"),
                    description=(item.get("job_description") or "")[:1000],
                    salary_min=item.get("job_min_salary"),
                    salary_max=item.get("job_max_salary"),
                    apply_url=item.get("job_apply_link", ""),
                    source="JSearch",
                    date_posted=item.get("job_posted_at_datetime_utc"),
                    job_type=item.get("job_employment_type"),
                    experience_level=item.get("job_experience_in_place_of_education")
                )
                jobs.append(job)
            except Exception as e:
                logger.warning(f"Error parsing JSearch job item: {e}")
                continue

        logger.info(f"Retrieved {len(jobs)} jobs from JSearch")
        job_cache.set(cache_key, jobs)
        return jobs

    except requests.exceptions.Timeout:
        logger.error("JSearch API timeout")
        raise Exception("JSearch search timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.error(f"JSearch API request failed: {e}")
        raise Exception(f"JSearch search failed: {str(e)}")
    except Exception as e:
        logger.error(f"JSearch search error: {e}")
        raise Exception(f"JSearch search encountered an error: {str(e)}")

def search_all_apis(query: str, location: str = None, max_results: int = 50) -> List[JobResult]:
    """Search all available job APIs and combine results"""
    # Enhanced input validation
    if not query or not query.strip():
        raise ValueError("Search query is required and cannot be empty")

    all_jobs = []
    errors = []

    # Define search functions
    search_functions = [
        ("Adzuna", lambda: search_adzuna(query, location or "India", results=max_results//3)),
        ("Remotive", lambda: search_remotive(query)),
        ("JSearch", lambda: search_jsearch(query, location, results=max_results//3))
    ]

    for api_name, search_func in search_functions:
        try:
            jobs = search_func()
            all_jobs.extend(jobs)
            logger.info(f"Successfully retrieved {len(jobs)} jobs from {api_name}")
        except Exception as e:
            error_msg = f"Failed to search {api_name}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    # Remove duplicates based on title and company
    unique_jobs = []
    seen = set()
    for job in all_jobs:
        job_key = (job.title.lower().strip(), job.company.lower().strip())
        if job_key not in seen:
            seen.add(job_key)
            unique_jobs.append(job)

    logger.info(f"Retrieved {len(unique_jobs)} unique jobs from {len(search_functions)} APIs")

    if errors and not unique_jobs:
        raise Exception(f"All job search APIs failed: {'; '.join(errors)}")
    elif errors:
        logger.warning(f"Some APIs failed but got results: {'; '.join(errors)}")

    # Sort by relevance (you can enhance this with better scoring)
    unique_jobs.sort(key=lambda job: (
        query.lower() in job.title.lower(),
        query.lower() in job.description.lower(),
        job.source == "JSearch"  # Prefer JSearch results
    ), reverse=True)

    return unique_jobs[:max_results]

def get_job_search_stats() -> Dict[str, Any]:
    """Get statistics about job search usage"""
    stats = {
        "cache_size": len(job_cache.cache),
        "rate_limits": {
            api: len(limiter.calls) for api, limiter in rate_limiters.items()
        },
        "timestamp": datetime.now().isoformat()
    }
    return stats
