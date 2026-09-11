#!/usr/bin/env python3
"""Tests for the RAG query classifier."""

import sys
from pathlib import Path

import pytest

# Add rag directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rag"))

from rag.query_classifier import QueryClassifier


@pytest.fixture
def classifier():
    return QueryClassifier()


class TestGreetingDetection:
    def test_hey(self, classifier):
        result = classifier.classify("Hey AIdo")
        assert result.type == "greeting"
        assert "Hello" in result.response

    def test_hello(self, classifier):
        result = classifier.classify("Hello there")
        assert result.type == "greeting"

    def test_hi(self, classifier):
        result = classifier.classify("Hi")
        assert result.type == "greeting"

    def test_good_morning(self, classifier):
        result = classifier.classify("Good morning!")
        assert result.type == "greeting"

    def test_case_insensitive(self, classifier):
        result = classifier.classify("HEY AIDO")
        assert result.type == "greeting"


class TestOffTopicDetection:
    def test_joke_request(self, classifier):
        result = classifier.classify("Tell me a joke")
        assert result.type == "off_topic"

    def test_weather(self, classifier):
        result = classifier.classify("What's the weather?")
        assert result.type == "off_topic"

    def test_time(self, classifier):
        result = classifier.classify("What time is it?")
        assert result.type == "off_topic"

    def test_no_domain_keywords(self, classifier):
        result = classifier.classify("Who is the president?")
        assert result.type == "off_topic"


class TestDomainDetection:
    def test_jellyfin_question(self, classifier):
        result = classifier.classify("How to enable Jellyfin hardware transcoding?")
        assert result.type == "domain"

    def test_docker_question(self, classifier):
        result = classifier.classify("How do I restart my Docker containers?")
        assert result.type == "domain"

    def test_nextcloud_question(self, classifier):
        result = classifier.classify("What is Nextcloud used for?")
        assert result.type == "domain"

    def test_thuis_question(self, classifier):
        result = classifier.classify("How does thuis work?")
        assert result.type == "domain"

    def test_multiple_keywords(self, classifier):
        result = classifier.classify("How to set up Traefik with Docker?")
        assert result.type == "domain"
