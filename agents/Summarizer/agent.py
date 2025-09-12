import json
import logging
from typing import Dict, List, Any
from collections import Counter
from crewai import Agent, Task
from crewai.tools import BaseTool
from ..base_agent import BaseAgent, HuggingFaceAPITool