"""Bright Data Amazon dataset integration using the existing dataset configuration."""

import logging
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

# Resolve this explicitly so the service reads backend/.env regardless of the
# directory from which Uvicorn or the tests are launched.
BACKEND_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
# This module can be imported by Uvicorn, pytest, or a command started from the
# repository root.  Always load *backend/.env* rather than relying on cwd.
load_dotenv(BACKEND_ENV_FILE)

logger = logging.getLogger(__name__)
BRIGHTDATA_SCRAPE_URL = "https://api.brightdata.com/datasets/v3/scrape"
AMAZON_DATASET_ID = "gd_l7q7dkf244hwjntr0"
AMAZON_SEARCH_DATASET_ID = "gd_lwdb4vjm1ehb499uxs"
AMAZON_REVIEWS_DATASET_ID = "gd_le8e811kzy4ggddlq"
# Verified from the configured Bright Data account's dataset list.  The
# discovery dataset turns a user query into live product URLs; the unified
# schema dataset then supplies the authoritative product fields for those URLs.
FLIPKART_PRODUCTS_DATASET_ID = "gd_mljhtaoe2n284ux79e"
FLIPKART_SEARCH_DATASET_ID = "gd_mj85tmhylhmbazp6h"
MYNTRA_PRODUCTS_DATASET_ID = "gd_lptvxr8b1qx1d9thgp"
REQUEST_TIMEOUT_SECONDS = 45
POLL_INTERVAL_SECONDS = 2


class BrightDataServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _first_value(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


def _first_non_empty_list(item: dict[str, Any], *keys: str) -> list[Any]:
    for key in keys:
        value = item.get(key)
        if isinstance(value, list) and value:
            return value
    return []


def _as_number(value: Any) -> float | None:
    if isinstance(value, dict):
        value = _first_value(value, "amount", "value", "price", "current_price")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        # Use the first numeric token.  Removing all non-digits turns strings
        # like "4.7 out of 5 stars" into the incorrect value 4.75.
        match = re.search(r"\d[\d,]*(?:\.\d+)?", value)
        cleaned = match.group(0).replace(",", "") if match else ""
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None
    return None


def _is_valid_image_url(url: Any) -> bool:
    if not url or not isinstance(url, str):
        return False
    cleaned = url.strip()
    if cleaned.startswith("//"):
        cleaned = "https:" + cleaned
    if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
        return False
    lower = cleaned.lower()
    unwanted = (
        "transparent-pixel", "grey-pixel", "1x1", "pixel.gif",
        "prime-logo", "nav-sprite", "amazon-logo", "flipkart-logo",
        "/badge/", "/badges/", "/icons/", "/icon-", "avatar", "no-image",
        "placeholder", "spacer.gif", "beacon", "load_indicator", "source_icon"
    )
    if any(u in lower for u in unwanted):
        return False

    if lower.endswith((".html", ".htm", ".php", ".asp", ".aspx")):
        return False
    if any(sp in lower for sp in ("/search?", "/search/", "google.com/search", "duckduckgo.com", "bing.com")):
        if "gstatic.com" not in lower and "googleusercontent.com" not in lower:
            return False

    image_extensions = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".svg", ".bmp")
    has_ext = any(lower.split("?")[0].endswith(ext) for ext in image_extensions)
    is_known_image_host = any(h in lower for h in (
        "media-amazon", "ssl-images-amazon", "images-amazon", "flixcart.com/image",
        "rukminim", "myntassets", "gstatic.com", "googleusercontent", "serpapi.com/images",
        "cloudinary", "imgix", "photobucket", "/images/", "/image/", "/img/", "/photos/", "/photo/"
    ))

    if any(store in lower for store in ("amazon.in", "amazon.com", "flipkart.com", "myntra.com", "croma.com")):
        if not has_ext and not is_known_image_host:
            return False

    return True


def _clean_image_url(url: str) -> str:
    if not isinstance(url, str):
        return ""
    cleaned = url.strip()
    if cleaned.startswith("//"):
        cleaned = "https:" + cleaned
    return cleaned


