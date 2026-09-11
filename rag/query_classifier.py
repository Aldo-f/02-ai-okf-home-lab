#!/usr/bin/env python3
"""
Query classifier for OKF RAG system.

Classifies incoming queries into:
- GREETING: casual greeting → return friendly response, skip RAG
- OFF_TOPIC: clearly unrelated to home-lab docs → return "I don't know"
- DOMAIN: relevant question → proceed to RAG retrieval
"""

import re
from dataclasses import dataclass
from typing import Literal


@dataclass
class Classification:
    type: Literal["greeting", "off_topic", "domain"]
    response: str
    question: str = ""


# Patterns for greeting detection (case-insensitive)
GREETING_PATTERNS = [
    r"^hi\b",
    r"^hello\b",
    r"^hey\b",
    r"^good\s+(morning|afternoon|evening)\b",
    r"^howdy\b",
    r"^greetings\b",
    r"^yo\b",
    r"^\*\w+\*$",  # *waves* style
]

# Patterns for off-topic detection (clearly non-home-lab)
OFF_TOPIC_PATTERNS = [
    r"\b(translate|翻译成|翻译为)\b.*\b(hello|world|apple|cat|dog)\b",
    r"\b(what's?\s+the\s+time|what\s+time\s+is\s+it)\b",
    r"\b(what's?\s+the\s+weather)\b",
    r"\b(joke|funny|laugh)\b",
    r"\b(tell\s+me\s+a\s+story)\b",
    r"\b(how\s+are\s+you)\b",
    r"\b(who\s+are\s+you)\b",  # Except "who built this"
]

# Home-lab domain keywords (if none match, likely off-topic)
DOMAIN_KEYWORDS = [
    "jellyfin", "plex", "nextcloud", "traefik", "docker", "pihole",
    "home-lab", "homelab", "nas", "synology", "qnap", "unraid",
    "nginx", "apache", "mysql", "postgres", "redis", "mqtt",
    "grafana", "prometheus", "influxdb", "node-red", "zigbee",
    "zwave", "homeassistant", "esphome", "tasmota",
    "thuis", "blanky", "okf", "pino", "passive income",
    "scraper", "watchlist", "download", "stream", "media",
    "automation", "script", "backup", "monitoring", "alert",
]


class QueryClassifier:
    """Classifies queries before RAG retrieval."""

    def __init__(self, min_domain_keywords: int = 1):
        self.greeting_patterns = [re.compile(p, re.IGNORECASE) for p in GREETING_PATTERNS]
        self.off_topic_patterns = [re.compile(p, re.IGNORECASE) for p in OFF_TOPIC_PATTERNS]
        self.min_domain_keywords = min_domain_keywords

    def classify(self, question: str) -> Classification:
        """
        Classify a query.

        Returns:
            Classification with type and appropriate response
        """
        question_stripped = question.strip()

        # Check greetings first
        for pattern in self.greeting_patterns:
            if pattern.match(question_stripped):
                return Classification(
                    type="greeting",
                    response="Hello! I'm AIdo, your OKF home-lab assistant. How can I help you today?",
                    question=question_stripped,
                )

        # Check off-topic patterns
        for pattern in self.off_topic_patterns:
            if pattern.search(question_stripped):
                return Classification(
                    type="off_topic",
                    response="I don't have information about that in my documentation. Could you ask about your home-lab setup, media servers, automation, or OKF projects?",
                    question=question_stripped,
                )

        # Check domain relevance
        question_lower = question_stripped.lower()
        keyword_count = sum(1 for kw in DOMAIN_KEYWORDS if kw.lower() in question_lower)

        if keyword_count < self.min_domain_keywords:
            return Classification(
                type="off_topic",
                response="I don't have information about that in my documentation. Could you ask about your home-lab setup, media servers, automation, or OKF projects?",
                question=question_stripped,
            )

        return Classification(
            type="domain",
            response="",
            question=question_stripped,
        )
