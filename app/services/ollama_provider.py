import json

import os

import re



import requests





class OllamaProvider:

    """Fast local LLM provider for CatalogIQ enrichment."""



    def __init__(self) -> None:

        self.base_url = os.getenv(

            "OLLAMA_BASE_URL",

            "http://localhost:11434",

        ).rstrip("/")



        self.model = os.getenv(

            "OLLAMA_MODEL",

            "qwen3:4b",

        )



        self.timeout = int(

            os.getenv(

                "OLLAMA_TIMEOUT",

                "60",

            )

        )



    def generate(

        self,

        prompt: str,

        json_mode: bool = False,

    ) -> str:

        """Generate a response from the local Ollama model."""



        payload = {

            "model": self.model,

            "prompt": prompt,

            "stream": False,

            "think": False,

            "options": {

                "temperature": 0.1,

                "num_predict": 2500,

            },

        }



        # Force Ollama to return JSON when requested.

        if json_mode:

            payload["format"] = "json"



        response = requests.post(

            f"{self.base_url}/api/generate",

            json=payload,

            timeout=self.timeout,

        )



        response.raise_for_status()



        data = response.json()



        result = data.get(

            "response",

            "",

        ).strip()



        if not result:

            raise RuntimeError(

                "Ollama returned an empty response. "

                f"Model={self.model}"

            )



        if json_mode:

            return self._extract_json(result)



        return self._clean_response(result)



    def _clean_response(

        self,

        text: str,

    ) -> str:

        """Remove Qwen thinking markers from normal responses."""



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



        # -------------------------------------------------

        # Remove markdown code fences

        # -------------------------------------------------



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



        # -------------------------------------------------

        # First: try the entire response

        # -------------------------------------------------



        try:

            parsed = json.loads(text)



            return json.dumps(

                parsed,

                ensure_ascii=False,

            )



        except json.JSONDecodeError:

            pass



        # -------------------------------------------------

        # Second: find a JSON object

        # -------------------------------------------------



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



        # -------------------------------------------------

        # Third: find a JSON array

        # -------------------------------------------------



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



        # -------------------------------------------------

        # Nothing valid was found

        # -------------------------------------------------



        raise RuntimeError(

            "Ollama returned a response, but no valid JSON "

            f"could be extracted.\nResponse:\n{text}"

        ) 

