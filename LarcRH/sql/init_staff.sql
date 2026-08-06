-- LarcRH v2: tables pour la gestion des ressources humaines
-- À exécuter sur Intranet (127.0.0.1:5432) ET Supabase Cloud (6543)

-- 1. Table de liaison staff non enseignant (postes/métiers)
DROP TABLE IF EXISTS larcauth_staff CASCADE;
CREATE TABLE larcauth_staff (
    aecuser_ptr_id          INTEGER PRIMARY KEY REFERENCES larcauth_aecuser(id),
    enabled                 BOOLEAN DEFAULT FALSE,
    hire_date               DATE,
    -- Postes / métiers (un membre du staff peut cumuler)
    is_DRH                  BOOLEAN DEFAULT FALSE,
    is_comptable            BOOLEAN DEFAULT FALSE,
    is_secretaire           BOOLEAN DEFAULT FALSE,
    is_AVS                  BOOLEAN DEFAULT FALSE,
    is_technicien_surface   BOOLEAN DEFAULT FALSE,
    is_technicien_info      BOOLEAN DEFAULT FALSE,
    is_documentaliste       BOOLEAN DEFAULT FALSE,
    is_infirmier            BOOLEAN DEFAULT FALSE,
    is_psychologue          BOOLEAN DEFAULT FALSE,
    is_directeur            BOOLEAN DEFAULT FALSE
);

-- 2. Événements staff (absences, retards, sorties)
-- Même structure que student_event
CREATE TABLE IF NOT EXISTS staff_event (
    event_id        SERIAL PRIMARY KEY,
    staff_id        INTEGER NOT NULL REFERENCES larcauth_aecuser(id),
    event_type      TEXT,
    event_at        TIMESTAMP,
    note            TEXT,
    source          TEXT,
    created_by      INTEGER,
    validated_by    INTEGER,
    created_at      TIMESTAMP DEFAULT NOW(),
    lieu_label      TEXT,
    subject_label   TEXT
);
