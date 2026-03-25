# Bot Development Plan

## Overview

This document outlines the development plan for building a Telegram bot that interfaces with the LMS (Learning Management System) backend. The bot enables students to check system health, browse available labs, view scores, and ask questions using natural language.

## Task 1: Project Scaffold

**Goal:** Establish a testable handler architecture with CLI test mode.

**Approach:**
- Create a `bot/` directory with clear separation between handlers (business logic) and the Telegram transport layer
- Implement `--test` mode in the entry point that calls handlers directly without connecting to Telegram
- Handlers are plain functions: they take a command string and return text responses
- This architecture enables offline testing and makes handlers reusable across test modes and Telegram

**Files:** `bot.py` (entry point), `handlers/` (command logic), `config.py` (environment loading)

## Task 2: Backend Integration

**Goal:** Connect handlers to the LMS backend API with real data.

**Approach:**
- Build an API client in `services/api_client.py` that wraps HTTP calls to the backend
- Use Bearer token authentication with `LMS_API_KEY` from environment variables
- Update handlers to call the API client instead of returning placeholders
- Implement error handling: backend failures produce friendly messages, not crashes
- Commands: `/health` (status check), `/labs` (list labs), `/scores <lab>` (pass rates)

**Key pattern:** Environment variables for URLs and credentials — never hardcode secrets.

## Task 3: Intent-Based Natural Language Routing

**Goal:** Enable plain text queries using an LLM for intent recognition.

**Approach:**
- Wrap all backend endpoints as "tools" with clear descriptions for the LLM
- When a user sends plain text (not a slash command), the LLM decides which tool to call
- Tool description quality matters more than prompt engineering — the LLM reads descriptions to make decisions
- Implement an intent router that sends non-command messages to the LLM
- Fallback: if the LLM service is unreachable, return a graceful error message

**Key insight:** Don't use regex or keyword matching to route intents. The LLM's job is to understand user intent from tool descriptions.

## Task 4: Containerization and Deployment

**Goal:** Deploy the bot alongside the backend using Docker Compose.

**Approach:**
- Create a `Dockerfile` for the bot using the same Python base image as the backend
- Add the bot as a service in `docker-compose.yml`
- Use Docker networking: containers communicate via service names (e.g., `backend`), not `localhost`
- Mount `.env.bot.secret` for configuration
- Document deployment in README with troubleshooting steps

**Key concept:** Container networking uses DNS service names. Inside Docker, `http://backend:8000` reaches the backend, not `http://localhost:8000`.

## Testing Strategy

- **Unit tests:** Test handlers in isolation using `--test` mode
- **Integration tests:** Verify API client with backend (requires running backend)
- **Manual testing:** Deploy to VM and test in Telegram

## Git Workflow

For each task:
1. Create a GitHub issue
2. Create a feature branch: `task-N/description`
3. Open a PR with "Closes #N" in the description
4. Partner review before merge
5. Deploy to VM after merge
