from fastapi import Request, HTTPException
import jwt
import requests


CLERK_ISSUER = "https://fitting-mouse-66.clerk.accounts.dev"


def _get_bearer(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


def _get_signing_key(token: str):
    """
    Fetch signing keys from Clerk JWKS and return the correct key for this token.
    """
    jwks_url = f"{CLERK_ISSUER}/.well-known/jwks.json"
    jwks = requests.get(jwks_url, timeout=8).json()
    return jwt.PyJWKClient(jwks_url).get_signing_key_from_jwt(token).key


def require_clerk_user(request: Request) -> dict:
    token = _get_bearer(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing Authorization Bearer token")

    try:
        signing_key = _get_signing_key(token)

        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=CLERK_ISSUER,          
            options={"verify_aud": False} 
        )

        user_id = claims.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token (no sub)")

        return {"clerk_user_id": user_id, "claims": claims}

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Clerk token: {type(e).__name__}")
