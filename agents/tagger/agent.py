"""
AI-Powered Tags Generator Agent for Topic & Theme Analysis
Uses Google Gemini LLM to generate keywords and topics from review data.
"""

import json
import logging
from typing import List, Dict, Any
import google.generativeai as genai
from utils.api_config import get_gemini_api_key

logger = logging.getLogger(__name__)


class BaseTool:
    """Simple base class to replace langchain BaseTool"""
    def __init__(self):
        pass


class GeminiTagsGeneratorTool(BaseTool):
    """AI tool for generating topic analysis using Google Gemini"""
    
    name: str = "gemini_tags_generator"
    description: str = "Generate topic analysis including keywords, topics, and issues using Google Gemini LLM"
    
    def __init__(self):
        super().__init__()
        object.__setattr__(self, 'name', 'gemini_tags_generator')
        object.__setattr__(self, 'description', 'Generate topic analysis including keywords, topics, and issues using Google Gemini LLM')
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Gemini model"""
        try:
            api_key = get_gemini_api_key()
            if api_key:
                genai.configure(api_key=api_key)
                object.__setattr__(self, 'model', genai.GenerativeModel('gemini-2.0-flash-exp'))
                logger.info("Gemini model initialized successfully for tags generation")
            else:
                logger.error("Gemini API key not found")
                object.__setattr__(self, 'model', None)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            object.__setattr__(self, 'model', None)

    def _run(self, reviews_data: str) -> str:
        """Generate topic analysis from reviews using Gemini"""
        try:
            if not hasattr(self, 'model') or not self.model:
                return self._get_fallback_response()
            
            reviews = json.loads(reviews_data)
            # Generate AI-powered tags for reviews
            
            prompt = f"""
            Analyze these {len(reviews)} hotel reviews and provide topic analysis in JSON format:

            Reviews: {json.dumps(reviews[:50], indent=2)}

            Return JSON with:
            {{
                "positive_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
                "negative_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
                "topic_metrics": {{
                    "service": {{
                        "percentage": 85,
                        "keywords": ["staff", "support", "help"],
                        "description": "Service quality analysis"
                    }},
                    "cleanliness": {{
                        "percentage": 78,
                        "keywords": ["clean", "hygiene", "tidy"],  
                        "description": "Cleanliness standards analysis"
                    }},
                    "location": {{
                        "percentage": 90,
                        "keywords": ["area", "transport", "access"],
                        "description": "Location convenience analysis"
                    }}
                }},
                "main_issues": ["issue1", "issue2", "issue3"],
                "emerging_topics": ["topic1", "topic2", "topic3"]
            }}

            Extract actual keywords from review texts and provide realistic percentages.
            """
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                response_text = response.text.strip()
                
                # Clean markdown formatting
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                # Validate JSON
                try:
                    json.loads(response_text)
                    logger.info("AI tags generation completed successfully")
                    return response_text
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in Gemini response")
                    return self._get_fallback_response()
            else:
                return self._get_fallback_response()
                
        except Exception as e:
            logger.error(f"Error in AI tags generation: {str(e)}")
            return self._get_fallback_response()

    def _get_fallback_response(self) -> str:
        """Return fallback response if AI generation fails"""
        fallback = {
            "positive_keywords": ["excellent", "clean", "friendly", "comfortable", "convenient"],
            "negative_keywords": ["dirty", "noise", "rude", "expensive", "disappointing"],
            "topic_metrics": {
                "service": {
                    "percentage": 75,
                    "keywords": ["staff", "support", "help"],
                    "description": "Service quality analysis"
                },
                "cleanliness": {
                    "percentage": 70,
                    "keywords": ["clean", "hygiene", "tidy"],
                    "description": "Cleanliness standards analysis"
                },
                "location": {
                    "percentage": 80,
                    "keywords": ["area", "transport", "access"],
                    "description": "Location convenience analysis"
                }
            },
            "main_issues": ["service issues", "cleanliness concerns", "noise problems"],
            "emerging_topics": ["technology concerns", "health safety", "value for money"]
        }
        
        return json.dumps(fallback, indent=2)


class TagsGeneratorAgent:
    """Agent for generating tags and topic analysis from hotel reviews"""
    
    def __init__(self):
        self.agent_name = "TagsGeneratorAgent"
        self.tool = GeminiTagsGeneratorTool()
        self.initialized = True
        logger.info("[OK] Tags Generator Agent initialized")
    
    def generate_tags(self, reviews_data: List[Dict]) -> Dict[str, Any]:
        """Generate tags and topics from review data"""
        try:
            if not self.initialized:
                logger.warning("Tags Generator Agent not properly initialized")
                return self._get_default_tags()
            
            if not reviews_data:
                logger.warning("No review data provided for tags generation")
                return self._get_default_tags()
            
            # Convert reviews data to JSON string for the tool
            reviews_json = json.dumps(reviews_data)
            
            # Use the Gemini tool to generate tags
            result = self.tool._run(reviews_json)
            
            # Parse the result
            tags_data = json.loads(result)
            
            logger.info(f"Tags generation completed for {len(reviews_data)} reviews")
            return tags_data
            
        except Exception as e:
            logger.error(f"Tags generation failed: {str(e)}")
            return self._get_default_tags()
    
    def _get_default_tags(self) -> Dict[str, Any]:
        """Return default tags structure"""
        return {
            "positive_keywords": ["good", "nice", "clean", "friendly", "comfortable"],
            "negative_keywords": ["bad", "dirty", "noise", "rude", "expensive"],
            "topic_metrics": {
                "service": {
                    "percentage": 70,
                    "keywords": ["staff", "support"],
                    "description": "Service quality"
                },
                "cleanliness": {
                    "percentage": 65,
                    "keywords": ["clean", "hygiene"],
                    "description": "Cleanliness standards"
                }
            },
            "main_issues": ["service concerns", "cleanliness issues"],
            "emerging_topics": ["general feedback", "basic concerns"]
        }