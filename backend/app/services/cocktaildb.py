"""TheCocktailDB HTTP adapter and stable record normalizer."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from app.config import settings
from app.services.vectorstore import create_or_update_document, replace_chunks
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
    return {"id": cocktail_id, "name": name, "category": str(raw_data.get("strCategory") or "").strip(), "glass": str(raw_data.get("strGlass") or "").strip(), "ingredients": ingredients, "instructions": str(raw_data.get("strInstructions") or "").strip(), "source_uri": source_uri, "raw": raw_data}


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


def cocktail_text(cocktail: dict[str, Any]) -> str:
    ingredients = ", ".join(f"{item['measure']} {item['name']}".strip() for item in cocktail["ingredients"])
    return f"Name: {cocktail['name']}\nCategory: {cocktail['category']}\nGlass: {cocktail['glass']}\nIngredients: {ingredients}\nInstructions: {cocktail['instructions']}\nSource: {cocktail['source_uri']}"


async def ingest_cocktails(*, letters: list[str], limit: int) -> int:
    cocktails = await fetch_cocktails(letters=letters, limit=min(limit, settings.THECOCKTAILDB_MAX_ITEMS))
    count = 0
    for cocktail in cocktails:
        content = cocktail_text(cocktail)
        document = await create_or_update_document(owner_id=None, source_type="cocktaildb", source_uri=cocktail["source_uri"], external_id=cocktail["id"], filename=None, mime_type="application/json", size_bytes=None, title=cocktail["name"], checksum=None, metadata={"provider": "TheCocktailDB", "external_id": cocktail["id"], "category": cocktail["category"], "glass": cocktail["glass"]})
        embedding = await embed_chunks([Chunk(index=0, content=content, metadata={})])
        await replace_chunks(document["id"], [{"document_id": document["id"], "chunk_index": 0, "content": content, "embedding": embedding[0], "metadata": {"source_type": "cocktaildb", "source_uri": cocktail["source_uri"], "external_id": cocktail["id"], "title": cocktail["name"]}}])
        count += 1
    return count
