"""
Title Generation Agent for Hotel Review Analysis
Uses AI to generate concise, meaningful titles for reviews based on content.
"""

import json
import logging
import os
import re
from typing import Dict, Any, List
from crewai import Agent, Task
from crewai.tools import BaseTool
import requests

logger = logging.getLogger('agents.title_generator')


class TitleGenerationTool(BaseTool):
    name: str = "title_generator"
    description: str = "Generate concise titles for hotel reviews based on content"
    
    def __init__(self):
        super().__init__()
        self._api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        self._api_key = os.getenv('HUGGINGFACE_API_KEY', '')

    def _run(self, text: str, sentiment: str = None) -> str:
        """Generate title using advanced text analysis"""
        try:
            # Use intelligent title generation (disable HuggingFace for reliability)
            title = self._intelligent_title_generation(text, sentiment)
            
            # Skip HuggingFace API for faster, more reliable titles
            # if self._api_key and len(self._api_key) > 10:
            #     enhanced_title = self._try_bart_enhancement(text, title)
            #     if enhanced_title and len(enhanced_title) > len(title):
            #         title = enhanced_title
            
            return f"Title: {title}"
            
        except Exception as e:
            logger.error(f"Title generation error: {str(e)}")
        
        return self._fallback_title_generation(text, sentiment)

    def _intelligent_title_generation(self, text: str, sentiment: str = None) -> str:
        """Generate intelligent titles using text analysis"""
        if not text or len(text.strip()) < 10:
            return "Short Review"
        
        # Clean and prepare text
        text_clean = re.sub(r'[^\w\s.,!?-]', '', text)
        sentences = re.split(r'[.!?]+', text_clean)
        
        # Find the most important sentence/phrase
        important_phrases = self._extract_key_phrases(text_clean)
        
        # Generate title based on content analysis
        if important_phrases:
            base_title = important_phrases[0]
        else:
            # Use first meaningful sentence
            base_title = self._get_first_meaningful_sentence(sentences)
        
        # Format and enhance the title
        title = self._format_intelligent_title(base_title, sentiment)
        
        return title
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from review text"""
        phrases = []
        text_lower = text.lower()
        
        # Hotel experience patterns
        experience_patterns = [
            (r'(amazing|excellent|outstanding|perfect|great|wonderful)\s+([\w\s]{1,30})', 'positive'),
            (r'(terrible|awful|horrible|disappointing|poor|bad)\s+([\w\s]{1,30})', 'negative'),
            (r'(love|loved|enjoyed|impressed|delighted)\s+([\w\s]{1,30})', 'positive'),
            (r'(hate|hated|disliked|frustrated|disappointed)\s+([\w\s]{1,30})', 'negative'),
            (r'(best|worst|favorite|favourite)\s+([\w\s]{1,30})', 'neutral'),
        ]
        
        # Service and amenity patterns
        amenity_patterns = [
            (r'(staff|service|reception|concierge)\s+(was|were)\s+([\w\s]{1,25})', 'service'),
            (r'(room|rooms|accommodation)\s+(was|were)\s+([\w\s]{1,25})', 'room'),
            (r'(breakfast|food|restaurant|dining)\s+(was|were)\s+([\w\s]{1,25})', 'dining'),
            (r'(location|area|neighborhood)\s+(is|was)\s+([\w\s]{1,25})', 'location'),
            (r'(wifi|internet|connection)\s+(was|were)\s+([\w\s]{1,25})', 'amenities'),
            (r'(pool|gym|spa|facilities)\s+(was|were)\s+([\w\s]{1,25})', 'facilities'),
        ]
        
        # Check patterns and extract phrases
        all_patterns = experience_patterns + amenity_patterns
        
        for pattern, category in all_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                if len(match.groups()) >= 2:
                    phrase = f"{match.group(1).title()} {match.group(2).title()}"
                    phrase = re.sub(r'\s+', ' ', phrase).strip()
                    if 5 <= len(phrase) <= 40:
                        phrases.append(phrase)
        
        # Remove duplicates and sort by relevance
        unique_phrases = list(dict.fromkeys(phrases))
        return unique_phrases[:3]
    
    def _get_first_meaningful_sentence(self, sentences: List[str]) -> str:
        """Get the first meaningful sentence from the review"""
        for sentence in sentences:
            sentence = sentence.strip()
            if (len(sentence) > 15 and 
                not sentence.lower().startswith(('i ', 'we ', 'my ', 'our ')) and
                any(word in sentence.lower() for word in 
                    ['hotel', 'room', 'staff', 'service', 'location', 'breakfast', 
                     'pool', 'wifi', 'clean', 'comfortable', 'good', 'great', 'bad', 'poor'])):
                return sentence[:50]
        
        # Fallback to first sentence
        if sentences and len(sentences[0]) > 10:
            return sentences[0][:50]
        
        return "Hotel Experience"
    
    def _format_intelligent_title(self, base_title: str, sentiment: str = None) -> str:
        """Format the title intelligently"""
        if not base_title:
            return self._get_sentiment_title(sentiment)
        
        # Clean the title
        title = base_title.strip()
        title = re.sub(r'\s+', ' ', title)
        
        # Remove common unnecessary words
        unnecessary_words = ['the hotel', 'this hotel', 'i think', 'i feel', 'i believe', 
                           'we had', 'we were', 'it was', 'there was', 'there were']
        
        title_lower = title.lower()
        for word in unnecessary_words:
            title_lower = title_lower.replace(word, '')
        
        # Rebuild title with proper capitalization
        words = title_lower.split()
        if not words:
            return self._get_sentiment_title(sentiment)
        
        # Keep only meaningful words (max 4-5 words)
        meaningful_words = []
        skip_words = ['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'was', 'were', 'is', 'are']
        
        for word in words[:8]:  # Look at first 8 words
            if word not in skip_words or len(meaningful_words) == 0:
                meaningful_words.append(word.capitalize())
                if len(meaningful_words) >= 4:
                    break
        
        if not meaningful_words:
            return self._get_sentiment_title(sentiment)
        
        title = ' '.join(meaningful_words)
        
        # Ensure it's not too long
        if len(title) > 45:
            title = title[:42] + "..."
        
        # Add sentiment enhancement if needed
        if sentiment and not self._has_sentiment_word(title):
            title = self._add_sentiment_enhancement(title, sentiment)
        
        return title
    
    def _has_sentiment_word(self, title: str) -> bool:
        """Check if title already has sentiment words"""
        sentiment_words = ['amazing', 'excellent', 'great', 'wonderful', 'perfect', 'outstanding',
                          'terrible', 'awful', 'poor', 'bad', 'horrible', 'disappointing',
                          'good', 'nice', 'decent', 'average', 'okay']
        return any(word in title.lower() for word in sentiment_words)
    
    def _add_sentiment_enhancement(self, title: str, sentiment: str) -> str:
        """Add appropriate sentiment enhancement"""
        if sentiment == 'positive':
            enhancers = ['Excellent', 'Great', 'Amazing', 'Wonderful']
        elif sentiment == 'negative':
            enhancers = ['Poor', 'Disappointing', 'Terrible', 'Bad']
        else:
            enhancers = ['Average', 'Decent', 'Standard']
        
        import random
        enhancer = random.choice(enhancers)
        
        # Only add if title doesn't already start with sentiment
        if not any(title.lower().startswith(word.lower()) for word in enhancers):
            return f"{enhancer} {title}"
        
        return title
    
    def _get_sentiment_title(self, sentiment: str) -> str:
        """Generate title based purely on sentiment"""
        if sentiment == 'positive':
            return "Great Hotel Experience"
        elif sentiment == 'negative':
            return "Disappointing Stay"
        else:
            return "Average Hotel Visit"
    
    def _try_bart_enhancement(self, text: str, current_title: str) -> str:
        """Try to enhance title using BART model"""
        try:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            
            # Use a more focused prompt for better results
            prompt = f"Generate a short hotel review title (4-6 words) for: {text[:300]}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 8,
                    "min_length": 3,
                    "do_sample": True,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(self._api_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0:
                    enhanced = result[0].get('summary_text', '').strip()
                    if enhanced and len(enhanced) > 10:
                        return self._format_title(enhanced)
            
        except Exception as e:
            logger.warning(f"BART enhancement failed: {str(e)}")
        
        return current_title

    def _format_title(self, text: str) -> str:
        """Format text into a proper title"""
        if not text:
            return ""
        
        # Remove common summary artifacts
        text = re.sub(r'^(The|This|It|Hotel|Review|Guest|Customer)\s+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+(says|mentions|states|reports|review|hotel)\s*$', '', text, flags=re.IGNORECASE)
        
        # Capitalize first letter of each word (title case)
        words = text.split()
        formatted_words = []
        
        for word in words[:4]:  # Limit to 4 words max
            # Skip articles and prepositions for title case
            if word.lower() not in ['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with']:
                formatted_words.append(word.capitalize())
            else:
                formatted_words.append(word.lower())
        
        title = ' '.join(formatted_words)
        
        # Ensure it's not too long
        if len(title) > 50:
            title = title[:47] + "..."
        
        return title

    def _enhance_with_sentiment(self, title: str, sentiment: str) -> str:
        """Enhance title based on sentiment"""
        sentiment_enhancers = {
            'positive': ['Great', 'Excellent', 'Amazing', 'Perfect', 'Outstanding'],
            'negative': ['Poor', 'Terrible', 'Disappointing', 'Awful', 'Bad'],
            'neutral': ['Average', 'Decent', 'Okay', 'Standard', 'Typical']
        }
        
        # If title doesn't already convey sentiment, add enhancement
        if sentiment.lower() in sentiment_enhancers:
            enhancers = sentiment_enhancers[sentiment.lower()]
            
            # Check if title already has sentiment words
            has_sentiment = any(enhancer.lower() in title.lower() for enhancer in 
                              sentiment_enhancers['positive'] + 
                              sentiment_enhancers['negative'] + 
                              sentiment_enhancers['neutral'])
            
            if not has_sentiment and title:
                # Add appropriate sentiment word
                import random
                enhancer = random.choice(enhancers)
                title = f"{enhancer} {title}"
        
        return title

    def _fallback_title_generation(self, text: str, sentiment: str = None) -> str:
        """Enhanced fallback title generation"""
        if not text or len(text.strip()) < 5:
            return f"Title: {self._get_sentiment_title(sentiment)}"
        
        text_lower = text.lower()
        
        # Advanced keyword detection
        hotel_aspects = {
            'service': ['service', 'staff', 'reception', 'concierge', 'help', 'assistance'],
            'room': ['room', 'bedroom', 'suite', 'accommodation', 'bed', 'bathroom'],
            'food': ['food', 'breakfast', 'dinner', 'restaurant', 'dining', 'meal', 'buffet'],
            'location': ['location', 'area', 'neighborhood', 'downtown', 'center', 'beach', 'city'],
            'cleanliness': ['clean', 'dirty', 'hygiene', 'sanitized', 'spotless', 'tidy'],
            'value': ['price', 'value', 'money', 'cost', 'expensive', 'cheap', 'affordable'],
            'amenities': ['wifi', 'pool', 'gym', 'spa', 'parking', 'elevator', 'air conditioning'],
            'comfort': ['comfortable', 'cozy', 'spacious', 'quiet', 'peaceful', 'relaxing']
        }
        
        # Find the most relevant aspect
        aspect_scores = {}
        for aspect, keywords in hotel_aspects.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                aspect_scores[aspect] = score
        
        # Generate title based on top aspect and sentiment
        if aspect_scores:
            top_aspect = max(aspect_scores.keys(), key=lambda x: aspect_scores[x])
            title = self._create_aspect_title(top_aspect, sentiment)
        else:
            title = self._get_sentiment_title(sentiment)
        
        return f"Title: {title}"
    
    def _create_aspect_title(self, aspect: str, sentiment: str) -> str:
        """Create title based on aspect and sentiment"""
        aspect_titles = {
            'service': {
                'positive': ['Excellent Service', 'Outstanding Staff', 'Great Service Experience'],
                'negative': ['Poor Service', 'Disappointing Staff', 'Terrible Customer Service'],
                'neutral': ['Average Service', 'Standard Staff', 'Decent Service']
            },
            'room': {
                'positive': ['Amazing Rooms', 'Perfect Accommodation', 'Excellent Room Quality'],
                'negative': ['Poor Room Conditions', 'Disappointing Rooms', 'Terrible Accommodation'],
                'neutral': ['Average Rooms', 'Standard Accommodation', 'Decent Room']
            },
            'food': {
                'positive': ['Excellent Dining', 'Amazing Breakfast', 'Outstanding Food'],
                'negative': ['Poor Food Quality', 'Disappointing Breakfast', 'Terrible Dining'],
                'neutral': ['Average Food', 'Standard Dining', 'Decent Breakfast']
            },
            'location': {
                'positive': ['Perfect Location', 'Excellent Area', 'Great Location Choice'],
                'negative': ['Poor Location', 'Disappointing Area', 'Bad Location'],
                'neutral': ['Average Location', 'Standard Area', 'Decent Location']
            },
            'cleanliness': {
                'positive': ['Spotless Hotel', 'Excellent Cleanliness', 'Very Clean'],
                'negative': ['Poor Hygiene', 'Dirty Conditions', 'Cleanliness Issues'],
                'neutral': ['Average Cleanliness', 'Standard Hygiene', 'Decent Cleaning']
            },
            'value': {
                'positive': ['Excellent Value', 'Great Price Point', 'Worth Every Penny'],
                'negative': ['Poor Value', 'Overpriced Stay', 'Not Worth Money'],
                'neutral': ['Average Value', 'Fair Pricing', 'Decent Value']
            },
            'amenities': {
                'positive': ['Great Amenities', 'Excellent Facilities', 'Amazing Features'],
                'negative': ['Poor Amenities', 'Disappointing Facilities', 'Lacking Features'],
                'neutral': ['Average Amenities', 'Standard Facilities', 'Decent Features']
            },
            'comfort': {
                'positive': ['Very Comfortable', 'Extremely Relaxing', 'Perfect Comfort'],
                'negative': ['Uncomfortable Stay', 'Poor Comfort', 'Unpleasant Experience'],
                'neutral': ['Average Comfort', 'Standard Relaxation', 'Decent Comfort']
            }
        }
        
        import random
        sentiment_key = sentiment if sentiment in ['positive', 'negative', 'neutral'] else 'neutral'
        
        if aspect in aspect_titles:
            titles = aspect_titles[aspect][sentiment_key]
            return random.choice(titles)
        
        return self._get_sentiment_title(sentiment)


class ReviewTitleGeneratorAgent:
    def __init__(self):
        self.name = "ReviewTitleGenerator"
        self.role = "Title Generation Specialist"
        self.goal = "Generate concise, meaningful titles for hotel reviews"
        self.backstory = "Expert in creating catchy, informative titles that capture the essence of customer reviews"
        self.tools = [TitleGenerationTool()]
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.tools,
            verbose=False,
            allow_delegation=False,
            max_iter=2
        )
    
    def create_task(self, review_text: str, sentiment: str = None) -> Task:
        task_description = f"""
        Generate a concise, meaningful title for this hotel review: "{review_text}"
        Sentiment: {sentiment or 'Unknown'}
        
        The title should:
        - Be 2-5 words long
        - Capture the main theme/experience
        - Reflect the sentiment appropriately
        - Be professional and clear
        
        Use the title_generator tool and provide a clean title.
        """
        
        return Task(
            description=task_description,
            agent=self.agent,
            expected_output="A concise title that captures the review's essence"
        )
    
    def generate_title(self, review_text: str, sentiment: str = None) -> Dict[str, Any]:
        """Direct title generation without CrewAI workflow"""
        try:
            tool = TitleGenerationTool()
            result = tool._run(review_text, sentiment)
            
            # Parse result
            title_match = re.search(r'Title:\s*(.+)', result)
            title = title_match.group(1).strip() if title_match else 'Untitled Review'
            
            # Ensure title is reasonable length
            if len(title) > 50:
                title = title[:47] + "..."
            
            return {
                'title': title,
                'confidence': 0.8 if title != 'Untitled Review' else 0.3,
                'sentiment': sentiment or 'neutral',
                'raw_result': result
            }
            
        except Exception as e:
            logger.error(f"Title generation failed: {str(e)}")
            return {
                'title': 'Untitled Review',
                'confidence': 0.0,
                'sentiment': sentiment or 'neutral',
                'raw_result': 'Error occurred during title generation'
            }

    def batch_generate_titles(self, reviews_with_sentiment: List[Dict]) -> List[Dict[str, Any]]:
        """Generate titles for multiple reviews"""
        return [self.generate_title(review.get('text', ''), review.get('sentiment', '')) 
                for review in reviews_with_sentiment]