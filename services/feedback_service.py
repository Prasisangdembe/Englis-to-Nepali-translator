import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import json

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.feedback_model import Feedback, User, Validation
from models.translation_model import Dictionary, ParallelSentence
from config.database_config import redis_client, SessionLocal
from config.settings import config
from utils.text_processing import TextProcessor
from utils.limbu_utils import LimbuValidator

logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.limbu_validator = LimbuValidator()
        self.load_spam_patterns()
        self.load_profanity_list()
    
    def load_spam_patterns(self):
        """Load spam detection patterns"""
        self.spam_patterns = [
            r'(viagra|cialis|casino|lottery|prize|winner)',
            r'(click here|buy now|limited offer|act now)',
            r'(.)\1{5,}',  # Repeated characters
            r'[A-Z]{10,}',  # All caps
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URLs
        ]
    
    def load_profanity_list(self):
        """Load profanity filter list"""
        # In production, load from database or file
        self.profanity_list = set([
            # Add actual profanity terms here
        ])
    
    def submit_feedback(self, feedback_data: Dict, user_id: str) -> Tuple[bool, str, Dict]:
        """
        Submit feedback with validation
        
        Returns:
            Tuple of (success, message, result_data)
        """
        db = SessionLocal()
        try:
            # Get or create user
            user = self._get_or_create_user(db, user_id)
            
            # Check rate limiting
            if not self._check_rate_limit(user):
                return False, "Rate limit exceeded", {}
            
            # Validate feedback
            is_valid, validation_result = self._validate_feedback(feedback_data, user)
            
            if not is_valid:
                return False, validation_result['reason'], validation_result
            
            # Generate feedback ID
            feedback_id = self._generate_feedback_id(feedback_data)
            
            # Check for duplicates
            if self._is_duplicate(db, feedback_id):
                return False, "Duplicate feedback", {'feedback_id': feedback_id}
            
            # Create feedback entry
            feedback = Feedback(
                feedback_id=feedback_id,
                user_id=user.id,
                english_text=feedback_data['english'],
                original_limbu=feedback_data.get('original_limbu'),
                suggested_limbu=feedback_data['suggested_limbu'],
                suggested_script=feedback_data.get('suggested_script'),
                suggested_pronunciation=feedback_data.get('suggested_pronunciation'),
                feedback_type=feedback_data.get('type', 'correction'),
                confidence_score=validation_result['confidence'],
                status=self._determine_initial_status(validation_result['confidence'], user)
            )
            
            db.add(feedback)
            
            # Update user stats
            user.total_contributions += 1
            user.last_active = datetime.utcnow()
            
            db.commit()
            
            # Process based on confidence
            result = self._process_feedback_by_confidence(
                db, feedback, validation_result['confidence']
            )
            
            return True, "Feedback submitted successfully", {
                'feedback_id': feedback_id,
                'status': feedback.status,
                'confidence': validation_result['confidence'],
                'next_steps': result.get('next_steps', 'Processing')
            }
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            db.rollback()
            return False, f"Error: {str(e)}", {}
        finally:
            db.close()
    
    def _validate_feedback(self, feedback_data: Dict, user: User) -> Tuple[bool, Dict]:
        """Comprehensive feedback validation"""
        validation_result = {
            'valid': True,
            'confidence': 1.0,
            'checks': {}
        }
        
        # 1. Spam check
        spam_score = self._calculate_spam_score(feedback_data)
        validation_result['checks']['spam_score'] = spam_score
        
        if spam_score > 0.7:
            validation_result['valid'] = False
            validation_result['reason'] = "Spam detected"
            return False, validation_result
        
        validation_result['confidence'] *= (1 - spam_score)
        
        # 2. Format validation
        format_valid = self._validate_format(feedback_data)
        validation_result['checks']['format_valid'] = format_valid
        
        if not format_valid:
            validation_result['valid'] = False
            validation_result['reason'] = "Invalid format"
            return False, validation_result
        
        # 3. Limbu script validation
        if 'suggested_script' in feedback_data:
            script_valid = self.limbu_validator.validate_script(
                feedback_data['suggested_script']
            )
            validation_result['checks']['script_valid'] = script_valid
            
            if not script_valid:
                validation_result['confidence'] *= 0.7
        
        # 4. Content quality check
        quality_score = self._assess_content_quality(feedback_data)
        validation_result['checks']['quality_score'] = quality_score
        validation_result['confidence'] *= quality_score
        
        # 5. User trust score
        trust_score = self._calculate_user_trust_score(user)
        validation_result['checks']['user_trust'] = trust_score
        validation_result['confidence'] *= trust_score
        
        # 6. Consistency check
        consistency_score = self._check_consistency(feedback_data)
        validation_result['checks']['consistency'] = consistency_score
        validation_result['confidence'] *= consistency_score
        
        return validation_result['valid'], validation_result
    
    def _calculate_spam_score(self, feedback_data: Dict) -> float:
        """Calculate spam probability score"""
        score = 0.0
        text = f"{feedback_data.get('english', '')} {feedback_data.get('suggested_limbu', '')}"
        
        # Check spam patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.2
        
        # Check profanity
        words = text.lower().split()
        profanity_count = sum(1 for word in words if word in self.profanity_list)
        score += profanity_count * 0.3
        
        # Check text length
        if len(text) < 3 or len(text) > 2000:
            score += 0.2
        
        # Check character repetition
        if re.search(r'(.)\1{4,}', text):
            score += 0.2
        
        # Check for excessive punctuation
        punct_ratio = sum(1 for c in text if c in '!?.,;:') / max(len(text), 1)
        if punct_ratio > 0.3:
            score += 0.1
        
        return min(score, 1.0)
    
    def _validate_format(self, feedback_data: Dict) -> bool:
        """Validate feedback data format"""
        required_fields = ['english', 'suggested_limbu']
        
        for field in required_fields:
            if field not in feedback_data or not feedback_data[field]:
                return False
        
        # Check field lengths
        if len(feedback_data['english']) > 1000:
            return False
        
        if len(feedback_data['suggested_limbu']) > 1000:
            return False
        
        return True
    
    def _assess_content_quality(self, feedback_data: Dict) -> float:
        """Assess quality of feedback content"""
        quality_score =