def _extract_images(item: dict[str, Any]) -> list[str]:
    results: list[str] = []

    def _walk(val: Any):
        if val is None or val == "":
            return
        if isinstance(val, str):
            if _is_valid_image_url(val):
                results.append(_clean_image_url(val))
        elif isinstance(val, list):
            for elem in val:
                _walk(elem)
        elif isinstance(val, dict):
            preferred_keys = ["url", "link", "src", "image_url", "image", "hires", "hi_res", "large", "main", "primary", "thumbnail"]
            for pk in preferred_keys:
                if pk in val and val[pk]:
                    _walk(val[pk])
            for k, v in val.items():
                if k not in preferred_keys:
                    _walk(v)

    image_keys = [
        "image_url", "image", "main_image", "primary_image", "thumbnail",
        "image_link", "image_urls", "additional_image_urls", "images",
        "additional_images", "product_images"
    ]
    for key in image_keys:
        if key in item and item[key]:
            _walk(item[key])

    seen = set()
    deduped: list[str] = []
    for u in results:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


def _extract_prices(item: dict[str, Any]) -> tuple[float | None, float | None, float | None]:
    current = None
    for key in ["final_price", "sale_price", "current_price", "price_value", "deal_price", "offer_price"]:
        if key in item and item[key] is not None:
            current = _as_number(item[key])
            if current is not None:
                break

    original = None
    for key in ["initial_price", "original_price", "list_price", "was_price", "mrp", "regular_price"]:
        if key in item and item[key] is not None:
            original = _as_number(item[key])
            if original is not None:
                break

    price_val = _as_number(item.get("price"))
    if current is None:
        current = price_val
    elif original is None and price_val is not None and price_val > current:
        original = price_val

    if original is not None and current is not None and original <= current:
        original = None

    discount = None
    if current and original and original > current:
        discount = round(((original - current) / original) * 100, 1)
    elif item.get("discount") is not None or item.get("discount_percent") is not None:
        d_val = _as_number(item.get("discount") or item.get("discount_percent"))
        if d_val and 0 < d_val < 100:
            discount = round(d_val, 1)

    return current, original, discount


def _normalise_product(item: dict[str, Any], index: int) -> dict[str, Any]:
    product_url = _first_value(item, "url", "product_url", "product_page_url", "canonical_url")
    asin = _first_value(item, "asin", "product_id", "id", "parent_asin")
    review_count = _as_number(_first_value(
        item, "review_count", "reviews_count", "num_reviews", "number_of_reviews", "rating_count", "num_ratings"
    ))
    candidates = _extract_images(item)
    if asin:
        asin_clean = str(asin).strip()
        if re.match(r'^[A-Z0-9]{10}$', asin_clean):
            asin_img = f"https://images-na.ssl-images-amazon.com/images/P/{asin_clean}.01._SX400_.jpg"
            if asin_img not in candidates:
                candidates.append(asin_img)
    image_url = candidates[0] if candidates else None
    current_price, original_price, discount = _extract_prices(item)
    normalized = {
        "id": str(asin or product_url or f"brightdata-{index}"),
        "source_product_id": str(asin) if asin else None,
        "asin": str(asin) if asin else None,
        "title": _first_value(item, "title", "name", "product_name", "product_title") or "",
        "product_url": product_url,
        "image_url": image_url,
        "image_candidates": candidates,
        "current_price": current_price,
        "original_price": original_price,
        "discount_percent": discount,
        "discount": discount,
        "currency": "INR",
        "rating": _as_number(_first_value(item, "rating", "stars", "rating_value", "product_rating")),
        "review_count": int(review_count) if review_count is not None else None,
        "availability": _first_value(item, "availability", "stock_status") or "In Stock",
        "seller": _first_value(item, "seller", "seller_name", "sold_by"),
        "brand": _first_value(item, "brand", "manufacturer", "brand_name") or "",
        "marketplace": "Amazon",
        "provider": "Bright Data",
        "source": "amazon",
        "description": _first_value(item, "description", "product_description"),
        "features": _first_value(item, "features", "bullet_points", "bullets", "feature_bullets") or [],
        "categories": _first_value(item, "categories", "category", "breadcrumbs") or [],
    }
    # Keep concise aliases for API clients that use Bright Data's field names.
    normalized.update({
        "price": normalized["current_price"],
        "reviews_count": normalized["review_count"],
        "image": normalized["image_url"],
        "images": candidates,
        "url": normalized["product_url"],
    })
    if not isinstance(normalized["features"], list):
        normalized["features"] = [str(normalized["features"])]
    if not isinstance(normalized["categories"], list):
        normalized["categories"] = [str(normalized["categories"])]
    return normalized


