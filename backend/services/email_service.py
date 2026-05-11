"""
Email service para HORUS Universal.
Soporta: Resend API (recomendado) o SMTP como fallback.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


async def send_team_invitation(
    *,
    to_email: str,
    inviter_name: str,
    team_name: str,
    team_id: str,
    role: str = "member",
) -> bool:
    """
    Envía email de invitación a un equipo HORUS.
    Retorna True si se envió, False si no hay config de email disponible.
    """
    try:
        # Intentar con Resend primero (si está configurado)
        resend_key = os.environ.get("RESEND_API_KEY", "")
        if resend_key:
            return await _send_via_resend(
                resend_key=resend_key,
                to_email=to_email,
                subject=f"Invitación al equipo {team_name} en HORUS",
                html=_team_invite_html(inviter_name, team_name, team_id, role),
            )

        # Fallback: SMTP
        smtp_host = os.environ.get("SMTP_HOST", "")
        if smtp_host:
            return await _send_via_smtp(
                to_email=to_email,
                subject=f"Invitación al equipo {team_name} en HORUS",
                html=_team_invite_html(inviter_name, team_name, team_id, role),
            )

        logger.warning("[Email] No email provider configured (RESEND_API_KEY or SMTP_HOST). Skipping.")
        return False

    except Exception as e:
        logger.error(f"[Email] Failed to send team invitation to {to_email}: {e}")
        return False


async def _send_via_resend(*, resend_key: str, to_email: str, subject: str, html: str) -> bool:
    """Send via Resend API (https://resend.com)."""
    import httpx
    from_addr = os.environ.get("EMAIL_FROM", "HORUS Universal <noreply@horusai.app>")

    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json",
            },
            json={"from": from_addr, "to": [to_email], "subject": subject, "html": html},
        )

    if res.status_code in (200, 201):
        logger.info(f"[Email] Resend OK -> {to_email}")
        return True
    else:
        logger.error(f"[Email] Resend error {res.status_code}: {res.text[:200]}")
        return False


async def _send_via_smtp(*, to_email: str, subject: str, html: str) -> bool:
    """Send via SMTP (uses env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS)."""
    import asyncio
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")
    from_addr = os.environ.get("EMAIL_FROM", user or "noreply@horusai.app")

    def _do_send():
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to_email], msg.as_string())

    try:
        await asyncio.to_thread(_do_send)
        logger.info(f"[Email] SMTP OK -> {to_email}")
        return True
    except Exception as e:
        logger.error(f"[Email] SMTP error: {e}")
        return False


def _team_invite_html(inviter_name: str, team_name: str, team_id: str, role: str) -> str:
    app_url = os.environ.get("FRONTEND_URL", "https://horus-universal.vercel.app")
    role_label = {"admin": "Administrador", "member": "Miembro", "viewer": "Observador"}.get(role, role.capitalize())

    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#f1f5f9; margin:0; padding:20px; }}
    .card {{ background:#fff; max-width:520px; margin:0 auto; border-radius:20px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,.08); }}
    .hero {{ background:linear-gradient(135deg,#4f46e5,#7c3aed); padding:40px 32px; text-align:center; }}
    .logo {{ font-size:48px; margin-bottom:12px; }}
    .hero h1 {{ color:#fff; font-size:22px; font-weight:700; margin:0; }}
    .hero p {{ color:rgba(255,255,255,.7); font-size:14px; margin:6px 0 0; }}
    .body {{ padding:32px; }}
    .body p {{ color:#475569; font-size:15px; line-height:1.6; margin:0 0 16px; }}
    .team-badge {{ display:inline-block; background:#ede9fe; color:#4f46e5; font-weight:700;
                   padding:6px 16px; border-radius:20px; font-size:14px; margin:4px 0 20px; }}
    .role-badge {{ display:inline-block; background:#f0fdf4; color:#16a34a; font-weight:600;
                   padding:4px 12px; border-radius:12px; font-size:13px; }}
    .btn {{ display:block; background:#4f46e5; color:#fff !important; text-decoration:none;
            text-align:center; padding:15px 24px; border-radius:12px; font-weight:700;
            font-size:16px; margin:24px 0 16px; }}
    .footer {{ background:#f8fafc; padding:20px 32px; border-top:1px solid #e2e8f0;
               text-align:center; color:#94a3b8; font-size:12px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="hero">
      <div class="logo">👁</div>
      <h1>HORUS Universal</h1>
      <p>Orquestador Personal de IA</p>
    </div>
    <div class="body">
      <p>Hola,</p>
      <p><strong>{inviter_name}</strong> te ha invitado a unirte al equipo:</p>
      <div class="team-badge">🏢 {team_name}</div>
      <p>Tu rol será: <span class="role-badge">{role_label}</span></p>
      <p>HORUS Universal te da acceso a 16 agentes de IA especializados para potenciar tu productividad en equipo.</p>
      <a href="{app_url}/teams/{team_id}" class="btn">✅ Aceptar invitación</a>
      <p style="font-size:13px;color:#94a3b8;">Si no esperabas esta invitación, ignora este correo.</p>
    </div>
    <div class="footer">
      HORUS Universal · Tu orquestador de IA personal<br>
      <a href="{app_url}" style="color:#6366f1;">{app_url}</a>
    </div>
  </div>
</body>
</html>
"""
