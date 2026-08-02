"""Reinitialise le mot de passe d'un utilisateur Larc.

Usage:
  python reset_pwd.py <email> [nouveau_mot_de_passe]
  python reset_pwd.py patrlabo@arc-en-ciel.org
  python reset_pwd.py prof@arc-en-ciel.org "NouveauMdp2026"
"""

import hashlib
import sys
from larccommon.database import db


def reset_password(email: str, new_pass: str = "Aec-2026") -> bool:
    """Reinitialise le mot de passe d'un utilisateur."""
    if not db.connect_intranet():
        print("ERREUR: Connexion intranet echouee. Verifier config.ini [IntranetDatabase].")
        return False

    if not db.is_server_connected:
        print("ERREUR: Base de donnees inaccessible.")
        return False

    h = hashlib.sha256(new_pass.encode('utf-8')).hexdigest()
    print(f'Hash SHA-256: {h}')

    try:
        with db.server_conn.cursor() as cur:
            cur.execute(
                "SELECT id, email FROM larcauth_aecuser WHERE LOWER(email) = %s",
                (email.lower(),)
            )
            row = cur.fetchone()
            if not row:
                print(f'Utilisateur {email} NON trouve.')
                return False

            print(f'Utilisateur trouve: id={row[0]}, email={row[1]}')
            cur.execute(
                "UPDATE larcauth_aecuser SET password = %s WHERE id = %s",
                (h, row[0])
            )
        print(f'Mot de passe reinitialise avec succes.')
        return True
    except Exception as e:
        print(f'ERREUR: {e}')
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    email = sys.argv[1]
    new_pass = sys.argv[2] if len(sys.argv) > 2 else "Aec-2026"
    ok = reset_password(email, new_pass)
    sys.exit(0 if ok else 1)
