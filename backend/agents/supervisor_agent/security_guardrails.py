# security_guardrails.py
"""
Production-Grade Medical Domain Guardrails
--------------------------------------------
Designed for natural medical conversations with proper safety boundaries
"""
import re, time, html
from typing import Tuple, Dict, List, Optional

# ==============================================================================
# MEDICAL DOMAIN KNOWLEDGE BASE
# ==============================================================================

# Primary medical symptoms and conditions
MEDICAL_KEYWORDS = set("""
rash acne eczema psoriasis lesion mole nevus wart blister itch itching itchy
erythema redness swelling inflammation bump bumps spot spots patch patches
bleeding bleed bruise bruising pain painful sore soreness hurt hurts burning
discharge pus infection infected inflamed tender tenderness
gum gums tooth teeth cavity caries gingivitis ulcer ulcers mouth lip lips
tongue jaw enamel plaque dental toothache sensitivity
""".split())

# Body parts and anatomical locations (comprehensive)
BODY_PARTS = set("""
arm arms leg legs hand hands foot feet finger fingers toe toes
forearm forearms wrist wrists elbow elbows shoulder shoulders
back chest stomach abdomen belly side sides
head face forehead cheek cheeks chin nose eye eyes ear ears neck throat
skin scalp hair nail nails
upper lower left right middle center
knee knees ankle ankles hip hips thigh thighs calf calves shin shins
""".split())

# Temporal and spatial descriptors
DESCRIPTORS = set("""
about around near between under over above below
halfway quarter third part area region section spot location
since ago days weeks months years yesterday today morning evening night
started began appeared developed showed noticed
small large big tiny huge medium sized
red pink white yellow brown black blue purple green
round circular oval irregular shaped
""".split())

# Personal medical information
PERSONAL_INFO = set("""
age years old months
male female man woman boy girl child adult
height weight tall short heavy light thin
pregnant pregnancy expecting trimester
allergic allergy allergies medication medicine drug
history family personal medical condition conditions
doctor physician dermatologist dentist
""".split())

# Conversational responses (common in follow-ups)
CONVERSATIONAL = set("""
yes no maybe sometimes always never
better worse same different
more less
started stopped changed
it its they them this that these those
""".split())

# Combined medical context vocabulary
MEDICAL_CONTEXT = MEDICAL_KEYWORDS | BODY_PARTS | DESCRIPTORS | PERSONAL_INFO | CONVERSATIONAL


# ==============================================================================
# SECURITY PATTERNS
# ==============================================================================

PRIVATE_IP_RE = re.compile(
    r"(^127\.0\.0\.1)|(^10\.)|(^172\.(1[6-9]|2\d|3[0-1])\.)|(^192\.168\.)|(^0\.)|(^169\.254\.)"
)

INJECTION_PATTERNS = [
    r"(?i)\bignore (all|previous) (instructions|rules|prompts)\b",
    r"(?i)\bdisregard (the )?(system|previous|prior) (prompt|instruction)\b",
    r"(?i)\boverride (the )?(safety|security|system)\b",
    r"(?i)\byou are (now |)chatgpt\b",
    r"(?i)\bpretend (you|to) (are|be)\b.*\b(not|different)\b",
    r"(?i)\breset (your|the) (instructions|rules|system)\b",
]

DISALLOWED_IMAGE_HOSTS = [r"localhost", r"file:", r"metadata\.googleinternal"]


# ==============================================================================
# RATE LIMITER
# ==============================================================================

class RateLimiter:
    """Token bucket rate limiter with separate limits for text and image requests"""
    
    def __init__(self):
        self.bucket = {}  # key -> [(timestamp...)]
        self.limits = {
            "text": (30, 60),      # 30 requests per 60 seconds
            "image": (5, 3600)     # 5 requests per hour
        }

    def check(self, user_id: str, kind: str) -> Tuple[bool, str]:
        limit, window = self.limits.get(kind, (30, 60))
        now = time.time()
        key = (user_id, kind)
        
        # Initialize or get request history
        if key not in self.bucket:
            self.bucket[key] = []
        
        # Remove expired timestamps
        self.bucket[key] = [t for t in self.bucket[key] if now - t < window]
        
        # Check if limit exceeded
        if len(self.bucket[key]) >= limit:
            wait_time = int(window - (now - self.bucket[key][0]))
            return False, f"Rate limit exceeded. Please try again in {wait_time} seconds."
        
        # Add current request
        self.bucket[key].append(now)
        return True, ""


