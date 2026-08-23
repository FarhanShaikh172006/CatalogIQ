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
                "180",
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
            "Accept": "application/json",
        }

        url = f"{self.base_url}/api/chat"

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

        except requests.Timeout as exc:
            raise RuntimeError(
                "Ollama Cloud request timed out. "
                f"Model={self.model}, "
                f"Timeout={self.timeout}s"
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                "Ollama Cloud request failed. "
                f"Model={self.model}, "
                f"URL={url}, "
                f"Error={exc}"
            ) from exc

        # ---------------------------------------------------------
        # HTTP error
        # ---------------------------------------------------------

        if not response.ok:
            raise RuntimeError(
                "Ollama Cloud returned an HTTP error. "
                f"HTTP={response.status_code}, "
                f"Model={self.model}, "
                f"Response={response.text[:2000]}"
            )

        # ---------------------------------------------------------
        # Parse JSON
        # ---------------------------------------------------------

        try:
            data = response.json()

        except ValueError as exc:
            raise RuntimeError(
                "Ollama Cloud returned invalid JSON. "
                f"HTTP={response.status_code}, "
                f"Model={self.model}, "
                f"Response={response.text[:2000]}"
            ) from exc

        # ---------------------------------------------------------
        # Extract assistant message
        # ---------------------------------------------------------

        message = data.get("message")

        if not isinstance(message, dict):
            raise RuntimeError(
                "Ollama Cloud returned no valid message object. "
                f"Model={self.model}. "
                f"Response={json.dumps(data)[:3000]}"
            )

        result = message.get("content", "")

        if not isinstance(result, str):
            result = str(result)

        result = result.strip()

        # ---------------------------------------------------------
        # Some Ollama models may return useful content in thinking.
        # Use it only if content itself is empty.
        # ---------------------------------------------------------

        if not result:
            thinking = message.get("thinking", "")

            if isinstance(thinking, str):
                thinking = thinking.strip()

                if thinking:
                    result = thinking

        if not result:
            raise RuntimeError(
                "Ollama Cloud returned an empty response. "
                f"Model={self.model}. "
                f"Full response={json.dumps(data)[:5000]}"
            )

        # ---------------------------------------------------------
        # JSON mode
        # ---------------------------------------------------------

        if json_mode:
            return self._extract_json(result)

        # ---------------------------------------------------------
        # Normal response
        # ---------------------------------------------------------

        return self._clean_response(result)

    def _clean_response(
        self,
        text: str,
    ) -> str:
        """Remove model thinking markers."""

        text = text.strip()

        if "</think>" in text:
            text = text.split(
                "</think>",
                1,
            )[1]

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
        # First: entire response
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
        # Second: JSON object
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
        # Third: JSON array
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

        raise RuntimeError(
            "Ollama returned a response, but no valid JSON "
            f"could be extracted.\nResponse:\n{text[:5000]}"
        )