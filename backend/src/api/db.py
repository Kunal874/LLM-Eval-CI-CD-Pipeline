"""Supabase client instance — imported by routers for database access."""

from supabase import create_client, Client
from api.config import settings

supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
