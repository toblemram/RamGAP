# -*- coding: utf-8 -*-
"""
AI Assistant Service
====================
Business logic for the AI assistant: building prompts, calling the LLM,
and executing or validating generated Plaxis code.
"""


class AIAssistantService:
    """Coordinates LLM calls and optional code execution against Plaxis."""

    def generate_code(self, user_prompt: str, context_docs: list) -> str:
        """
        Call the LLM with a system prompt and retrieved context documents
        and return the generated Plaxis Python code.

        Args:
            user_prompt:   Raw message from the user.
            context_docs:  Relevant Plaxis API doc snippets from the knowledge base.

        Returns:
            A string containing pure Python code (no markdown).
        """
        # TODO: implement using config.OPENAI_MODEL and prompts.plaxis_code
        raise NotImplementedError
