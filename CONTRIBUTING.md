# Contributing to Arohan

First off, thank you for considering contributing to Arohan! It's people like you that make Arohan such a great tool for the elderly.

Arohan is an emergency response application designed to provide immediate assistance during medical emergencies. By contributing, you are helping us build a more reliable and accessible safety net for those who need it most.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Style Guides](#style-guides)
  - [Git Commit Messages](#git-commit-messages)
  - [TypeScript Style Guide](#typescript-style-guide)
  - [Python Style Guide](#python-style-guide)
- [Project Structure](#project-structure)

---

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for Arohan. Following these guidelines helps maintainers and contributors understand your report, reproduce the behavior, and find related reports.

- **Use a clear and descriptive title** for the issue to identify the problem.
- **Describe the exact steps which reproduce the problem** in as many details as possible.
- **Provide specific examples to demonstrate the steps.** Include links to files or copy-pasteable snippets, which you use in those steps.
- **Describe the behavior you observed after following the steps** and explain precisely what is the problem with that behavior.
- **Explain which behavior you expected to see instead and why.**
- **Include screenshots and animated GIFs** which help you demonstrate the steps or the out-of-the-box behavior.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for Arohan, including completely new features and minor improvements to existing functionality.

- **Use a clear and descriptive title** for the issue to identify the suggestion.
- **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current behavior and explain which behavior you expected to see instead** and why.
- **Explain why this enhancement would be useful** to Arohan users.

### Pull Requests

- Fill in the required template (if provided).
- Do not include issue numbers in the PR title.
- Follow the [Style Guides](#style-guides).
- Include screenshots/recordings for UI changes.
- Ensure all tests pass.

## Development Setup

Please refer to the [README.md](README.md) for detailed instructions on setting up the frontend and backend environments.

Quick Checklist:

1. Clone the repo.
2. Install Node dependencies: `npm install`.
3. Set up Python virtual environment in `backend/` and install `requirements.txt`.
4. Configure `.env` with your API URLs.
5. Ensure Docker is running for Redis and PostgreSQL.

## Style Guides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature").
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...").
- Limit the first line to 72 characters or less.
- Reference issues and pull requests liberally after the first line.

### TypeScript Style Guide

- Use **PascalCase** for component names (e.g., `SOSButton.tsx`).
- Use **camelCase** for function and variable names.
- Use **interface** for defining object shapes unless you specifically need a **type**.
- Favor functional components and hooks over class components.
- Ensure all components are properly typed.

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide.
- Use **snake_case** for function and variable names.
- Use **PascalCase** for class names.
- Provide type hints for all function arguments and return types.
- Use Pydantic models for request and response validation.

## Project Structure

- `app/`: Expo Router screens and main application flow.
- `backend/`: FastAPI backend, AI services (Gemini), and OTP logic (Twilio).
- `components/`: Shared UI components used across the app.
- `constants/`: Theme configuration, colors, and global constants.
- `store/`: State management using Zustand.
- `services/`: API clients and external service integrations.

---

Thank you for contributing to Arohan! 💝
