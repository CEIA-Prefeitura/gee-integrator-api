from typing import Any, Callable, List, Sequence
from fastapi import APIRouter, Depends
from app.auth.check_rules import RequireRoles

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}

class RoleAPIRouter(APIRouter):
    """
    Router que aceita `roles=[...]` em *qualquer* decorator HTTP.
    Ex.: @router.get("/path", roles=["admin"])
    """

    # ------------------ núcleo: injeta a dependência ------------------ #
    @staticmethod
    def _with_roles(deps: List[Any] | None, roles: Sequence[str] | None):
        deps = list(deps or [])
        if roles:
            deps.append(Depends(RequireRoles(*roles)))
        return deps

    # --------------- override genérico para todos os verbos ----------- #
    def __getattribute__(self, name: str):                    # noqa: C901
        """Intercepta .get/.post/... para aceitar o novo kwargs `roles=`."""
        attr = super().__getattribute__(name)
        if name.upper() in HTTP_METHODS:          # é um decorator HTTP
            def wrapper(path: str, *, roles: Sequence[str] | None = None, **kw):
                # `dependencies` pode ter vindo do usuário
                kw["dependencies"] = self._with_roles(kw.get("dependencies"), roles)
                return attr(path, **kw)           # chama decorator original
            return wrapper
        return attr
