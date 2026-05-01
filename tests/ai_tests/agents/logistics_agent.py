"""
Placeholder for logistics-role simulation.

Stud does not expose logistics endpoints in this repository.
"""


class LogisticsAgentNotAvailable(RuntimeError):
    pass


async def logistics_reply_stub(*_args, **_kwargs) -> str:
    raise LogisticsAgentNotAvailable(
        "Logistics agent: no Stud endpoint — implement when logistics API is added."
    )