def _extract_items(payload: Any, source_name: str = "Amazon") -> list[dict[str, Any]]:
    """Accept the documented response plus common dataset response wrappers."""
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        # /datasets/v3/scrape normally returns a JSON array.  Keep these
        # wrappers for dashboard/API response variants without mistaking an
        # error object for a product.
        items = _first_value(payload, "data", "results", "items", "products")
    else:
        raise BrightDataServiceError(f"{source_name} scraping service returned an invalid response.")

    if not isinstance(items, list):
        raise BrightDataServiceError(f"{source_name} scraping service returned an unexpected response.")
    if not items:
        raise BrightDataServiceError(f"Bright Data did not return products for this {source_name} search.", 502)
    if not all(isinstance(item, dict) for item in items):
        raise BrightDataServiceError(f"{source_name} scraping service returned malformed product data.")
    return items


def _json_response(response: requests.Response, url: str, source_name: str = "Amazon") -> Any:
    try:
        return response.json()
    except ValueError as exc:
        logger.warning("Bright Data returned non-JSON data for %s request=%r", source_name, url)
        raise BrightDataServiceError(f"{source_name} scraping service returned an invalid response.") from exc


def _http_error_message(exc: requests.HTTPError) -> tuple[str, int]:
    """Translate Bright Data failures without leaking credentials or response bodies."""
    response = exc.response
    status = response.status_code if response is not None else 502
    messages = {
        400: "Bright Data rejected the Amazon product URL.",
        401: "Bright Data authentication failed. Check the server API key.",
        403: "Bright Data access was denied for this dataset.",
        404: "Bright Data dataset or product was not found.",
        408: "Amazon scraping timed out. Please try again.",
        429: "Bright Data rate limit reached. Please try again shortly.",
    }
    if status in messages:
        return messages[status], status
    logger.warning("Bright Data returned HTTP %s", status)
    return "Amazon scraping service is unavailable. Please try again.", 502


