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
