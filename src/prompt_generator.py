"""
Prompt Generator - OpenRouter API client for generating prompts
"""
import json
import requests
from typing import Optional, Dict

from .config import get_config
from .logger import get_logger


# Hardcoded system prompt for sexy dance video generation
SYSTEM_PROMPT = """You are a creative prompt generator for AI image and video creation. Content is for adult entertainment - sexy but tasteful.

Your task is to generate a COMPLETE SET of prompts that are 100% consistent with each other:
1. IMAGE PROMPT: Describe a single seductive woman with SPECIFIC details about clothing, pose, and environment. She must be LOOKING DIRECTLY AT THE CAMERA with seductive eye contact.
2. VIDEO 1 PROMPT: 2 sensual teasing actions that EXACTLY match the clothing/pose from the image prompt. She maintains eye contact with camera throughout.
3. VIDEO 2 PROMPT: 2 continuation actions that flow naturally from video 1. She keeps looking at camera seductively.

CLOTHING OPTIONS (pick one per generation):
- Sexy lingerie set (lace bra and panties)
- Tiny bikini showing curves
- Sheer bodysuit with visible silhouette
- Crop top and tight shorts
- Low-cut dress or nightgown
- Tight bodycon dress

TEASING ACTIONS TO INCLUDE:
- Slowly adjusting bra straps, pulling them down shoulders
- Running hands along curves sensually
- Playing with waistband/panty strings teasingly
- Arching back to emphasize figure
- Caressing thighs and hips slowly
- Biting lip while touching body
- Turning around showing back/behind
- Dancing seductively with hip movements
- Unbuttoning or unzipping clothing slowly
- Stretching arms up to show body
- Lying down in provocative pose

CRITICAL RULES:
- Clothing in IMAGE PROMPT must match the teasing actions
- Actions should be suggestive and teasing, not fully explicit
- Movements should be slow, sensual, and captivating
- Focus on body language and seduction
- Actions should progressively get more teasing from video1 to video2

OUTPUT FORMAT (JSON):
{
  "image_prompt": "A seductive woman wearing [sexy clothing], in [alluring pose], [environment]...",
  "video1_prompt": "She [teasing action 1], then [teasing action 2]. Sensual and captivating movements.",
  "video2_prompt": "She continues with [teasing action 3], then [teasing action 4]. Smooth and seductive."
}

Only output the JSON, nothing else."""


