import requests
from typing import Optional, Dict
from agno.tools import Toolkit


class ExternalAgentToolkit(Toolkit):
    def __init__(
        self,
        name: str = "Toolkit for Crew-AI Agent",
        endpoint_url: str = "http://127.0.0.1:5000/run-agent",
        input_key: str = "prompt",
        result_key: str = "result",
        timeout: int = 15,
        **kwargs
    ):
        """
        A generic toolkit to onboard any external agent via HTTP API.

        Args:
            name (str): Toolkit name.
            endpoint_url (str): The URL to the external agent's API endpoint.
            input_key (str): The key expected by the external agent in the request body. Default is 'prompt'.
            result_key (str): The key containing the result in the response. Default is 'result'.
            timeout (int): Timeout in seconds for the API call.
        """
        self.endpoint_url = endpoint_url
        self.input_key = input_key
        self.result_key = result_key
        self.timeout = timeout

        super().__init__(
            name=name,
            tools=[self.invoke_external_agent],
            **kwargs
        )

    def invoke_external_agent(self, input_text: str, extra_data: Optional[Dict] = None) -> str:
        """
        Invokes the external agent by posting input_text to its API.

        Args:
            input_text (str): The prompt or instruction to send.
            extra_data (dict): Optional additional fields to send in the payload.

        Returns:
            str: The response result from the external agent.
        """
        try:
            payload = {self.input_key: input_text}
            if extra_data:
                payload.update(extra_data)

            response = requests.post(
                self.endpoint_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            response_data = response.json()
            return response_data.get(self.result_key, "No result returned from agent.")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to invoke external agent at {self.endpoint_url}: {str(e)}")
