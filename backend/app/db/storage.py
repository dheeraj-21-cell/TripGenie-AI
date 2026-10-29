import sqlite3
import json
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Any, Dict
from ..models.schemas import TripResponse, TripRecord
from ..core.config import settings

logger = logging.getLogger("tripgenie.storage")

# Optional Supabase import (available in backend .venv via supabase-py)
try:
    from supabase import create_client, Client
    HAS_SUPABASE_LIB = True
except ImportError:
    HAS_SUPABASE_LIB = False
    Client = Any

DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "tripgenie.db"


class SQLiteStorageEngine:
    """
    Local SQLite Storage Engine (100% Free, zero external dependency).
    Provides resilient, durable local storage for itineraries and acts as the
    automatic fallback engine if Supabase Cloud is unreachable or unconfigured.
    """
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize SQLite table for local trip persistence."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS saved_trips (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    itinerary_json TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_trip(self, trip: TripResponse, user_id: str = "local-guest") -> TripRecord:
        """Save a new trip itinerary locally in SQLite."""
        trip_id = trip.id or str(uuid.uuid4())
        created_at = trip.created_at or datetime.now(timezone.utc).isoformat()

        trip.id = trip_id
        trip.created_at = created_at

        itinerary_json = trip.model_dump_json()

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO saved_trips (id, user_id, destination, duration_days, created_at, itinerary_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (trip_id, user_id, trip.destination, trip.duration_days, created_at, itinerary_json))
            conn.commit()

        return TripRecord(
            id=trip_id,
            user_id=user_id,
            destination=trip.destination,
            duration_days=trip.duration_days,
            created_at=created_at,
            itinerary_data=trip
        )

    def get_trip(self, trip_id: str, user_id: Optional[str] = None) -> Optional[TripRecord]:
        """Fetch a saved trip from SQLite by its unique ID, with optional user_id isolation."""
        with self._get_connection() as conn:
            if user_id:
                row = conn.execute(
                    "SELECT * FROM saved_trips WHERE id = ? AND user_id = ?",
                    (trip_id, user_id)
                ).fetchone()
            else:
                row = conn.execute("SELECT * FROM saved_trips WHERE id = ?", (trip_id,)).fetchone()

            if not row:
                return None
            trip_data = TripResponse.model_validate_json(row["itinerary_json"])
            return TripRecord(
                id=row["id"],
                user_id=row["user_id"],
                destination=row["destination"],
                duration_days=row["duration_days"],
                created_at=row["created_at"],
                itinerary_data=trip_data
            )

    def list_trips(self, user_id: str = "local-guest") -> List[TripRecord]:
        """List all saved itineraries from SQLite for a given user, ordered newest first."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM saved_trips WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            ).fetchall()

            records = []
            for row in rows:
                try:
                    trip_data = TripResponse.model_validate_json(row["itinerary_json"])
                    records.append(TripRecord(
                        id=row["id"],
                        user_id=row["user_id"],
                        destination=row["destination"],
                        duration_days=row["duration_days"],
                        created_at=row["created_at"],
                        itinerary_data=trip_data
                    ))
                except Exception as exc:
                    logger.warning(f"Error reading SQLite trip record: {exc}")
                    continue
            return records

    def update_trip(self, trip_id: str, trip: TripResponse, user_id: Optional[str] = None) -> Optional[TripRecord]:
        """Update an existing itinerary in SQLite, ensuring user isolation."""
        existing = self.get_trip(trip_id, user_id=user_id)
        if not existing:
            return None

        trip.id = trip_id
        trip.created_at = existing.created_at
        itinerary_json = trip.model_dump_json()

        with self._get_connection() as conn:
            if user_id:
                conn.execute("""
                    UPDATE saved_trips
                    SET destination = ?, duration_days = ?, itinerary_json = ?
                    WHERE id = ? AND user_id = ?
                """, (trip.destination, trip.duration_days, itinerary_json, trip_id, user_id))
            else:
                conn.execute("""
                    UPDATE saved_trips
                    SET destination = ?, duration_days = ?, itinerary_json = ?
                    WHERE id = ?
                """, (trip.destination, trip.duration_days, itinerary_json, trip_id))
            conn.commit()

        return TripRecord(
            id=trip_id,
            user_id=existing.user_id,
            destination=trip.destination,
            duration_days=trip.duration_days,
            created_at=existing.created_at,
            itinerary_data=trip
        )

    def delete_trip(self, trip_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a saved trip from SQLite, ensuring user isolation."""
        with self._get_connection() as conn:
            if user_id:
                cursor = conn.execute("DELETE FROM saved_trips WHERE id = ? AND user_id = ?", (trip_id, user_id))
            else:
                cursor = conn.execute("DELETE FROM saved_trips WHERE id = ?", (trip_id,))
            conn.commit()
            return cursor.rowcount > 0