class PromptGenerator:
    """Generate prompts using OpenRouter API."""
    
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self):
        """Initialize prompt generator."""
        self.config = get_config()
        self.logger = get_logger()
    
    def _get_api_key(self) -> str:
        """Get OpenRouter API key from config."""
        return self.config.get("openrouter_api_key", "")
    
    def _get_model(self) -> str:
        """Get OpenRouter model from config."""
        return self.config.get("openrouter_model", "")
    
    def generate_prompts(self) -> Optional[Dict[str, str]]:
        """
        Generate image and video prompts.
        
        Returns:
            Dict with keys: image_prompt, video1_prompt, video2_prompt
            or None if failed
        """
        api_key = self._get_api_key()
        model = self._get_model()
        
        if not api_key:
            self.logger.error("Chưa cấu hình OpenRouter API key")
            return None
        
        if not model:
            self.logger.error("Chưa cấu hình OpenRouter model")
            return None
        
        self.logger.info(f"Đang tạo prompt với model: {model}")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Add randomization to break repetitive patterns
        import random
        from datetime import datetime
        
        random_seed = random.randint(1000, 9999)
        timestamp = datetime.now().strftime("%H%M%S")
        
        # Random style/theme variations to encourage diversity
        styles = [
            # Phong cách kinh điển & quyến rũ
            "elegant and classy lingerie goddess",
            "wild and untamed sex kitten",
            "sweet and innocent but dangerously seductive",
            "mysterious dark femme fatale",
            "playful teasing little devil",
            "confident dominant queen energy",
            "shy but extremely horny",
            "fierce and powerful dominatrix vibes",
            "soft romantic bedroom eyes",
            "naughty schoolgirl gone bad",
            "mature experienced seductress",
            "athletic toned gym bombshell",

            # Phong cách nóng bỏng hơn, táo bạo
            "slutty and proud of it",
            "dripping wet and needy",
            "cum-hungry bedroom stare",
            "bound and begging",
            "just-fucked messy hair glow",
            "oiled up glistening skin",
            "spread wide and shameless",
            "choking hazard throat",
            "dripping honey sweet & filthy",
            "corrupted angel fallen from grace",
            "high-class escort premium service",
            "backseat car quickie energy",

            # Roleplay & fantasy nặng đô
            "bunny girl with very short tail",
            "naughty nurse ready to examine",
            "strict teacher punishment time",
            "maid who doesn't clean at all",
            "succubus ready to drain you",
            "vampire queen blood & lust",
            "catgirl in extreme heat",
            "office slut after hours",
            "cheerleader with no panties",
            "bride on her last wild night",
            "police officer frisking you hard",
            "japanese gravure idol wet shirt",

            # Aesthetic & mood đặc trưng
            "neon cyberpunk strip club",
            "gothic victorian dark erotica",
            "vaporwave pastel lewd",
            "luxury sugar baby aesthetic",
            "y2k trashy hot mess",
            "e-girl onlyfans teaser",
            "softcore morning after glow",
            "hardcore BDSM dungeon queen",
            "glamour pornstar red carpet",
            "tropical vacation sex on the beach",
            "winter fireplace slow sensual",
            "sweaty summer midnight hookup",
        ]
        
        locations = [
            "luxurious bedroom with silk sheets", "steamy bathroom with foggy mirror",
            "beach cabana at sunset", "private pool with underwater lights",
            "penthouse with city view at night", "studio with professional lighting",
            "cozy living room by fireplace", "outdoor garden at golden hour",
            "hotel room with mood lighting", "yacht deck under stars"
        ]
        
        ethnicities = [
            "Asian", "Caucasian", "Latina", "mixed-race", "Eastern European",
            "Mediterranean", "Nordic", "Middle Eastern", "African", "South Asian"
        ]
        
        chosen_style = random.choice(styles)
        chosen_location = random.choice(locations)
        chosen_ethnicity = random.choice(ethnicities)
        
        user_message = f"""Generate a completely NEW and UNIQUE set of prompts.
        
Random seed: {random_seed}-{timestamp}
Style direction: {chosen_style}
Location: {chosen_location}
Ethnicity: {chosen_ethnicity}

Make this generation DIFFERENT from any previous ones. Be creative and surprising!"""
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "temperature": 1.0,  # Increased for more randomness
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                self.OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                self.logger.error(f"OpenRouter API lỗi: {response.status_code}")
                self.logger.error(f"Phản hồi: {response.text}")
                return None
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Parse JSON from response
            prompts = self._parse_json_response(content)
            
            if prompts:
                self.logger.success("Đã tạo prompt thành công")
                self.logger.info(f"Image prompt: {prompts.get('image_prompt', '')[:100]}...")
            
            return prompts
            
        except requests.RequestException as e:
            self.logger.error(f"Yêu cầu thất bại: {e}")
            return None
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Không thể parse phản hồi: {e}")
            return None
    
    def _parse_json_response(self, content: str) -> Optional[Dict[str, str]]:
        """Parse JSON from model response."""
        # Try to find JSON in response
        content = content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        try:
            prompts = json.loads(content)
            
            # Validate required keys
            required_keys = ["image_prompt", "video1_prompt", "video2_prompt"]
            if all(key in prompts for key in required_keys):
                return prompts
            else:
                self.logger.error("Thiếu key bắt buộc trong phản hồi")
                return None
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON không hợp lệ: {e}")
            self.logger.debug(f"Content: {content[:500]}")
            return None


def generate_prompts() -> Optional[Dict[str, str]]:
    """Convenience function to generate prompts."""
    generator = PromptGenerator()
    return generator.generate_prompts()
