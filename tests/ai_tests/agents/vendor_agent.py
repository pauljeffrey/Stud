"""
Placeholder for vendor-role simulation.

Stud does not expose a vendor commerce API in this repository.
When a vendor HTTP API exists, this module can call it or generate vendor-side messages via LLM.
"""


class VendorAgentNotAvailable(RuntimeError):
    pass


async def vendor_reply_stub(*_args, **_kwargs) -> str:
    raise VendorAgentNotAvailable(
        "Vendor agent: no Stud endpoint — implement when commerce API is added."
    )