class SupabaseStorageEngine:
    """
    Supabase Cloud PostgreSQL Storage Engine (100% Free Tier - https://supabase.com).
    Connects to the managed Supabase PostgreSQL instance via the official Supabase Python client.
    Stores structured itineraries with JSONB support and user isolation.
    """
    def __init__(self, client: Optional[Any] = None):
        self._client = client

    def get_client(self) -> Any:
        """Retrieve or lazily initialize the authenticated Supabase client."""
        if self._client is not None:
            return self._client
        if not HAS_SUPABASE_LIB:
            raise RuntimeError("supabase package is not installed in the python environment.")
        if not settings.is_supabase_available:
            raise RuntimeError("Supabase credentials not configured in backend/.env.")

        url = settings.SUPABASE_URL
        key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        self._client = create_client(url, key)
        return self._client

    def save_trip(self, trip: TripResponse, user_id: str = "local-guest") -> TripRecord:
        """Save or upsert a trip itinerary in Supabase PostgreSQL 'trips' table."""
        trip_id = trip.id or str(uuid.uuid4())
        created_at = trip.created_at or datetime.now(timezone.utc).isoformat()

        trip.id = trip_id
        trip.created_at = created_at

        payload = {
            "id": trip_id,
            "user_id": user_id,
            "destination": trip.destination,
            "duration_days": trip.duration_days,
            "created_at": created_at,
            "itinerary_data": trip.model_dump(mode="json")
        }

        client = self.get_client()
        client.table("trips").upsert(payload).execute()

        return TripRecord(
            id=trip_id,
            user_id=user_id,
            destination=trip.destination,
            duration_days=trip.duration_days,
            created_at=created_at,
            itinerary_data=trip
        )

    def get_trip(self, trip_id: str, user_id: Optional[str] = None) -> Optional[TripRecord]:
        """Fetch a saved trip from Supabase 'trips' table by its ID, with optional user_id isolation."""
        client = self.get_client()
        query = client.table("trips").select("*").eq("id", trip_id)
        if user_id:
            query = query.eq("user_id", user_id)
        res = query.execute()
        if not res.data:
            return None

        row = res.data[0]
        itinerary_data = row.get("itinerary_data")
        if isinstance(itinerary_data, str):
            trip_obj = TripResponse.model_validate_json(itinerary_data)
        elif isinstance(itinerary_data, dict):
            trip_obj = TripResponse.model_validate(itinerary_data)
        else:
            return None

        return TripRecord(
            id=row["id"],
            user_id=row.get("user_id", user_id or "local-guest"),
            destination=row.get("destination", trip_obj.destination),
            duration_days=row.get("duration_days", trip_obj.duration_days),
            created_at=row.get("created_at", trip_obj.created_at or ""),
            itinerary_data=trip_obj
        )

    def list_trips(self, user_id: str = "local-guest") -> List[TripRecord]:
        """List all saved itineraries for a given user from Supabase, ordered newest first."""
        client = self.get_client()
        res = client.table("trips").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()

        records: List[TripRecord] = []
        for row in (res.data or []):
            try:
                itinerary_data = row.get("itinerary_data")
                if isinstance(itinerary_data, str):
                    trip_obj = TripResponse.model_validate_json(itinerary_data)
                elif isinstance(itinerary_data, dict):
                    trip_obj = TripResponse.model_validate(itinerary_data)
                else:
                    continue
                records.append(TripRecord(
                    id=row["id"],
                    user_id=row.get("user_id", user_id),
                    destination=row.get("destination", trip_obj.destination),
                    duration_days=row.get("duration_days", trip_obj.duration_days),
                    created_at=row.get("created_at", trip_obj.created_at or ""),
                    itinerary_data=trip_obj
                ))
            except Exception as exc:
                logger.warning(f"Error parsing Supabase trip record: {exc}")
                continue
        return records

    def update_trip(self, trip_id: str, trip: TripResponse, user_id: Optional[str] = None) -> Optional[TripRecord]:
        """Update an existing itinerary in Supabase, enforcing user ownership."""
        client = self.get_client()
        query = client.table("trips").select("*").eq("id", trip_id)
        if user_id:
            query = query.eq("user_id", user_id)
        res = query.execute()
        if not res.data:
            return None

        existing = res.data[0]
        created_at = existing.get("created_at") or trip.created_at or datetime.now(timezone.utc).isoformat()
        owner_user_id = existing.get("user_id", user_id or "local-guest")

        trip.id = trip_id
        trip.created_at = created_at

        update_payload = {
            "destination": trip.destination,
            "duration_days": trip.duration_days,
            "itinerary_data": trip.model_dump(mode="json")
        }
        up_query = client.table("trips").update(update_payload).eq("id", trip_id)
        if user_id:
            up_query = up_query.eq("user_id", user_id)
        up_query.execute()

        return TripRecord(
            id=trip_id,
            user_id=owner_user_id,
            destination=trip.destination,
            duration_days=trip.duration_days,
            created_at=created_at,
            itinerary_data=trip
        )

    def delete_trip(self, trip_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a saved trip from Supabase, enforcing user ownership."""
        client = self.get_client()
        query = client.table("trips").select("id").eq("id", trip_id)
        if user_id:
            query = query.eq("user_id", user_id)
        res = query.execute()
        if not res.data:
            return False

        del_query = client.table("trips").delete().eq("id", trip_id)
        if user_id:
            del_query = del_query.eq("user_id", user_id)
        del_query.execute()
        return True


class DatabaseStorage:
    """
    Unified Storage Adapter with Cloud-Primary / Local-Fallback Strategy:
    - Primary: Supabase PostgreSQL Cloud (if SUPABASE_URL and key are configured).
    - Fallback: Local SQLite database (if Supabase is unconfigured, unreachable, or fails).

    Guarantees ₹0 spending, user data isolation, and uninterrupted service.
    """
    def __init__(self, db_path: Path = DB_PATH):
        self.sqlite_engine = SQLiteStorageEngine(db_path=db_path)
        self.supabase_engine = SupabaseStorageEngine()

    @property
    def db_path(self) -> Path:
        """Backwards compatibility accessor for SQLite DB path."""
        return self.sqlite_engine.db_path

    @property
    def is_supabase_active(self) -> bool:
        """Check whether Supabase is configured and should be used as primary."""
        return settings.is_supabase_available

    @property
    def active_storage(self) -> str:
        """Name of the active storage mode for diagnostics and health check."""
        return "supabase_cloud" if self.is_supabase_active else "local_sqlite_free"

    def save_trip(self, trip: TripResponse, user_id: str = "local-guest") -> TripRecord:
        """Save a trip to Supabase Cloud with seamless fallback to SQLite on failure."""
        if self.is_supabase_active:
            try:
                return self.supabase_engine.save_trip(trip, user_id=user_id)
            except Exception as exc:
                logger.warning(f"Supabase save_trip failed ({exc}); falling back to local SQLite.")
                return self.sqlite_engine.save_trip(trip, user_id=user_id)
        return self.sqlite_engine.save_trip(trip, user_id=user_id)

    def get_trip(self, trip_id: str, user_id: Optional[str] = None) -> Optional[TripRecord]:
        """Fetch trip from Supabase, checking local SQLite if not found or on error, respecting user_id."""
        if self.is_supabase_active:
            try:
                record = self.supabase_engine.get_trip(trip_id, user_id=user_id)
                if record is not None:
                    return record
                return self.sqlite_engine.get_trip(trip_id, user_id=user_id)
            except Exception as exc:
                logger.warning(f"Supabase get_trip failed ({exc}); falling back to local SQLite.")
                return self.sqlite_engine.get_trip(trip_id, user_id=user_id)
        return self.sqlite_engine.get_trip(trip_id, user_id=user_id)

    def list_trips(self, user_id: str = "local-guest") -> List[TripRecord]:
        """List trips for a specific user from Supabase merged with any existing local SQLite trips."""
        if self.is_supabase_active:
            try:
                cloud_trips = self.supabase_engine.list_trips(user_id=user_id)
                local_trips = self.sqlite_engine.list_trips(user_id=user_id)
                seen_ids = {t.id for t in cloud_trips}
                merged = list(cloud_trips)
                for t in local_trips:
                    if t.id not in seen_ids:
                        merged.append(t)
                return merged
            except Exception as exc:
                logger.warning(f"Supabase list_trips failed ({exc}); falling back to local SQLite.")
                return self.sqlite_engine.list_trips(user_id=user_id)
        return self.sqlite_engine.list_trips(user_id=user_id)

    def update_trip(self, trip_id: str, trip: TripResponse, user_id: Optional[str] = None) -> Optional[TripRecord]:
        """Update trip in Supabase, falling back to local SQLite if record exists there, respecting user_id."""
        if self.is_supabase_active:
            try:
                record = self.supabase_engine.update_trip(trip_id, trip, user_id=user_id)
                if record is not None:
                    return record
                return self.sqlite_engine.update_trip(trip_id, trip, user_id=user_id)
            except Exception as exc:
                logger.warning(f"Supabase update_trip failed ({exc}); falling back to local SQLite.")
                return self.sqlite_engine.update_trip(trip_id, trip, user_id=user_id)
        return self.sqlite_engine.update_trip(trip_id, trip, user_id=user_id)

    def delete_trip(self, trip_id: str, user_id: Optional[str] = None) -> bool:
        """Delete trip from Supabase and/or SQLite, respecting user_id."""
        if self.is_supabase_active:
            try:
                cloud_deleted = self.supabase_engine.delete_trip(trip_id, user_id=user_id)
                local_deleted = self.sqlite_engine.delete_trip(trip_id, user_id=user_id)
                return cloud_deleted or local_deleted
            except Exception as exc:
                logger.warning(f"Supabase delete_trip failed ({exc}); falling back to local SQLite.")
                return self.sqlite_engine.delete_trip(trip_id, user_id=user_id)
        return self.sqlite_engine.delete_trip(trip_id, user_id=user_id)


# Global singleton database storage instance
db_storage = DatabaseStorage()
