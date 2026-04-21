from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.feedback_model import Feedback, User, Validation
from models.translation_model import Dictionary, ParallelSentence
from config.database_config import SessionLocal, redis_client
from config.settings import config
import json

logger = logging.getLogger(__name__)

class ValidationService:
    def __init__(self):
        self.min_validators = config.MIN_VALIDATORS
        self.consensus_threshold = config.CONSENSUS_THRESHOLD
    
    def submit_validation_vote(self, feedback_id: str, validator_id: str, 
                             vote: str, modification: Optional[Dict] = None,
                             comment: Optional[str] = None) -> Tuple[bool, str, Dict]:
        """Submit a validation vote"""
        db = SessionLocal()
        try:
            # Get feedback
            feedback = db.query(Feedback).filter(
                Feedback.feedback_id == feedback_id
            ).first()
            
            if not feedback:
                return False, "Feedback not found", {}
            
            if feedback.status != 'pending_validation':
                return False, "Feedback not pending validation", {}
            
            # Get validator
            validator = db.query(User).filter(
                User.user_id == validator_id
            ).first()
            
            if not validator:
                return False, "Validator not found", {}
            
            # Check if validator is qualified
            if not self._is_qualified_validator(validator):
                return False, "User not qualified to validate", {}
            
            # Check if already voted
            existing_vote = db.query(Validation).filter(
                Validation.feedback_id == feedback.id,
                Validation.validator_id == validator.id
            ).first()
            
            if existing_vote:
                return False, "Already voted on this feedback", {}
            
            # Calculate vote weight
            vote_weight = self._calculate_vote_weight(validator)
            
            # Create validation entry
            validation = Validation(
                feedback_id=feedback.id,
                validator_id=validator.id,
                vote=vote,
                vote_weight=vote_weight,
                modification=modification,
                comment=comment
            )
            
            db.add(validation)
            db.commit()
            
            # Check if consensus reached
            consensus_result = self._check_consensus(db, feedback)
            
            if consensus_result['reached']:
                self._process_consensus(db, feedback, consensus_result)
                
                return True, "Vote recorded and consensus reached", {
                    'consensus': consensus_result['decision'],
                    'confidence': consensus_result['confidence']
                }
            
            return True, "Vote recorded successfully", {
                'total_votes': consensus_result['total_votes'],
                'votes_needed': self.min_validators - consensus_result['total_votes']
            }
            
        except Exception as e:
            logger.error(f"Error submitting validation vote: {str(e)}")
            db.rollback()
            return False, str(e), {}
        finally:
            db.close()
    
    def _is_qualified_validator(self, user: User) -> bool:
        """Check if user is qualified to validate"""
        # Native speakers and linguists are automatically qualified
        if user.is_native_speaker or user.is_linguist:
            return True
        
        # Check contribution history
        if user.accepted_contributions >= 50 and user.trust_score >= 0.7:
            return True
        
        # Verified users with good standing
        if user.is_verified and user.trust_score >= 0.8:
            return True
        
        return False
    
    def _calculate_vote_weight(self, validator: User) -> float:
        """Calculate vote weight based on validator credentials"""
        weight = 1.0
        
        # Credential multipliers
        if validator.is_native_speaker:
            weight *= 2.0
        if validator.is_linguist:
            weight *= 1.5
        if validator.is_verified:
            weight *= 1.2
        
        # Trust score multiplier
        weight *= (0.5 + validator.trust_score)
        
        # Experience multiplier
        if validator.accepted_contributions > 100:
            weight *= 1.2
        elif validator.accepted_contributions > 50:
            weight *= 1.1
        
        return min(weight, 5.0)  # Cap at 5x
    
    def _check_consensus(self, db: Session, feedback: Feedback) -> Dict:
        """Check if consensus has been reached"""
        validations = db.query(Validation).filter(
            Validation.feedback_id == feedback.id
        ).all()
        
        if not validations:
            return {'reached': False, 'total_votes': 0}
        
        # Calculate weighted votes
        vote_tallies = {}
        total_weight = 0
        
        for validation in validations:
            vote = validation.vote
            weight = validation.vote_weight
            
            if vote not in vote_tallies:
                vote_tallies[vote] = 0
            
            vote_tallies[vote] += weight
            total_weight += weight
        
        # Check if minimum validators reached
        if len(validations) < self.min_validators:
            return {
                'reached': False,
                'total_votes': len(validations),
                'vote_tallies': vote_tallies
            }
        
        # Check if any vote has consensus
        for vote, weight in vote_tallies.items():
            ratio = weight / total_weight
            
            if ratio >= self.consensus_threshold:
                return {
                    'reached': True,
                    'decision': vote,
                    'confidence': ratio,
                    'total_votes': len(validations),
                    'vote_tallies': vote_tallies
                }
        
        # Check if maximum validators reached without consensus
        if len(validations) >= self.min_validators * 2:
            # Take the highest voted option
            best_vote = max(vote_tallies.items(), key=lambda x: x[1])
            return {
                'reached': True,
                'decision': best_vote[0],
                'confidence': best_vote[1] / total_weight,
                'total_votes': len(validations),
                'vote_tallies': vote_tallies,
                'forced': True
            }
        
        return {
            'reached': False,
            'total_votes': len(validations),
            'vote_tallies': vote_tallies
        }
    
    def _process_consensus(self, db: Session, feedback: Feedback, consensus_result: Dict):
        """Process feedback based on consensus decision"""
        decision = consensus_result['decision']
        
        if decision == 'approve':
            feedback.status = 'approved'
            self._add_to_dictionary(db, feedback)
            self._update_user_stats(db, feedback.user_id, True)
            
        elif decision == 'reject':
            feedback.status = 'rejected'
            self._update_user_stats(db, feedback.user_id, False)
            
        elif decision == 'modify':
            feedback.status = 'needs_modification'
            # Collect modifications from validators
            self._process_modifications(db, feedback)
        
        feedback.processed_at = datetime.utcnow()
        db.commit()
        
        # Clear from validation queue
        self._remove_from_validation_queue(feedback.feedback_id)
    
    def _add_to_dictionary(self, db: Session, feedback: Feedback):
        """Add approved feedback to dictionary"""
        # Check if entry exists
        existing = db.query(Dictionary).filter(
            Dictionary.english == feedback.english_text.lower()
        ).first()
        
        if existing:
            # Update existing entry
            existing.limbu = feedback.suggested_limbu
            existing.limbu_script = feedback.suggested_script
            existing.pronunciation = feedback.suggested_pronunciation
            existing.updated_at = datetime.utcnow()
            existing.verified = True
        else:
            # Create new entry
            new_entry = Dictionary(
                english=feedback.english_text.lower(),
                limbu=feedback.suggested_limbu,
                limbu_script=feedback.suggested_script,
                pronunciation=feedback.suggested_pronunciation,
                verified=True
            )
            db.add(new_entry)
        
        # Also add to parallel sentences if it's a sentence
        if ' ' in feedback.english_text:
            parallel = ParallelSentence(
                english=feedback.english_text,
                limbu=feedback.suggested_limbu,
                limbu_script=feedback.suggested_script,
                pronunciation=feedback.suggested_pronunciation,
                source='feedback',
                verified=True
            )
            db.add(parallel)
    
    def _update_user_stats(self, db: Session, user_id: int, accepted: bool):
        """Update user statistics after validation"""
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            if accepted:
                user.accepted_contributions += 1
            
            # Recalculate trust score
            if user.total_contributions > 0:
                acceptance_rate = user.accepted_contributions / user.total_contributions
                user.trust_score = min(0.5 + (acceptance_rate * 0.5), 1.0)
    
    def _process_modifications(self, db: Session, feedback: Feedback):
        """Process modifications suggested by validators"""
        validations = db.query(Validation).filter(
            Validation.feedback_id == feedback.id,
            Validation.vote == 'modify',
            Validation.modification.isnot(None)
        ).all()
        
        if validations:
            # Aggregate modifications
            modifications = []
            for validation in validations:
                modifications.append({
                    'validator_id': validation.validator_id,
                    'modification': validation.modification,
                    'weight': validation.vote_weight
                })
            
            # Store modifications for expert review
            redis_client.rpush(
                'modification_queue',
                json.dumps({
                    'feedback_id': feedback.feedback_id,
                    'modifications': modifications,
                    'timestamp': datetime.utcnow().isoformat()
                })
            )
    
    def _remove_from_validation_queue(self, feedback_id: str):
        """Remove feedback from validation queue"""
        # Remove from Redis queue
        queue_length = redis_client.llen('validation_queue')
        
        for i in range(queue_length):
            item = redis_client.lindex('validation_queue', i)
            if item:
                data = json.loads(item)
                if data.get('feedback_id') == feedback_id:
                    redis_client.lrem('validation_queue', 1, item)
                    break
    
    def get_pending_validations(self, validator_id: str, limit: int = 10) -> List[Dict]:
        """Get pending validations for a validator"""
        db = SessionLocal()
        try:
            # Get validator
            validator = db.query(User).filter(
                User.user_id == validator_id
            ).first()
            
            if not validator or not self._is_qualified_validator(validator):
                return []
            
            # Get feedback that validator hasn't voted on
            voted_feedback_ids = db.query(Validation.feedback_id).filter(
                Validation.validator_id == validator.id
            ).subquery()
            
            pending_feedback = db.query(Feedback).filter(
                Feedback.status == 'pending_validation',
                ~Feedback.id.in_(voted_feedback_ids)
            ).order_by(Feedback.created_at).limit(limit).all()
            
            results = []
            for feedback in pending_feedback:
                # Get current vote status
                validations = db.query(
                    Validation.vote,
                    func.sum(Validation.vote_weight).label('total_weight')
                ).filter(
                    Validation.feedback_id == feedback.id
                ).group_by(Validation.vote).all()
                
                vote_summary = {v.vote: v.total_weight for v in validations}
                total_votes = db.query(func.count(Validation.id)).filter(
                    Validation.feedback_id == feedback.id
                ).scalar()
                
                results.append({
                    'feedback_id': feedback.feedback_id,
                    'english': feedback.english_text,
                    'suggested_limbu': feedback.suggested_limbu,
                    'suggested_script': feedback.suggested_script,
                    'suggested_pronunciation': feedback.suggested_pronunciation,
                    'confidence_score': feedback.confidence_score,
                    'created_at': feedback.created_at.isoformat(),
                    'vote_summary': vote_summary,
                    'total_votes': total_votes,
                    'votes_needed': self.min_validators - total_votes
                })
            
            return results
            
        finally:
            db.close()