def _download_snapshot(
    snapshot_id: str,
    headers: dict[str, str],
    url: str,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    source_name: str = "Amazon",
) -> Any:
    """Wait briefly for an over-one-minute synchronous scrape, then download it."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            progress = requests.get(
                f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}",
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            progress.raise_for_status()
            status = _json_response(progress, url, source_name)
        except requests.Timeout as exc:
            raise BrightDataServiceError(f"{source_name} scraping timed out. Please try again.", 504) from exc
        except requests.RequestException as exc:
            raise BrightDataServiceError(f"{source_name} scraping service is unavailable. Please try again.") from exc

        if isinstance(status, dict) and str(status.get("status", "")).lower() in {"ready", "completed", "done"}:
            try:
                result = requests.get(
                    f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}",
                    params={"format": "json"},
                    headers=headers,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                result.raise_for_status()
                return _json_response(result, url, source_name)
            except requests.Timeout as exc:
                raise BrightDataServiceError(f"{source_name} scraping timed out. Please try again.", 504) from exc
            except requests.RequestException as exc:
                raise BrightDataServiceError(f"{source_name} scraping service is unavailable. Please try again.") from exc
        time.sleep(POLL_INTERVAL_SECONDS)
    raise BrightDataServiceError(f"{source_name} scraping timed out. Please try again.", 504)


def _scrape_records(dataset_id: str, input_payload: Any, url_for_logs: str) -> list[dict[str, Any]]:
    api_key = os.getenv("BRIGHTDATA_API_KEY", "").strip()
    if not api_key or api_key == "YOUR_BRIGHT_DATA_API_KEY":
        raise BrightDataServiceError("Bright Data is not configured on the server.", 503)

    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.post(
            BRIGHTDATA_SCRAPE_URL,
            params={"dataset_id": dataset_id, "format": "json"},
            headers=headers,
            # The Amazon Products scraper accepts a JSON array of URL input
            # records. The API key stays server-side in the Authorization
            # header and is never sent to the browser.
            json=input_payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        logger.warning("Bright Data request timed out for input=%r", url_for_logs)
        raise BrightDataServiceError("Amazon scraping timed out. Please try again.", 504) from exc
    except requests.HTTPError as exc:
        message, status = _http_error_message(exc)
        raise BrightDataServiceError(message, status) from exc
    except requests.RequestException as exc:
        logger.warning("Bright Data request failed for input=%r: %s", url_for_logs, type(exc).__name__)
        raise BrightDataServiceError("Amazon scraping service is unavailable. Please try again.") from exc

    payload = _json_response(response, url_for_logs)
    # The configured /scrape endpoint is synchronous and returns a list.  The
    # fallback keeps compatibility with an older asynchronous response shape.
    snapshot_id = payload.get("snapshot_id") if isinstance(payload, dict) else None
    if snapshot_id:
        payload = _download_snapshot(str(snapshot_id), headers, url_for_logs)
    items = _extract_items(payload)

    return items


def _scrape(dataset_id: str, input_payload: Any, url_for_logs: str) -> list[dict[str, Any]]:
    """Amazon compatibility wrapper returning the project's legacy aliases."""
    items = _scrape_records(dataset_id, input_payload, url_for_logs)
    products = [_normalise_product(item, index) for index, item in enumerate(items)]
    logger.info("Bright Data Amazon scrape completed: input=%r products=%d", url_for_logs, len(products))
    return products


def scrape_amazon(url: str) -> list[dict[str, Any]]:
    """Collect one known Amazon product URL with the Products dataset."""
    return _scrape(AMAZON_DATASET_ID, [{"url": url}], url)


def search_amazon(query: str, pages_to_search: int = 1) -> list[dict[str, Any]]:
    """Discover real Amazon India listings for a normal keyword query."""
    query = query.strip()
    if not query:
        return []
    payload = {
        "input": [{
            "keyword": query,
            "url": "https://www.amazon.in",
            "pages_to_search": max(1, min(pages_to_search, 2)),
        }]
    }
    return _scrape(AMAZON_SEARCH_DATASET_ID, payload, query)


def search_flipkart_records(query: str) -> list[dict[str, Any]]:
    """Discover live Flipkart product records for a user search query."""
    query = query.strip()
    if not query:
        return []
    search_url = f"https://www.flipkart.com/search?{urlencode({'q': query})}"
    return _scrape_records(
        FLIPKART_SEARCH_DATASET_ID,
        [{"url": search_url, "page": 1}],
        query,
    )


def search_flipkart_product_urls(query: str) -> list[str]:
    """Discover live Flipkart product URLs for a user search query."""
    query = query.strip()
    if not query:
        return []
    search_url = f"https://www.flipkart.com/search?{urlencode({'q': query})}"
    records = _scrape_records(
        FLIPKART_SEARCH_DATASET_ID,
        [{"url": search_url, "page": 1}],
        query,
    )
    return [record["url"] for record in records if isinstance(record.get("url"), str)]


def fetch_flipkart_products(product_urls: list[str]) -> list[dict[str, Any]]:
    """Fetch real product details through Flipkart Products unified schema."""
    inputs = [{"url": url, "all_variations": False} for url in product_urls if url]
    if not inputs:
        return []
    return _scrape_records(FLIPKART_PRODUCTS_DATASET_ID, inputs, "Flipkart product URLs")


