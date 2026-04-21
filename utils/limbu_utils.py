import re
from typing import Dict, List, Optional

class LimbuScriptConverter:
    """Convert between Limbu romanization and script"""
    
    def __init__(self):
        self.load_mappings()
    
    def load_mappings(self):
        """Load character mappings"""
        # Basic consonants
        self.consonants = {
            'k': 'ᤁ', 'kh': 'ᤂ', 'g': 'ᤃ', 'gh': 'ᤄ', 'ng': 'ᤅ',
            'c': 'ᤆ', 'ch': 'ᤇ', 'j': 'ᤈ', 'ny': 'ᤉ',
            't': 'ᤋ', 'th': 'ᤌ', 'd': 'ᤍ', 'dh': 'ᤎ', 'n': 'ᤏ',
            'p': 'ᤐ', 'ph': 'ᤑ', 'b': 'ᤒ', 'bh': 'ᤓ', 'm': 'ᤔ',
            'y': 'ᤕ', 'r': 'ᤖ', 'l': 'ᤗ', 'w': 'ᤘ',
            'sh': 'ᤙ', 's': 'ᤚ', 'h': 'ᤛ'
        }
        
        # Vowels
        self.vowels = {
            'a': 'ᤠ', 'i': 'ᤡ', 'u': 'ᤢ', 'e': 'ᤣ',
            'ai': 'ᤤ', 'o': 'ᤥ', 'au': 'ᤦ'
        }
        
        # Special marks
        self.special = {
            '?': '᤹',
            '!': '᤺',
            'ng': 'ᤱ'  # Final ng
        }
    
    def romanized_to_script(self, text: str) -> str:
        """Convert romanized Limbu to script"""
        result = []
        words = text.split()
        
        for word in words:
            # Check if already in script or untranslatable
            if re.search(r'[\u1900-\u194F]', word) or word.startswith('['):
                result.append(word)
                continue
            
            script_word = self.convert_word(word)
            result.append(script_word)
        
        return ' '.join(result)
    
    def convert_word(self, word: str) -> str:
        """Convert single word to script"""
        word = word.lower()
        result = ''
        i = 0
        
        while i < len(word):
            # Check for two-character combinations first
            if i < len(word) - 1:
                two_char = word[i:i+2]
                if two_char in self.consonants:
                    result += self.consonants[two_char]
                    i += 2
                    continue
                elif two_char in self.vowels:
                    result += self.vowels[two_char]
                    i += 2
                    continue
            
            # Single character
            char = word[i]
            if char in self.consonants:
                result += self.consonants[char]
            elif char in self.vowels:
                result += self.vowels[char]
            elif char in self.special:
                result += self.special[char]
            else:
                result += char  # Keep as is
            
            i += 1
        
        return result
    
    def script_to_romanized(self, script: str) -> str:
        """Convert Limbu script to romanized form"""
        # Create reverse mapping
        reverse_map = {}
        for roman, limbu in self.consonants.items():
            reverse_map[limbu] = roman
        for roman, limbu in self.vowels.items():
            reverse_map[limbu] = roman
        for roman, limbu in self.special.items():
            reverse_map[limbu] = roman
        
        result = []
        for char in script:
            if char in reverse_map:
                result.append(reverse_map[char])
            elif char == ' ':
                result.append(' ')
            else:
                result.append(char)
        
        return ''.join(result)
    
    def generate_pronunciation(self, text: str) -> str:
        """Generate pronunciation guide"""
        # Simplified pronunciation - in production, use phonetic rules
        pronunciation = text.lower()
        
        # Apply basic rules
        pronunciation = pronunciation.replace('kh', 'kʰ')
        pronunciation = pronunciation.replace('gh', 'gʰ')
        pronunciation = pronunciation.replace('th', 'tʰ')
        pronunciation = pronunciation.replace('dh', 'dʰ')
        pronunciation = pronunciation.replace('ph', 'pʰ')
        pronunciation = pronunciation.replace('bh', 'bʰ')
        pronunciation = pronunciation.replace('ch', 'tʃ')
        pronunciation = pronunciation.replace('sh', 'ʃ')
        pronunciation = pronunciation.replace('ng', 'ŋ')
        
        return pronunciation


class LimbuValidator:
    """Validate Limbu text and script"""
    
    def __init__(self):
        self.limbu_range = (0x1900, 0x194F)
    
    def validate_script(self, text: str) -> bool:
        """Check if text contains valid Limbu script"""
        if not text:
            return False
        
        # Should contain at least one Limbu character
        has_limbu = False
        for char in text:
            if self.limbu_range[0] <= ord(char) <= self.limbu_range[1]:
                has_limbu = True
                break
        
        if not has_limbu and not text.startswith('['):
            return False
        
        # Check for invalid character mixing
        # Limbu text shouldn't have random Latin characters
        for char in text:
            if char.isalpha() and ord(char) < 128:  # Latin letter
                if not (text.startswith('[') and text.endswith(']')):
                    return False
        
        return True
    
    def validate_word_structure(self, word: str) -> bool:
        """Validate Limbu word structure"""
        # Basic validation rules
        # Limbu words typically don't have more than 3 consonants in a row
        consonant_count = 0
        
        for char in word.lower():
            if char in 'bcdfghjklmnpqrstvwxyz':
                consonant_count += 1
                if consonant_count > 3:
                    return False
            else:
                consonant_count = 0
        
        return True
    
    def detect_mixed_script(self, text: str) -> List[str]:
        """Detect mixed script usage"""
        issues = []
        
        words = text.split()
        for word in words:
            has_limbu = any(
                self.limbu_range[0] <= ord(c) <= self.limbu_range[1] 
                for c in word
            )
            has_latin = any(c.isalpha() and ord(c) < 128 for c in word)
            
            if has_limbu and has_latin:
                issues.append(f"Mixed script in word: {word}")
        
        return issues