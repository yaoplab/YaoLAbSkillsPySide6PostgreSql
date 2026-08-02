import os
import shutil
import urllib.request

from .app_config import app_config
from .logger import log
from .session import ConnMode, session

_SUPABASE_REF = "crvyxfsuvwqxzlhsfbwq"
_STORAGE_URL = f"https://{_SUPABASE_REF}.supabase.co/storage/v1/object/public/student-photos"


def _intranet_path(sid: int) -> str:
    return os.path.join(app_config.get("photos_dir"), f"{sid}.png")


def _cache_path(sid: int) -> str:
    return os.path.join(app_config.get("photos_cache_dir"), f"{sid}.png")


def get_photo_path(sid: int) -> str:
    """Renvoie un chemin valide vers la photo de l'élève.

    Priorité : fichier local (dossier partagé intranet) → cache → cloud.
    - Intranet : chemin local direct (dossier partagé LarcSuperviseur)
    - Cloud    : télécharge depuis Supabase Storage dans le cache local
    """
    # Le fichier intranet est la source locale de vérité : s'il existe
    # (sauvegarde fraîche), il est utilisé en priorité, dans les deux modes.
    local = _intranet_path(sid)
    if os.path.isfile(local):
        return local

    cache = _cache_path(sid)
    if os.path.isfile(cache):
        return cache

    if session.conn_mode == ConnMode.INTRANET:
        return local

    try:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        url = f"{_STORAGE_URL}/{sid}.png"
        urllib.request.urlretrieve(url, cache)
        log(f"Photos: telecharge {sid}.png depuis le cloud")
        return cache
    except Exception as e:
        log(f"Photos: echec telechargement {sid}.png ({e})")
        return local


def save_photo(sid: int, source_path: str) -> str:
    """Sauvegarde une photo depuis un fichier source.

    Écrit à la fois dans le dossier intranet ET le cache local : en mode cloud,
    le cache étant prioritaire après la sauvegarde, la nouvelle photo apparaît
    immédiatement (avant, le cache gardait l'ancienne photo → « rien ne change »).
    Retourne le chemin de destination (intranet).
    """
    dest = _intranet_path(sid)
    cache = _cache_path(sid)
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        shutil.copy2(source_path, dest)
        shutil.copy2(source_path, cache)
        log(f"Photos: sauvegarde {sid}.png depuis {source_path}")
    except Exception as e:
        log(f"Photos: echec sauvegarde {sid}.png ({e})")
        raise
    return dest
