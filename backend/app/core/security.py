from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
import tldextract
from Levenshtein import distance
import re
import idna
from urllib.parse import urlparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand_database import BRAND_DATABASE, CHARACTER_SUBSTITUTIONS, SUSPICIOUS_KEYWORDS

class PhishingDetector:
    """Enhanced phishing detection with typosquatting and homograph attack detection"""
    
    def __init__(self):
        self.brands = BRAND_DATABASE
        self.substitution_map = CHARACTER_SUBSTITUTIONS
        self.suspicious_keywords = SUSPICIOUS_KEYWORDS
        
    def extract_domain(self, url):
        """Extract domain from URL"""
        try:
            extracted = tldextract.extract(url)
            return {
                'subdomain': extracted.subdomain.lower(),
                'domain': extracted.domain.lower(),
                'sld': extracted.domain.lower(),
                'tld': extracted.suffix.lower(),
                'full_domain': f"{extracted.domain}.{extracted.suffix}".lower()
            }
        except:
            return None
    
    def normalize_text(self, text):
        """Normalize text by replacing homograph characters"""
        if not text:
            return ""
            
        normalized = text.lower()
        
        # Replace number substitutions with letters
        for num, letters in self.substitution_map.items():
            if num.isdigit():
                for letter in letters:
                    if letter.isalpha():
                        normalized = normalized.replace(num, letter)
        
        # Remove special characters and digits for comparison
        normalized = re.sub(r'[^a-z]', '', normalized)
        
        return normalized
    
    def detect_character_substitution(self, domain):
        """Detect if domain uses character substitutions like o->0, l->1"""
        substitutions = []
        
        for char in domain:
            if char in self.substitution_map:
                substitutions.append({
                    'character': char,
                    'common_substitution': self.substitution_map[char][0] if self.substitution_map[char] else char
                })
        
        return {
            'has_substitution': len(substitutions) > 0,
            'substitutions': substitutions,
            'substitution_count': len(substitutions)
        }
    
    def calculate_similarity(self, domain, brand):
        """Calculate similarity between domain and brand"""
        domain_lower = domain.lower()
        brand_lower = brand.lower()
        
        # If domain is too short or too different in length
        if len(domain_lower) < 3 or abs(len(domain_lower) - len(brand_lower)) > 5:
            return 0.0
        
        # Check exact match
        if domain_lower == brand_lower:
            return 1.0
        
        # Calculate Levenshtein distance
        lev_distance = distance(domain_lower, brand_lower)
        max_len = max(len(domain_lower), len(brand_lower))
        similarity = 1 - (lev_distance / max_len)
        
        # Boost similarity if domain contains brand
        if brand_lower in domain_lower or domain_lower in brand_lower:
            similarity = min(similarity + 0.2, 1.0)
        
        # Check normalized version (after substitution removal)
        normalized_domain = self.normalize_text(domain_lower)
        normalized_brand = self.normalize_text(brand_lower)
        
        if normalized_domain and normalized_brand:
            if normalized_domain == normalized_brand:
                similarity = 1.0
            else:
                # Calculate normalized similarity
                norm_lev_distance = distance(normalized_domain, normalized_brand)
                norm_max_len = max(len(normalized_domain), len(normalized_brand))
                norm_similarity = 1 - (norm_lev_distance / norm_max_len) if norm_max_len > 0 else 0
                
                # Use the higher similarity score
                similarity = max(similarity, norm_similarity)
        
        return similarity
    
    def check_typosquatting(self, url):
        """Main typosquatting detection function"""
        domain_info = self.extract_domain(url)
        if not domain_info:
            return {
                'is_typosquatting': False,
                'confidence': 0,
                'detected_brand': None,
                'details': 'Failed to extract domain'
            }
        
        domain_name = domain_info['domain']
        
        results = {
            'is_typosquatting': False,
            'confidence': 0,
            'detected_brand': None,
            'similarity_score': 0,
            'techniques': [],
            'details': {}
        }
        
        best_match = None
        best_score = 0
        
        # 1. Check for exact match first (Legitimate Site)
        # This prevents flagging google.com as a partial match
        for brand_key, brand_info in self.brands.items():
            if domain_name == brand_key:
                return {
                    'is_typosquatting': False,
                    'confidence': 0,
                    'detected_brand': brand_info['name'],
                    'similarity_score': 1.0,
                    'techniques': [],
                    'details': {'exact_match': True}
                }

        # 2. Analyze variations (Full domain + Hyphenated parts)
        # We split by hyphen to catch cases like 'amazon-account' or 'google-login'
        check_candidates = set([domain_name])
        if '-' in domain_name:
            check_candidates.update(domain_name.split('-'))
        
        # Check each candidate part against the brand database
        for candidate in check_candidates:
            # Skip short candidates to avoid false positives (e.g. 'com', 'net')
            if len(candidate) < 3:
                continue

            for brand_key, brand_info in self.brands.items():
                # Skip very short brands
                if len(brand_key) < 4:
                    continue
                
                similarity = self.calculate_similarity(candidate, brand_key)
                
                # Potential typosquat detected on this part
                if similarity >= 0.65:  # 65% similarity threshold
                    # Check character substitutions on the candidate
                    substitution_info = self.detect_character_substitution(candidate)
                    
                    techniques = []
                    confidence = similarity * 100
                    
                    if substitution_info['has_substitution']:
                        techniques.append('character_substitution')
                        confidence *= 1.3  # Boost confidence for substitutions
                    
                    if similarity >= 0.8:
                        techniques.append('high_similarity')
                    
                    # Check for Brand Inclusion (Exact match on a PART of the domain)
                    # e.g. 'apple' inside 'apple-verify'
                    if candidate == brand_key:
                        techniques.append('brand_inclusion')
                        confidence = 95.0

                    # Check Levenshtein distance
                    lev_distance = distance(candidate.lower(), brand_key.lower())
                    if lev_distance <= 2:
                        techniques.append('minor_typo')
                        confidence *= 1.2
                    
                    # Track best match
                    if similarity > best_score:
                        best_score = similarity
                        best_match = {
                            'brand': brand_info['name'],
                            'brand_key': brand_key,
                            'similarity': similarity,
                            'confidence': min(confidence, 99),  # Cap at 99%
                            'techniques': techniques,
                            'substitutions': substitution_info['substitutions']
                        }
        
        # If we found a good match
        if best_match and best_match['confidence'] >= 65:
            results['is_typosquatting'] = True
            results['detected_brand'] = best_match['brand']
            results['confidence'] = best_match['confidence']
            results['similarity_score'] = best_match['similarity']
            results['techniques'] = best_match['techniques']
            results['details'] = {
                'matched_brand': best_match['brand_key'],
                'levenshtein_distance': distance(domain_name.lower(), best_match['brand_key'].lower()),
                'character_substitutions': best_match['substitutions']
            }
        
        return results
    
    def check_homograph_attack(self, url):
        """Detect homograph attacks using Unicode characters"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Check for punycode (xn-- prefix)
            is_punycode = domain.startswith('xn--')
            
            # Check for mixed script
            has_unicode = False
            unicode_chars = []
            
            for char in domain:
                # Check if character is outside ASCII range
                if ord(char) > 127:
                    has_unicode = True
                    unicode_chars.append({
                        'char': char,
                        'unicode': f'U+{ord(char):04X}',
                        'likely_ascii_match': self.substitution_map.get(char, '?')
                    })
            
            # Decode punycode to see what it represents
            decoded_domain = None
            if is_punycode:
                try:
                    decoded_domain = idna.decode(domain)
                except:
                    decoded_domain = "Unable to decode"
            
            return {
                'is_homograph': has_unicode or is_punycode,
                'has_unicode': has_unicode,
                'is_punycode': is_punycode,
                'unicode_chars': unicode_chars,
                'decoded_domain': decoded_domain,
                'risk_level': 'high' if has_unicode or is_punycode else 'low'
            }
            
        except Exception as e:
            return {
                'is_homograph': False,
                'error': str(e),
                'risk_level': 'unknown'
            }
    
    def check_suspicious_keywords(self, url):
        """Check for phishing-related keywords in URL"""
        url_lower = url.lower()
        
        found_keywords = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': []
        }
        
        # Check each category
        for risk_level, keywords in self.suspicious_keywords.items():
            for keyword in keywords:
                # Use word boundary matching to avoid false positives
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, url_lower):
                    found_keywords[risk_level].append(keyword)
        
        # Calculate risk score
        risk_score = (
            len(found_keywords['high_risk']) * 10 +
            len(found_keywords['medium_risk']) * 5 +
            len(found_keywords['low_risk']) * 2
        )
        
        total_found = (
            len(found_keywords['high_risk']) +
            len(found_keywords['medium_risk']) +
            len(found_keywords['low_risk'])
        )
        
        return {
            'has_suspicious_keywords': total_found > 0,
            'found_keywords': found_keywords,
            'total_count': total_found,
            'risk_score': risk_score,
            'risk_level': 'high' if risk_score >= 10 else 'medium' if risk_score >= 5 else 'low'
        }

# Create global instance
phishing_detector = PhishingDetector()

# Wrapper functions for backward compatibility
def detect_phishing(url):
    """Comprehensive phishing detection"""
    typosquatting = phishing_detector.check_typosquatting(url)
    homograph = phishing_detector.check_homograph_attack(url)
    keywords = phishing_detector.check_suspicious_keywords(url)
    
    # Calculate overall phishing score (0-100)
    phishing_score = 0
    
    if typosquatting['is_typosquatting']:
        phishing_score += typosquatting['confidence'] * 0.6
    
    if homograph['is_homograph']:
        phishing_score += 30
    
    phishing_score += keywords['risk_score']
    
    # Cap at 100
    phishing_score = min(phishing_score, 100)
    
    return {
        'typosquatting': typosquatting,
        'homograph_attack': homograph,
        'suspicious_keywords': keywords,
        'phishing_score': phishing_score,
        'is_phishing': phishing_score >= 50,  # 50+ is considered phishing
        'risk_level': 'critical' if phishing_score >= 80 else 
                     'high' if phishing_score >= 60 else 
                     'medium' if phishing_score >= 40 else 
                     'low'
    }

# SECRET SETTINGS
SECRET_KEY = "CHANGE_THIS_TO_A_SUPER_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- CHANGE: Switched from 'bcrypt' to 'argon2' to fix compatibility errors ---
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)