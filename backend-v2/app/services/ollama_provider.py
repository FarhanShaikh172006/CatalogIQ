import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()


class OllamaProvider:
    """Ollama Cloud LLM provider for CatalogIQ enrichment."""

    def __init__(self) -> None:
        self.base_url = os.getenv(
            "OLLAMA_BASE_URL",
            "https://ollama.com",
        ).rstrip("/")

        self.api_key = os.getenv("OLLAMA_API_KEY")

        self.model = os.getenv(
            "OLLAMA_MODEL",
            "gpt-oss:20b",
        )

        self.timeout = int(
            os.getenv(
                "OLLAMA_TIMEOUT",
                "120",
            )
        )

        if not self.api_key:
            raise RuntimeError(
                "OLLAMA_API_KEY environment variable is not configured."
            )

    def generate(
        self,
        prompt: str,
        json_mode: bool = False,
    ) -> str:
        """Generate a response using Ollama Cloud."""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 2500,
            },
        }

        if json_mode:
            payload["format"] = "json"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except requests.RequestException as exc:
            raise RuntimeError(
                "Ollama Cloud request failed. "
                f"Model={self.model}, "
                f"URL={self.base_url}/api/chat, "
                f"Error={exc}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Ollama Cloud returned invalid JSON. "
                f"HTTP={response.status_code}, "
                f"Response={response.text[:1000]}"
            ) from exc

        # ---------------------------------------------------------
        # Ollama Cloud /api/chat response
        #
        # {
        #     "message": {
        #         "role": "assistant",
        #         "content": "..."
        #     }
        # }
        # ---------------------------------------------------------

        message = data.get("message")

        if not isinstance(message, dict):
            raise RuntimeError(
                "Ollama Cloud returned no valid message object. "
                f"Model={self.model}. "
                f"Response={data}"
            )

        result = message.get("content", "")

        if not isinstance(result, str):
            result = str(result)

        result = result.strip()

        if not result:
            raise RuntimeError(
                "Ollama Cloud returned an empty response. "
                f"Model={self.model}. "
                f"Response={data}"
            )

        # ---------------------------------------------------------
        # JSON mode
        # ---------------------------------------------------------

        if json_mode:
            return self._extract_json(result)

        # ---------------------------------------------------------
        # Normal text response
        # ---------------------------------------------------------

        return self._clean_response(result)

    def _clean_response(
        self,
        text: str,
    ) -> str:
        """Remove model thinking markers from normal responses."""

        # Remove content before </think>
        if "</think>" in text:
            text = text.split(
                "</think>",
                1,
            )[1]

        # Remove any remaining <think> marker
        if "<think>" in text:
            text = text.split(
                "<think>",
                1,
            )[0]

        return text.strip()

    def _extract_json(
        self,
        text: str,
    ) -> str:
        """Extract and validate JSON from an LLM response."""

        text = self._clean_response(text)

        # ---------------------------------------------------------
        # Remove markdown code fences
        # ---------------------------------------------------------

        text = re.sub(
            r"```(?:json)?",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = text.replace(
            "```",
            "",
        ).strip()

        # ---------------------------------------------------------
        # Try entire response first
        # ---------------------------------------------------------

        try:
            parsed = json.loads(text)

            return json.dumps(
                parsed,
                ensure_ascii=False,
            )

        except json.JSONDecodeError:
            pass

        # ---------------------------------------------------------
        # Find JSON object
        # ---------------------------------------------------------

        start = text.find("{")
        end = text.rfind("}")

        if (
            start != -1
            and end != -1
            and end > start
        ):
            candidate = text[
                start : end + 1
            ]

            try:
                parsed = json.loads(candidate)

                return json.dumps(
                    parsed,
                    ensure_ascii=False,
                )

            except json.JSONDecodeError:
                pass

        # ---------------------------------------------------------
        # Find JSON array
        # ---------------------------------------------------------

        start = text.find("[")
        end = text.rfind("]")

        if (
            start != -1
            and end != -1
            and end > start
        ):
            candidate = text[
                start : end + 1
            ]

            try:
                parsed = json.loads(candidate)

                return json.dumps(
                    parsed,
                    ensure_ascii=False,
                )

            except json.JSONDecodeError:
                pass

        # ---------------------------------------------------------
        # No valid JSON found
        # ---------------------------------------------------------

        raise RuntimeError(
            "Ollama returned a response, but no valid JSON "
            f"could be extracted.\nResponse:\n{text}"
        )