# ==============================================================================
# PROMPT INJECTION DETECTOR
# ==============================================================================

class PromptInjectionDetector:
    """Detects attempts to manipulate the AI system through prompt injection"""
    
    def detect(self, text: str) -> Tuple[bool, str]:
        if not text:
            return False, ""
        
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text):
                return True, "Invalid input detected"
        
        return False, ""


# ==============================================================================
# DOMAIN GROUNDING (Medical Context Validation)
# ==============================================================================

class DomainGrounding:
    """
    Intelligent medical domain validation with conversation awareness.
    Designed for natural medical conversations while maintaining safety boundaries.
    """
    
    def __init__(self):
        self.medical_context = MEDICAL_CONTEXT
        self.body_parts = BODY_PARTS
        self.descriptors = DESCRIPTORS
    
    def is_in_domain(self, text: str, speciality: str, history: List = None) -> Tuple[bool, str]:
        """
        Validates if message is appropriate for medical consultation.
        
        Progressive trust model:
        1. Empty history + specialty selected = Allow if medical context OR descriptive response
        2. Medical history present = Very permissive (trust conversation flow)
        3. No medical context anywhere = Reject with helpful guidance
        
        Args:
            text: Current user message
            speciality: "skin" or "oral" (user's explicit selection)
            history: Previous conversation messages
            
        Returns:
            (is_valid, error_message)
        """
        if not text:
            return True, ""
        
        # Tokenize message
        text_lower = text.lower()
        tokens = set(re.findall(r'[a-z]+', text_lower))
        
        # =========================================================================
        # SIGNAL 1: Direct medical keywords
        # =========================================================================
        if tokens & MEDICAL_KEYWORDS:
            return True, ""
        
        # =========================================================================
        # SIGNAL 2: Body parts + specialty match
        # =========================================================================
        has_body_part = bool(tokens & BODY_PARTS)
        if has_body_part:
            # Body part mentioned = likely medical context
            return True, ""
        
        # =========================================================================
        # SIGNAL 3: Medical descriptors (location, time, severity)
        # =========================================================================
        has_descriptors = bool(tokens & DESCRIPTORS)
        descriptor_count = len(tokens & DESCRIPTORS)
        
        # Messages like "on my left arm, about halfway up" have many descriptors
        if descriptor_count >= 2 and len(tokens) <= 20:
            # Short message with spatial/temporal descriptors = likely medical response
            return True, ""
        
        # =========================================================================
        # SIGNAL 4: Personal medical information
        # =========================================================================
        has_personal_info = bool(tokens & PERSONAL_INFO)
        if has_personal_info and len(tokens) <= 15:
            # Short messages with age/gender/medical history = relevant context
            return True, ""
        
        # =========================================================================
        # SIGNAL 5: Conversation history analysis
        # =========================================================================
        if history and len(history) > 0:
            # Check if conversation has established medical context
            has_medical_context = self._analyze_conversation_context(history, speciality)
            
            if has_medical_context:
                # In active medical conversation - be very permissive
                # Allow follow-up responses even without explicit medical terms
                
                # Common follow-up patterns that should be allowed:
                # - "It's on my left arm"
                # - "About 3 days ago"
                # - "Yes, it's getting worse"
                # - "35 years old, male"
                
                is_followup_response = (
                    len(tokens) <= 20 or  # Short responses
                    has_descriptors or     # Location/time descriptors
                    any(w in tokens for w in ['yes', 'no', 'it', 'its', 'this', 'that'])  # Conversational
                )
                
                if is_followup_response:
                    return True, ""
        
        # =========================================================================
        # SIGNAL 6: Specialty selection (user explicitly chose medical domain)
        # =========================================================================
        # If user selected a specialty, they're seeking medical consultation
        # Allow ambiguous but potentially medical messages
        if speciality in ["skin", "oral"]:
            # Check for specialty-specific context
            specialty_keywords = {
                "skin": ["skin", "derma", "face", "body", "area", "spot", "mark"],
                "oral": ["tooth", "teeth", "mouth", "dental", "bite", "chew", "taste"]
            }
            
            if any(word in text_lower for word in specialty_keywords.get(speciality, [])):
                return True, ""
            
            # Allow very short messages in specialty context (likely answers to questions)
            if len(tokens) <= 10 and (has_descriptors or has_personal_info):
                return True, ""
        
        # =========================================================================
        # REJECTION: No medical context detected
        # =========================================================================
        # Only reject if clearly off-topic
        
        # Check for obviously non-medical content
        non_medical_patterns = [
            r'\b(weather|sports|politics|news|recipe|movie|music)\b',
            r'\b(how to (make|cook|build|install))\b',
            r'\b(what is (the|a) (capital|president|weather))\b',
        ]
        
        for pattern in non_medical_patterns:
            if re.search(pattern, text_lower):
                return False, self.off_topic_response()
        
        # If we reach here: ambiguous message without clear medical context
        # Decision: Reject with helpful guidance
        return False, self.off_topic_response()
    
    def _analyze_conversation_context(self, history: List, speciality: str) -> bool:
        """
        Analyze conversation history to determine if medical context is established.
        
        Returns True if:
        - Any message contains medical keywords
        - Body parts mentioned in specialty context
        - Multiple descriptive medical terms present
        """
        if not history:
            return False
        
        # Look at recent conversation (last 10 messages)
        recent_messages = history[-10:] if len(history) > 10 else history
        
        # Combine all message content
        combined_text = " ".join([
            msg.get("content", "") if isinstance(msg, dict) else str(msg)
            for msg in recent_messages
        ]).lower()
        
        # Tokenize conversation history
        history_tokens = set(re.findall(r'[a-z]+', combined_text))
        
        # Check for medical context
        has_medical_keywords = bool(history_tokens & MEDICAL_KEYWORDS)
        has_body_parts = bool(history_tokens & BODY_PARTS)
        has_descriptors = len(history_tokens & DESCRIPTORS) >= 3
        
        # Specialty-specific context
        specialty_context = {
            "skin": ["skin", "derma", "rash", "mole", "itch", "face", "arm", "leg", "back"],
            "oral": ["tooth", "teeth", "gum", "mouth", "dental", "bite", "jaw", "tongue"]
        }
        
        has_specialty_context = any(
            word in combined_text 
            for word in specialty_context.get(speciality, [])
        )
        
        # Consider context established if any strong signal present
        return has_medical_keywords or has_specialty_context or (has_body_parts and has_descriptors)
    
    @staticmethod
    def off_topic_response() -> str:
        """Helpful error message for off-topic queries"""
        return (
            "I'm designed to help with skin and oral health concerns. "
            "Please describe your medical symptoms or concern. "
            "For example: 'I have a rash on my arm' or 'My gums are bleeding'."
        )


