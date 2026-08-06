-- LarcRH: tables pour la gestion des ressources humaines
-- À exécuter sur Intranet (127.0.0.1:5432) ET Supabase Cloud (6543)

-- 1. Table de liaison staff non enseignant
CREATE TABLE IF NOT EXISTS larcauth_staff (
    aecuser_ptr_id  INTEGER PRIMARY KEY REFERENCES larcauth_aecuser(id),
    enabled         BOOLEAN DEFAULT FALSE,
    fk_job_category_id INTEGER,
    hire_date       DATE
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
