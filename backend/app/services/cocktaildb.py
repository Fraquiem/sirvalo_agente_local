"""TheCocktailDB HTTP adapter and stable record normalizer."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from app.config import settings
from app.services.vectorstore import create_or_update_document, get_document_chunks, replace_chunks
from app.services.ingestion import embed_chunks, Chunk
BASE_URL = settings.THECOCKTAILDB_BASE_URL.rstrip("/")


def normalize_cocktail(raw_data: dict[str, Any]) -> dict[str, Any]:
    cocktail_id = str(raw_data.get("idDrink") or "").strip()
    name = str(raw_data.get("strDrink") or "").strip()
    ingredients = []
    for index in range(1, 16):
        ingredient = str(raw_data.get(f"strIngredient{index}") or "").strip()
        measure = str(raw_data.get(f"strMeasure{index}") or "").strip()
        if ingredient:
            ingredients.append({"name": ingredient, "measure": measure})
    source_uri = f"{BASE_URL}/lookup.php?i={quote(cocktail_id)}" if cocktail_id else None
    image_url = str(raw_data.get("strDrinkThumb") or "").strip() or None
    if image_url and not image_url.startswith("https://"):
        image_url = None
    return {"id": cocktail_id, "name": name, "category": str(raw_data.get("strCategory") or "").strip(), "glass": str(raw_data.get("strGlass") or "").strip(), "ingredients": ingredients, "instructions": str(raw_data.get("strInstructions") or "").strip(), "source_uri": source_uri, "image_url": image_url, "raw": raw_data}


async def fetch_cocktails(*, letters: list[str], limit: int) -> list[dict[str, Any]]:
    if limit < 1:
        return []
    letters = [letter.lower() for letter in letters if len(letter) == 1 and letter.isalpha()]
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    async with httpx.AsyncClient(timeout=settings.THECOCKTAILDB_TIMEOUT_SECONDS) as client:
        for letter in letters:
            listing = await client.get(f"{BASE_URL}/search.php", params={"f": letter})
            listing.raise_for_status()
            drinks = (listing.json() or {}).get("drinks") or []
            for item in drinks:
                cocktail_id = str(item.get("idDrink") or "")
                if not cocktail_id or cocktail_id in seen:
                    continue
                detail = await client.get(f"{BASE_URL}/lookup.php", params={"i": cocktail_id})
                detail.raise_for_status()
                records = (detail.json() or {}).get("drinks") or []
                if records:
                    results.append(normalize_cocktail(records[0]))
                    seen.add(cocktail_id)
                if len(results) >= limit:
                    return results
    return results


async def fetch_named_cocktail(candidate: str) -> dict[str, Any] | None:
    """Fetch one named cocktail using bounded search and detail requests."""
    candidate = candidate.strip()
    if not candidate:
        return None
    async with httpx.AsyncClient(timeout=settings.THECOCKTAILDB_TIMEOUT_SECONDS) as client:
        listing = await client.get(f"{BASE_URL}/search.php", params={"s": candidate})
        listing.raise_for_status()
        drinks = (listing.json() or {}).get("drinks") or []
        if not drinks:
            return None
        normalized_candidate = " ".join(candidate.casefold().split())
        selected = next(
            (
                item for item in drinks
                if " ".join(str(item.get("strDrink") or "").casefold().split()) == normalized_candidate
            ),
            drinks[0],
        )
        cocktail_id = str(selected.get("idDrink") or "").strip()
        if not cocktail_id:
            return None
        detail = await client.get(f"{BASE_URL}/lookup.php", params={"i": cocktail_id})
        detail.raise_for_status()
        records = (detail.json() or {}).get("drinks") or []
        return normalize_cocktail(records[0]) if records else None

async def fetch_cocktails_by_ingredient(ingredient: str, limit: int) -> list[dict[str, Any]]:
    """Fetch a bounded set of cocktails containing an ingredient.

    The provider's filter endpoint only returns summary records, so each
    distinct drink is followed by one bounded detail lookup before
    normalization.  Persistence is deliberately kept separate so callers can
    choose when to write the global provider document.
    """
    ingredient = " ".join(ingredient.split())
    limit = min(max(limit, 0), settings.THECOCKTAILDB_INGREDIENT_MAX_ITEMS)
    if not ingredient or not limit:
        return []
    async with httpx.AsyncClient(timeout=settings.THECOCKTAILDB_TIMEOUT_SECONDS) as client:
        listing = await client.get(f"{BASE_URL}/filter.php", params={"i": ingredient})
        listing.raise_for_status()
        drinks = (listing.json() or {}).get("drinks") or []
        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in drinks:
            cocktail_id = str(item.get("idDrink") or "").strip()
            if not cocktail_id or cocktail_id in seen:
                continue
            seen.add(cocktail_id)
            detail = await client.get(f"{BASE_URL}/lookup.php", params={"i": cocktail_id})
            detail.raise_for_status()
            records = (detail.json() or {}).get("drinks") or []
            if records:
                results.append(normalize_cocktail(records[0]))
            if len(results) >= limit:
                break
    return results



async def persist_cocktail(cocktail: dict[str, Any]) -> dict[str, Any]:
    """Upsert one provider record and replace its deterministic embedded chunk."""
    content = cocktail_text(cocktail)
    document = await create_or_update_document(
        owner_id=None,
        source_type="cocktaildb",
        source_uri=cocktail["source_uri"],
        external_id=cocktail["id"],
        filename=None,
        mime_type="application/json",
        size_bytes=None,
        title=cocktail["name"],
        checksum=None,
        metadata={
            "provider": "TheCocktailDB",
            "external_id": cocktail["id"],
            "category": cocktail["category"],
            "glass": cocktail["glass"],
            "image_url": cocktail["image_url"],
        },
    )
    embedding = await embed_chunks([Chunk(index=0, content=content, metadata={})])
    await replace_chunks(
        document["id"],
        [{
            "document_id": document["id"],
            "chunk_index": 0,
            "content": content,
            "embedding": embedding[0],
            "metadata": {
                "source_type": "cocktaildb",
                "source_uri": cocktail["source_uri"],
                "external_id": cocktail["id"],
                "title": cocktail["name"],
                "image_url": cocktail["image_url"],
            },
        }],
    )
    chunks = await get_document_chunks(document["id"])
    if not chunks:
        raise RuntimeError("Cocktail persistence returned no chunks")
    chunk = chunks[0]
    return {
        "document_id": document["id"],
        "chunk_id": chunk["id"],
        "content": chunk["content"],
        "metadata": chunk.get("metadata") or {},
        "similarity": 1.0,
    }


def cocktail_text(cocktail: dict[str, Any]) -> str:
    ingredients = ", ".join(f"{item['measure']} {item['name']}".strip() for item in cocktail["ingredients"])
    return f"Name: {cocktail['name']}\nCategory: {cocktail['category']}\nGlass: {cocktail['glass']}\nIngredients: {ingredients}\nInstructions: {cocktail['instructions']}\nSource: {cocktail['source_uri']}"


async def ingest_cocktails(*, letters: list[str], limit: int) -> int:
    cocktails = await fetch_cocktails(letters=letters, limit=min(limit, settings.THECOCKTAILDB_MAX_ITEMS))
    count = 0
    for cocktail in cocktails:
        await persist_cocktail(cocktail)
        count += 1
    return count
