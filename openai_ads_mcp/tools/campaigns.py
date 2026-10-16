"""Campaign tools: read and write.

Read tools: list_campaigns, get_campaign.
Write tools: create_campaign, update_campaign, activate_campaign,
pause_campaign, archive_campaign.

Safety defaults:
- New campaigns are created with status "paused" unless explicitly set.
- A lifetime spend limit is required and must be at least 1 EUR
  (1,000,000 micros), matching the API minimum.
- archive_campaign is irreversible and is marked as destructive.

API reference: https://developers.openai.com/ads/api-reference/campaigns
"""

from typing import Any, Mapping, Optional

from mcp.types import ToolAnnotations

from openai_ads_mcp.client import request
from openai_ads_mcp.coordinator import mcp

_MIN_LIFETIME_SPEND_MICROS = 1_000_000  # 1 EUR, API minimum


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def list_campaigns(
    limit: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    order: Optional[str] = None,
) -> Any:
    """List campaigns in the current ad account (pagination + sort).

    See https://developers.openai.com/ads/api-reference/campaigns
    """
    return request(
        "GET",
        "/campaigns",
        params={
            "limit": limit,
            "after": after,
            "before": before,
            "order": order,
        },
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def get_campaign(campaign_id: str) -> Any:
    """Fetch one campaign by id."""
    return request("GET", f"/campaigns/{campaign_id}")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
def create_campaign(
    name: str,
    lifetime_spend_limit_micros: int,
    status: str = "paused",
    description: Optional[str] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    bidding_type: Optional[str] = None,
    conversion_event_setting_ids: Optional[list[str]] = None,
    targeting: Optional[Mapping[str, Any]] = None,
    mode: Optional[str] = None,
) -> Any:
    """Create a campaign in the current ad account.

    Defaults to status "paused" so nothing spends until it is activated.
    lifetime_spend_limit_micros is required: 1 EUR = 1000000 micros, minimum 1 EUR.
    bidding_type: impressions (default), clicks, or conversions.
    start_time / end_time: Unix timestamps (seconds).
    targeting example: {"locations": {"include": [{"id": "1000056"}]}}
    (1000056 = Germany).

    See https://developers.openai.com/ads/api-reference/campaigns
    """
    if status not in ("active", "paused"):
        raise ValueError("status must be 'active' or 'paused' on create.")
    if lifetime_spend_limit_micros < _MIN_LIFETIME_SPEND_MICROS:
        raise ValueError("lifetime_spend_limit_micros must be at least 1000000 (1 EUR).")
    if bidding_type == "conversions" and not conversion_event_setting_ids:
        raise ValueError("bidding_type 'conversions' requires conversion_event_setting_ids.")

    body = {
        "name": name,
        "status": status,
        "budget": {"lifetime_spend_limit_micros": lifetime_spend_limit_micros},
        "description": description,
        "start_time": start_time,
        "end_time": end_time,
        "bidding_type": bidding_type,
        "conversion_event_setting_ids": conversion_event_setting_ids,
        "targeting": dict(targeting) if targeting is not None else None,
        "mode": mode,
    }
    return request("POST", "/campaigns", json_body=body)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
def update_campaign(
    campaign_id: str,
    status: Optional[str] = None,
    description: Optional[str] = None,
    lifetime_spend_limit_micros: Optional[int] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    targeting: Optional[Mapping[str, Any]] = None,
) -> Any:
    """Update a campaign. Only the fields you pass are changed.

    status: active, paused, or archived (prefer the dedicated activate, pause,
    archive tools). bidding_type cannot be changed.
    lifetime_spend_limit_micros: sent as the full budget object; minimum 1000000.

    See https://developers.openai.com/ads/api-reference/campaigns
    """
    if status is not None and status not in ("active", "paused", "archived"):
        raise ValueError("status must be 'active', 'paused', or 'archived'.")
    if lifetime_spend_limit_micros is not None and lifetime_spend_limit_micros < _MIN_LIFETIME_SPEND_MICROS:
        raise ValueError("lifetime_spend_limit_micros must be at least 1000000 (1 EUR).")

    body = {
        "status": status,
        "description": description,
        "budget": (
            {"lifetime_spend_limit_micros": lifetime_spend_limit_micros}
            if lifetime_spend_limit_micros is not None
            else None
        ),
        "start_time": start_time,
        "end_time": end_time,
        "targeting": dict(targeting) if targeting is not None else None,
    }
    return request("POST", f"/campaigns/{campaign_id}", json_body=body)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
def activate_campaign(campaign_id: str) -> Any:
    """Activate a campaign so it starts delivering ads (spends budget).

    See https://developers.openai.com/ads/api-reference/campaigns
    """
    return request("POST", f"/campaigns/{campaign_id}/activate")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
def pause_campaign(campaign_id: str) -> Any:
    """Pause a campaign. Paused campaigns do not deliver ads.

    See https://developers.openai.com/ads/api-reference/campaigns
    """
    return request("POST", f"/campaigns/{campaign_id}/pause")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True))
def archive_campaign(campaign_id: str) -> Any:
    """Archive a campaign. This is NOT reversible. Only use when the campaign is no longer needed.

    See https://developers.openai.com/ads/api-reference/campaigns
    """
    return request("POST", f"/campaigns/{campaign_id}/archive")
