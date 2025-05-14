from fastapi import HTTPException, status
from fastapi import Depends
from starlette.requests import Request

def RequireRoles(*allowed: str):
    """Factory de dependência que exige pelo menos uma das roles informadas."""
    async def _checker(request: Request):          # sem  Depends()
        user_roles: list[str] = getattr(request.state, "roles", [])
        if not any(role in user_roles for role in allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )
    return _checker