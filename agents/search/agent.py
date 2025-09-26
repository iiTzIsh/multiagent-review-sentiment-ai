"""
Review Search Agent - CrewAI Implementation
Search and filter hotel reviews based on various criteria

AGENT ROLE: Review Search Expert
- Well-defined role: Search and retrieve hotel reviews based on multiple criteria
- Clear responsibility: Filter reviews by sentiment, score range, keywords, and date
- Communication: Uses CrewAI framework for task execution and tool integration
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from crewai import Agent, Task
from crewai.tools import BaseTool

logger = logging.getLogger('agents.searcher')