def _scrape_myntra_pdp(url: str) -> dict[str, Any] | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        import json
        from json import JSONDecoder
        decoder = JSONDecoder()
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            scripts = re.findall(r"<script[^>]*>(.*?)</script>", resp.text, re.DOTALL)
            for s in scripts:
                if "window.__myx" in s and "{" in s:
                    idx = s.find("{")
                    if idx != -1:
                        try:
                            data, _ = decoder.raw_decode(s[idx:])
                            pdp = data.get("pdpData")
                            if isinstance(pdp, dict):
                                pdp["url"] = url
                                return pdp
                        except Exception:
                            pass
    except Exception as e:
        logger.debug("Live Myntra PDP fallback failed for %s: %s", url, e)
    return None


def fetch_myntra_products(product_urls: list[str]) -> list[dict[str, Any]]:
    """Fetch real product details through Bright Data Myntra products dataset."""
    inputs = [{"url": url} for url in product_urls if url]
    if not inputs:
        return []
    api_key = os.getenv("BRIGHTDATA_API_KEY", "").strip()
    if not api_key or api_key == "YOUR_BRIGHT_DATA_API_KEY":
        raise BrightDataServiceError("Bright Data is not configured on the server.", 503)

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        trigger_url = f"https://api.brightdata.com/datasets/v3/trigger?dataset_id={MYNTRA_PRODUCTS_DATASET_ID}&format=json&uncompressed_webhook=true"
        resp = requests.post(trigger_url, headers=headers, json=inputs, timeout=15)
        logger.info("Bright Data Myntra trigger status=%s input_records=%d", resp.status_code, len(inputs))
        resp.raise_for_status()
        res_data = resp.json()
        snapshot_id = res_data.get("snapshot_id")
        if snapshot_id:
            payload = _download_snapshot(
                str(snapshot_id),
                headers,
                "Myntra product URLs",
                source_name="Myntra",
            )
            records = _extract_items(payload, source_name="Myntra")
            logger.info("Bright Data Myntra snapshot ready snapshot_id=%s raw_records=%d", snapshot_id, len(records))
            return records
        raise BrightDataServiceError("Bright Data Myntra did not return a snapshot ID.")
    except BrightDataServiceError:
        raise
    except requests.Timeout as exc:
        logger.warning("Bright Data Myntra trigger timed out; falling back to direct PDP fetch")
        records = []
        for url in product_urls:
            pdp = _scrape_myntra_pdp(url)
            if pdp:
                records.append(pdp)
        if records:
            return records
        raise BrightDataServiceError("Bright Data Myntra request timed out.", 504) from exc
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        logger.warning("Bright Data Myntra trigger returned HTTP status=%s; falling back to direct PDP fetch", status_code)
        records = []
        for url in product_urls:
            pdp = _scrape_myntra_pdp(url)
            if pdp:
                records.append(pdp)
        if records:
            return records
        raise BrightDataServiceError("Bright Data Myntra request failed.", 502) from exc
    except requests.RequestException as exc:
        logger.warning("Bright Data Myntra request failed error_type=%s", type(exc).__name__)
        raise BrightDataServiceError("Bright Data Myntra request failed.", 502) from exc
    except (ValueError, KeyError) as exc:
        logger.warning("Bright Data Myntra returned malformed trigger response")
        raise BrightDataServiceError("Bright Data Myntra returned a malformed response.", 502) from exc


_AMAZON_REVIEWS_CACHE: dict[str, dict[str, Any]] = {}


