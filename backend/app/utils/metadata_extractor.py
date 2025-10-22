"""
Metadata extraction utilities for patient information
"""

import re
from typing import Dict, Any, List, Optional, Tuple
import logging

from app.core.logging import logger


class MetadataExtractor:
    """Extract patient metadata from text conversations"""
    
    # Age patterns
    AGE_PATTERNS = [
        r'\b(\d{1,3})\s*(?:year|yr|y\.o\.|years old|yo)\b',
        r'\b(?:age|aged)\s*(\d{1,3})\b',
        r'\b(\d{1,3})\s*(?:years?)\b'
    ]
    
    # Gender patterns
    GENDER_PATTERNS = {
        'male': [r'\b(male|man|boy|guy|gentleman)\b', r'\b(he|him|his)\b'],
        'female': [r'\b(female|woman|girl|lady|gentlewoman)\b', r'\b(she|her|hers)\b']
    }
    
    # Symptom keywords
    SYMPTOM_KEYWORDS = [
        'pain', 'ache', 'hurt', 'sore', 'tender',
        'itch', 'itchy', 'burning', 'stinging',
        'swelling', 'swollen', 'inflamed', 'redness',
        'bleeding', 'blood', 'discharge', 'pus',
        'growth', 'lump', 'bump', 'lesion', 'spot',
        'change', 'different', 'abnormal', 'unusual',
        'rash', 'blister', 'ulcer', 'sore', 'wound',
        'numbness', 'tingling', 'burning sensation',
        'dry', 'scaly', 'flaky', 'peeling'
    ]
    
    # Location keywords
    LOCATION_KEYWORDS = [
        'face', 'cheek', 'forehead', 'chin', 'nose',
        'arm', 'hand', 'finger', 'leg', 'foot', 'toe',
        'back', 'chest', 'stomach', 'abdomen',
        'neck', 'throat', 'mouth', 'lip', 'tongue',
        'eye', 'ear', 'head', 'scalp',
        'shoulder', 'elbow', 'knee', 'ankle',
        'wrist', 'palm', 'sole', 'heel'
    ]
    
    # Duration patterns
    DURATION_PATTERNS = [
        r'\b(\d+)\s*(?:day|days)\b',
        r'\b(\d+)\s*(?:week|weeks)\b',
        r'\b(\d+)\s*(?:month|months)\b',
        r'\b(\d+)\s*(?:year|years)\b',
        r'\b(?:for|since)\s*(\d+)\s*(?:day|week|month|year)s?\b',
        r'\b(?:last|past)\s*(\d+)\s*(?:day|week|month|year)s?\b'
    ]
    
    def __init__(self):
        self.compiled_age_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.AGE_PATTERNS]
        self.compiled_gender_patterns = {
            gender: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for gender, patterns in self.GENDER_PATTERNS.items()
        }
        self.compiled_duration_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.DURATION_PATTERNS]
    
    def extract_metadata(self, text: str, existing_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract metadata from text"""
        try:
            metadata = existing_metadata.copy() if existing_metadata else {}
            
            # Extract age
            age = self._extract_age(text)
            if age and not metadata.get('age'):
                metadata['age'] = age
            
            # Extract gender
            gender = self._extract_gender(text)
            if gender and not metadata.get('gender'):
                metadata['gender'] = gender
            
            # Extract symptoms
            symptoms = self._extract_symptoms(text)
            if symptoms:
                existing_symptoms = metadata.get('symptoms', [])
                metadata['symptoms'] = list(set(existing_symptoms + symptoms))
            
            # Extract location
            location = self._extract_location(text)
            if location and not metadata.get('location'):
                metadata['location'] = location
            
            # Extract duration
            duration = self._extract_duration(text)
            if duration and not metadata.get('duration'):
                metadata['duration'] = duration
            
            # Extract medical history
            medical_history = self._extract_medical_history(text)
            if medical_history:
                existing_history = metadata.get('medical_history', {})
                existing_history.update(medical_history)
                metadata['medical_history'] = existing_history
            
            logger.info(f"Metadata extracted: {list(metadata.keys())}")
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction error: {e}")
            return existing_metadata or {}
    
    def _extract_age(self, text: str) -> Optional[str]:
        """Extract age from text"""
        try:
            for pattern in self.compiled_age_patterns:
                match = pattern.search(text)
                if match:
                    age = int(match.group(1))
                    if 0 <= age <= 120:  # Reasonable age range
                        return str(age)
            return None
        except Exception:
            return None
    
    def _extract_gender(self, text: str) -> Optional[str]:
        """Extract gender from text"""
        try:
            text_lower = text.lower()
            
            for gender, patterns in self.compiled_gender_patterns.items():
                for pattern in patterns:
                    if pattern.search(text_lower):
                        return gender
            return None
        except Exception:
            return None
    
    def _extract_symptoms(self, text: str) -> List[str]:
        """Extract symptoms from text"""
        try:
            text_lower = text.lower()
            symptoms = []
            
            for keyword in self.SYMPTOM_KEYWORDS:
                if keyword in text_lower:
                    symptoms.append(keyword)
            
            return symptoms
        except Exception:
            return []
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract body location from text"""
        try:
            text_lower = text.lower()
            
            for location in self.LOCATION_KEYWORDS:
                if location in text_lower:
                    return location
            return None
        except Exception:
            return None
    
    def _extract_duration(self, text: str) -> Optional[str]:
        """Extract duration from text"""
        try:
            for pattern in self.compiled_duration_patterns:
                match = pattern.search(text)
                if match:
                    return match.group(0)
            return None
        except Exception:
            return None
    
    def _extract_medical_history(self, text: str) -> Dict[str, Any]:
        """Extract medical history from text"""
        try:
            medical_history = {}
            text_lower = text.lower()
            
            # Check for common medical conditions
            conditions = [
                'diabetes', 'hypertension', 'high blood pressure',
                'asthma', 'allergies', 'cancer', 'heart disease',
                'depression', 'anxiety', 'arthritis'
            ]
            
            for condition in conditions:
                if condition in text_lower:
                    medical_history[condition] = True
            
            # Check for medications
            medication_patterns = [
                r'\b(?:taking|on|using)\s+([a-zA-Z]+)\b',
                r'\b(?:medication|medicine|drug)\s+([a-zA-Z]+)\b'
            ]
            
            for pattern in medication_patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    medical_history['medications'] = matches
            
            return medical_history
        except Exception:
            return {}
    
    def validate_extracted_metadata(self, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate extracted metadata"""
        try:
            errors = []
            
            # Validate age
            if 'age' in metadata:
                try:
                    age = int(metadata['age'])
                    if not (0 <= age <= 120):
                        errors.append(f"Invalid age: {age}")
                except ValueError:
                    errors.append(f"Invalid age format: {metadata['age']}")
            
            # Validate gender
            if 'gender' in metadata:
                if metadata['gender'] not in ['male', 'female']:
                    errors.append(f"Invalid gender: {metadata['gender']}")
            
            # Validate symptoms
            if 'symptoms' in metadata:
                if not isinstance(metadata['symptoms'], list):
                    errors.append("Symptoms must be a list")
                else:
                    for symptom in metadata['symptoms']:
                        if not isinstance(symptom, str):
                            errors.append(f"Invalid symptom: {symptom}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Metadata validation error: {e}")
            return False, [str(e)]
    
    def get_metadata_summary(self, metadata: Dict[str, Any]) -> str:
        """Get human-readable metadata summary"""
        try:
            summary_parts = []
            
            if metadata.get('age'):
                summary_parts.append(f"Age: {metadata['age']}")
            
            if metadata.get('gender'):
                summary_parts.append(f"Gender: {metadata['gender']}")
            
            if metadata.get('location'):
                summary_parts.append(f"Location: {metadata['location']}")
            
            if metadata.get('duration'):
                summary_parts.append(f"Duration: {metadata['duration']}")
            
            if metadata.get('symptoms'):
                symptoms = ', '.join(metadata['symptoms'][:5])  # Limit to 5 symptoms
                if len(metadata['symptoms']) > 5:
                    symptoms += f" (+{len(metadata['symptoms']) - 5} more)"
                summary_parts.append(f"Symptoms: {symptoms}")
            
            return '; '.join(summary_parts) if summary_parts else "No metadata available"
            
        except Exception as e:
            logger.error(f"Metadata summary error: {e}")
            return "Error generating summary"
