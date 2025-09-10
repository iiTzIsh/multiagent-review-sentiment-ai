"""
Sentiment Scorer Agent
Assigns numerical scores (0-5) to hotel reviews based on sentiment analysis
"""

import json
import logging
import re
from typing import Dict, List, Any
from crewai import Agent, Task
from crewai.tools import BaseTool
from ..base_agent import BaseAgent, HuggingFaceAPITool, parse_agent_response

logger = logging.getLogger('agents.scorer')



class SentimentScoringTool(HuggingFaceAPITool):
    """Tool for generating numerical sentiment scores"""
    
    name: str = "sentiment_scorer"
    description: str = "Generate numerical sentiment scores from 0-5 based on text analysis"
    
    def __init__(self):
        super().__init__("nlptown/bert-base-multilingual-uncased-sentiment")
    
    def _run(self, text: str, sentiment: str = None) -> str:
        """Generate sentiment score for the given text"""
        try:
            payload = {"inputs": text}

            #loop to make api request until correct response is received
            result = self._make_api_request(payload)

            count = 0
            flag = False
            while flag == False and count < 5:

                result = self._make_api_request(payload)
                if isinstance(result, list) and len(result) > 0:
                    predictions = result[0]

                check_score = 0
                for pred in predictions:
                        label = pred['label']
                        score = pred['score']

                        check_score = check_score + score
                if 0.98 <= check_score <= 1.02:
                    flag = True
                else:
                    flag = False     
                count = count + 1

            if flag == False:
                logger.error(f"Sentiment scoring failed: API did not return valid scores after multiple attempts")
                return "Score: 3.0"

                
                # Calculate weighted score based on predictions
                total_score = 0
                for pred in predictions:
                    label = pred['label']
                    score = pred['score']
                    
                    # Map labels to numerical values
                    if 'star' in label.lower() or label.isdigit():
                        # Extract number from label
                        num_match = re.search(r'\d+', label)
                        if num_match:
                            star_value = int(num_match.group())
                            total_score = total_score + (star_value * score)
                    else:
                        # Fallback sentiment mapping
                        sentiment_mapping = {
                            'very_negative': 1,
                            'negative': 2,
                            'neutral': 3,
                            'positive': 4,
                            'very_positive': 5
                        }
                        
                        for sent_key, sent_value in sentiment_mapping.items():
                            if sent_key in label.lower():
                                total_score = total_score + (sent_value * score)
                                break
                #loop end

                # Normalize score to 0-5 range
                final_score = max(0, min(5, total_score))
                return f"Score: {final_score:.1f}"
            
            # Fallback based on sentiment if provided
            if sentiment:
                sentiment_scores = {
                    'positive': 4.0,
                    'neutral': 3.0,
                    'negative': 2.0
                }
                score = sentiment_scores.get(sentiment.lower(), 3.0)
                return f"Score: {score:.1f}"
            
            return "Score: 3.0"
            
        except Exception as e:
            logger.error(f"Sentiment scoring failed: {str(e)}")
            return "Score: 3.0"



class SentimentScorerAgent(BaseAgent):
    """
    Agent responsible for assigning numerical scores to reviews
    """
    
    def __init__(self):
        super().__init__(
            name="Sentiment Scorer",
            role="Review Scoring Specialist",
            goal="Assign accurate numerical scores (0-5) to hotel reviews based on sentiment analysis",
            backstory="""You are a data analyst specialized in converting qualitative feedback
            into quantitative metrics. You have extensive experience in the hospitality industry
            and understand how to translate customer emotions into meaningful numerical scores
            that help hotel managers track satisfaction trends."""
        )
    
    def setup_tools(self) -> List[BaseTool]:
        """Setup tools for sentiment scoring"""
        self.tools = [SentimentScoringTool()]
        return self.tools
    
    def create_agent(self) -> Agent:
        """Create the CrewAI agent for sentiment scoring"""
        tools = self.setup_tools()
        
        self.agent = Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=tools,
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        
        return self.agent
    
    def create_task(self, description: str, context: Dict[str, Any]) -> Task:
        """Create a sentiment scoring task"""
        review = context.get('review', {})
        sentiment = context.get('sentiment', '')
        review_text = review.get('text', description)
        
        task_description = f"""
        Assign a numerical score from 0-5 to the following hotel review based on its sentiment and content.
        
        Review Text: "{review_text}"
        Detected Sentiment: {sentiment}
        
        Scoring Guidelines:
        - 0-1: Very negative (angry, disappointed, major issues)
        - 1-2: Negative (unsatisfied, minor complaints)
        - 2-3: Neutral (mixed feelings, average experience)
        - 3-4: Positive (satisfied, good experience)
        - 4-5: Very positive (delighted, exceptional experience)
        
        Consider:
        - Severity of complaints or praise
        - Specific mentions of hotel services
        - Overall customer satisfaction level
        - Language intensity and emotion
        
        Provide only the numerical score with one decimal place.
        """
        
        return Task(
            description=task_description,
            agent=self.agent,
            expected_output="Numerical score from 0.0 to 5.0"
        )
    

    def score_review(self, review_text: str, sentiment: str = None) -> Dict[str, Any]:
        """
        Score a single review and return structured result
        """
        try:
            result = self.execute_task(
                f"Score review: {review_text}",
                {'review': {'text': review_text}, 'sentiment': sentiment}
            )
            
            # Parse the numerical score
            score = parse_agent_response(result, 'score')
            
            return {
                'score': score,
                'sentiment': sentiment,
                'raw_result': result
            }
            
        except Exception as e:
            logger.error(f"Review scoring failed: {str(e)}")
            return {
                'score': 3.0,
                'sentiment': sentiment or 'neutral',
                'raw_result': str(e)
            }
    
    def batch_score(self, reviews_with_sentiment: List[Dict]) -> List[Dict[str, Any]]:
        """
        Score multiple reviews efficiently
        """
        results = []
        for review_data in reviews_with_sentiment:
            review_text = review_data.get('text', '')
            sentiment = review_data.get('sentiment', '')
            
            result = self.score_review(review_text, sentiment)
            results.append(result)
        
        return results
   