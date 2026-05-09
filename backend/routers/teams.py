"""
Router de Teams — HORUS Universal
Workspaces de equipo: crear org, invitar miembros, historial compartido, roles.
"""
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from auth.supabase_auth import get_optional_user
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/teams", tags=["teams"])


def _client():
    from supabase import create_client
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def _require_user(user):
    if not user:
        raise HTTPException(401, "Autenticación requerida.")
    return user


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateTeamRequest(BaseModel):
    name: str
    description: Optional[str] = ""

class InviteMemberRequest(BaseModel):
    email: str
    role: str = "member"  # admin | member | viewer

class UpdateRoleRequest(BaseModel):
    user_id: str
    role: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/")
async def create_team(body: CreateTeamRequest, user=Depends(get_optional_user)):
    """Crea un nuevo workspace de equipo."""
    _require_user(user)
    client = _client()
    team_id = str(uuid.uuid4())

    try:
        # Create team
        client.table("teams").insert({
            "id": team_id,
            "name": body.name,
            "description": body.description,
            "owner_id": user.id,
            "plan": "team",
        }).execute()

        # Add creator as admin
        client.table("team_members").insert({
            "team_id": team_id,
            "user_id": user.id,
            "role": "admin",
            "email": getattr(user, "email", ""),
        }).execute()

        return {"id": team_id, "name": body.name, "role": "admin"}
    except Exception as e:
        logger.error(f"[Teams] create error: {e}")
        raise HTTPException(500, str(e))


@router.get("/")
async def list_teams(user=Depends(get_optional_user)):
    """Lista los teams del usuario."""
    _require_user(user)
    client = _client()
    try:
        result = client.table("team_members") \
            .select("role, teams(id, name, description, plan, owner_id, created_at)") \
            .eq("user_id", user.id) \
            .execute()
        teams = []
        for row in (result.data or []):
            team = row.get("teams") or {}
            teams.append({**team, "my_role": row.get("role", "member")})
        return {"teams": teams}
    except Exception as e:
        logger.error(f"[Teams] list error: {e}")
        return {"teams": []}


@router.get("/{team_id}")
async def get_team(team_id: str, user=Depends(get_optional_user)):
    """Obtiene detalles de un team."""
    _require_user(user)
    client = _client()
    # Verify membership
    mem = client.table("team_members").select("role").eq("team_id", team_id).eq("user_id", user.id).execute()
    if not mem.data:
        raise HTTPException(403, "No eres miembro de este equipo.")

    team = client.table("teams").select("*").eq("id", team_id).single().execute()
    members = client.table("team_members").select("user_id, email, role, joined_at").eq("team_id", team_id).execute()

    return {
        **team.data,
        "members": members.data or [],
        "my_role": mem.data[0]["role"],
    }


@router.post("/{team_id}/invite")
async def invite_member(team_id: str, body: InviteMemberRequest, user=Depends(get_optional_user)):
    """Invita a un miembro al equipo (solo admins)."""
    _require_user(user)
    client = _client()

    # Check caller is admin
    mem = client.table("team_members").select("role").eq("team_id", team_id).eq("user_id", user.id).execute()
    if not mem.data or mem.data[0]["role"] not in ("admin",):
        raise HTTPException(403, "Solo los admins pueden invitar miembros.")

    # Find user by email in user_plans
    target = client.table("user_plans").select("user_id").eq("email", body.email).execute()
    if not target.data:
        raise HTTPException(404, f"Usuario {body.email} no encontrado en HORUS.")

    target_id = target.data[0]["user_id"]

    # Check not already member
    existing = client.table("team_members").select("id").eq("team_id", team_id).eq("user_id", target_id).execute()
    if existing.data:
        raise HTTPException(409, "El usuario ya es miembro de este equipo.")

    client.table("team_members").insert({
        "team_id": team_id,
        "user_id": target_id,
        "role": body.role,
        "email": body.email,
    }).execute()

    return {"message": f"{body.email} añadido como {body.role}.", "team_id": team_id}


@router.patch("/{team_id}/members")
async def update_member_role(team_id: str, body: UpdateRoleRequest, user=Depends(get_optional_user)):
    """Cambia el rol de un miembro."""
    _require_user(user)
    client = _client()
    mem = client.table("team_members").select("role").eq("team_id", team_id).eq("user_id", user.id).execute()
    if not mem.data or mem.data[0]["role"] != "admin":
        raise HTTPException(403, "Solo admins pueden cambiar roles.")
    client.table("team_members").update({"role": body.role}).eq("team_id", team_id).eq("user_id", body.user_id).execute()
    return {"message": "Rol actualizado."}


@router.delete("/{team_id}/members/{member_id}")
async def remove_member(team_id: str, member_id: str, user=Depends(get_optional_user)):
    """Elimina a un miembro del equipo."""
    _require_user(user)
    client = _client()
    mem = client.table("team_members").select("role").eq("team_id", team_id).eq("user_id", user.id).execute()
    if not mem.data or (mem.data[0]["role"] != "admin" and user.id != member_id):
        raise HTTPException(403, "Sin permisos.")
    client.table("team_members").delete().eq("team_id", team_id).eq("user_id", member_id).execute()
    return {"message": "Miembro eliminado."}
