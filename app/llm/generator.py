import os

from groq import Groq

from dotenv import load_dotenv


load_dotenv()


class LLMGenerator:
    def __init__(self):
        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found in environment variables"
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model = (
            "llama-3.1-8b-instant"
        )

    def generate_response(
        self,
        prompt: str,
    ):
        try:
            trimmed_prompt = (
                prompt[:12000]
            )

            response = (
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a senior full-stack engineer and product designer "
                                "specialized in codebase analysis. "
                                "Be accurate and grounded in the provided repository context.\n\n"
                                "Output MUST be clean, scannable Markdown with these sections:\n"
                                "## Overview\n"
                                "## Issue\n"
                                "## Explanation\n"
                                "## Solution\n\n"
                                "Use short paragraphs and bullet points. "
                                "Avoid rambling, avoid filler, and do not invent details."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                trimmed_prompt
                            ),
                        },
                    ],
                    temperature=0.2,
                    max_tokens=1200,
                )
            )

            if not hasattr(
                response,
                "choices",
            ):
                raise Exception(
                    f"Invalid Groq response: {response}"
                )

            if (
                not response.choices
                or len(
                    response.choices
                )
                == 0
            ):
                raise Exception(
                    "No choices returned from Groq"
                )

            first_choice = (
                response.choices[0]
            )

            if not hasattr(
                first_choice,
                "message",
            ):
                raise Exception(
                    "No message returned from Groq"
                )

            message = (
                first_choice.message
            )

            if not hasattr(
                message,
                "content",
            ):
                raise Exception(
                    "No content returned from Groq"
                )

            content = (
                message.content
            )

            if (
                not content
                or not content.strip()
            ):
                raise Exception(
                    "Empty response returned from Groq"
                )

            return content.strip()

        except Exception as error:
            raise Exception(
                f"Groq generation failed: {error}"
            )