def fetch_amazon_reviews(urls_or_asins: list[str]) -> dict[str, dict[str, Any]]:
    """
    Fetch authentic written customer reviews from Amazon India using Bright Data
    Amazon Reviews dataset (gd_le8e811kzy4ggddlq).
    Returns mapping: {asin_or_url: {"reviews": list[dict], "product_rating_object": dict, "product_rating_count": int}}
    """
    api_key = os.getenv("BRIGHTDATA_API_KEY", "").strip()
    if not api_key or api_key == "YOUR_BRIGHT_DATA_API_KEY":
        logger.warning("Bright Data API key not configured; skipping Amazon reviews retrieval.")
        return {}

    results: dict[str, dict[str, Any]] = {}
    pending_urls: list[str] = []
    asin_to_key: dict[str, str] = {}

    for item in urls_or_asins:
        if not item:
            continue
        asin_match = re.search(r"(?:/dp/|/gp/product/)?([A-Z0-9]{10})(?:[/?]|$)", str(item))
        asin = asin_match.group(1) if asin_match else str(item).strip()
        canonical_url = f"https://www.amazon.in/dp/{asin}"

        # Check cache
        if asin in _AMAZON_REVIEWS_CACHE:
            results[item] = _AMAZON_REVIEWS_CACHE[asin]
            results[asin] = _AMAZON_REVIEWS_CACHE[asin]
            continue
        if canonical_url in _AMAZON_REVIEWS_CACHE:
            results[item] = _AMAZON_REVIEWS_CACHE[canonical_url]
            results[asin] = _AMAZON_REVIEWS_CACHE[canonical_url]
            continue

        pending_urls.append(canonical_url)
        asin_to_key[asin] = item
        asin_to_key[canonical_url] = item

    if not pending_urls:
        return results

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    trigger_url = f"https://api.brightdata.com/datasets/v3/trigger?dataset_id={AMAZON_REVIEWS_DATASET_ID}&include_errors=true"
    payload = [{"url": u} for u in pending_urls]

    try:
        resp = requests.post(trigger_url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        snapshot_id = data.get("snapshot_id")
        if not snapshot_id:
            logger.warning("Bright Data did not return snapshot_id for reviews trigger")
            return results

        records_payload = _download_snapshot(str(snapshot_id), headers, "Amazon Reviews", timeout_seconds=80)
        records = _extract_items(records_payload) if records_payload else []
    except Exception as exc:
        logger.warning("Failed to fetch Amazon reviews from Bright Data: %s", exc)
        return results

    # Group and deduplicate reviews
    grouped: dict[str, list[dict[str, Any]]] = {}
    rating_objects: dict[str, dict[str, Any]] = {}
    rating_counts: dict[str, int] = {}
    seen_review_ids: set[str] = set()

    for rec in records:
        if not isinstance(rec, dict) or rec.get("error"):
            continue
        asin = rec.get("asin") or rec.get("variant_asin")
        text = rec.get("review_text") or rec.get("text") or rec.get("body")
        if not text:
            continue

        review_id = rec.get("review_id") or rec.get("id") or f"{rec.get('author_name')}_{hash(text)}"
        if review_id in seen_review_ids:
            continue
        seen_review_ids.add(review_id)

        clean_review = {
            "id": str(review_id),
            "asin": str(asin) if asin else None,
            "marketplace": "Amazon India",
            "rating": _as_number(rec.get("rating")),
            "title": rec.get("review_header") or rec.get("title") or "",
            "review_text": str(text).strip(),
            "reviewer_name": rec.get("author_name") or rec.get("author"),
            "review_date": rec.get("review_posted_date") or rec.get("date"),
            "verified_purchase": bool(rec.get("is_verified")),
            "source_url": rec.get("url") or f"https://www.amazon.in/dp/{asin}" if asin else None,
            "helpful_count": _as_number(rec.get("helpful_count")),
        }

        key = asin or rec.get("url")
        if key:
            grouped.setdefault(key, []).append(clean_review)
            if rec.get("product_rating_object") and key not in rating_objects:
                rating_objects[key] = rec.get("product_rating_object")
            if rec.get("product_rating_count") and key not in rating_counts:
                rating_counts[key] = int(rec.get("product_rating_count"))

    # Populate cache and results
    for key, rev_list in grouped.items():
        entry = {
            "reviews": rev_list,
            "product_rating_object": rating_objects.get(key, {}),
            "product_rating_count": rating_counts.get(key, len(rev_list)),
        }
        _AMAZON_REVIEWS_CACHE[key] = entry
        results[key] = entry
        original_key = asin_to_key.get(key)
        if original_key:
            results[original_key] = entry

    logger.info("Successfully fetched %d Amazon reviews across %d products", len(seen_review_ids), len(grouped))
    return results

