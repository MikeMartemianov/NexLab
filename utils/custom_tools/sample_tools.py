from smart_agent_arch.tools_loader import export_tool

@export_tool
def calculate_sum(a: int, b: int) -> int:
    """
    Calculates the sum of two integers.
    :param a: The first number.
    :param b: The second number.
    """
    return a + b

@export_tool
def get_weather(city: str) -> str:
    """
    Simulates getting the weather for a city.
    :param city: The name of the city.
    """
    return f"The weather in {city} is sunny and 25°C."