# ==============================================================================
# CONTENT MODERATOR
# ==============================================================================

class ContentModerator:
    """Screens for harmful, dangerous, or inappropriate content"""
    
    def moderate(self, text: str) -> Tuple[bool, str, str]:
        """
        Returns: (is_safe, category, message)
        """
        if not text:
            return True, "safe", ""
        
        text_lower = text.lower()
        
        # Emergency/crisis content
        crisis_patterns = [
            r'\b(suicide|kill myself|end my life|want to die)\b',
            r'\b(self.harm|cutting myself|hurt myself)\b',
        ]
        
        for pattern in crisis_patterns:
            if re.search(pattern, text_lower):
                return False, "emergency", self.emergency_response()
        
        # Input validation
        if len(text) > 8000:
            return False, "validation", "Message too long. Please keep messages under 8000 characters."
        
        # Spam/abuse detection (very basic)
        if len(set(text.lower().split())) < 3 and len(text) > 50:
            # Repeated characters or words
            return False, "validation", "Invalid message format"
        
        return True, "safe", ""
    
    @staticmethod
    def emergency_response() -> str:
        """Crisis response message"""
        return (
            "I'm concerned about your safety. If you're in crisis or considering self-harm, "
            "please contact emergency services immediately (call 911 in the US) or reach out to "
            "a crisis helpline like the 988 Suicide & Crisis Lifeline (call or text 988). "
            "Your life matters and help is available 24/7."
        )


# ==============================================================================
# RESPONSE SANITIZER
# ==============================================================================

class ResponseSanitizer:
    """Cleans and sanitizes text output"""
    
    def sanitize_text(self, text: str) -> str:
        """Remove potentially dangerous content from text"""
        if not text:
            return ""
        
        # HTML escape
        sanitized = html.escape(text)
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', sanitized)
        
        return sanitized.strip()


# ==============================================================================
# SECURITY ORCHESTRATOR
# ==============================================================================

class SecurityOrchestrator:
    """
    Main security coordination layer.
    Orchestrates all security checks with proper logging and metrics.
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.rate_limiter = RateLimiter()
        self.injection_detector = PromptInjectionDetector()
        self.domain_grounding = DomainGrounding()
        self.moderator = ContentModerator()
        self.sanitizer = ResponseSanitizer()
        
        # Metrics (in production, send to monitoring system)
        self.metrics = {
            "total_requests": 0,
            "blocked_requests": 0,
            "block_reasons": {}
        }
    
    def validate_input(
        self,
        user_id: str,
        message: str,
        req_type: str,
        speciality: str,
        history: List = None
    ) -> Tuple[bool, str, Dict]:
        """
        Comprehensive input validation with multiple security layers.
        
        Returns:
            (is_valid, error_message, metadata)
        """
        self.metrics["total_requests"] += 1
        
        if not self.enabled:
            return True, "", {"category": "security_disabled"}
        
        # Sanitize input early
        message = (message or "").strip()
        
        # Layer 1: Rate limiting
        ok, msg = self.rate_limiter.check(user_id, "text" if req_type == "text" else "image")
        if not ok:
            self._track_block("rate_limit")
            return False, msg, {"error_type": "rate_limit"}
        
        # Layer 2: Prompt injection detection
        suspicious, inj_msg = self.injection_detector.detect(message)
        if suspicious:
            self._track_block("injection")
            return False, "Invalid input detected.", {"error_type": "security"}
        
        # Layer 3: Domain grounding (for text messages)
        if req_type == "text":
            in_domain, domain_msg = self.domain_grounding.is_in_domain(
                message, speciality, history=history
            )
            if not in_domain:
                self._track_block("off_topic")
                return False, domain_msg, {"error_type": "off_topic"}
        
        # Layer 4: Content moderation
        safe, category, mod_msg = self.moderator.moderate(message)
        if not safe:
            self._track_block(category)
            if category == "emergency":
                return False, mod_msg, {"error_type": "emergency"}
            return False, mod_msg or "Inappropriate content", {"error_type": category}
        
        # All checks passed
        return True, "", {"category": "safe"}
    
    def sanitize_output(self, text: str) -> str:
        """Sanitize text output before returning to user"""
        return self.sanitizer.sanitize_text(text)
    
    def _track_block(self, reason: str):
        """Track blocked requests for monitoring"""
        self.metrics["blocked_requests"] += 1
        self.metrics["block_reasons"][reason] = self.metrics["block_reasons"].get(reason, 0) + 1
    
    def get_metrics(self) -> Dict:
        """Return current security metrics"""
        return {
            **self.metrics,
            "block_rate": self.metrics["blocked_requests"] / max(self.metrics["total_requests"], 1)
        }