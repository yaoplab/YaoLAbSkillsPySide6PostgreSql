-- LarcCompta: gestion des frais de scolarite
-- A executer sur Intranet (127.0.0.1:5432) ET Supabase Cloud (6543)

-- 1. Bareme des frais par programme / annee scolaire
CREATE TABLE IF NOT EXISTS compta_fee_structure (
    id              SERIAL PRIMARY KEY,
    program_id      INTEGER NOT NULL REFERENCES larcauth_program(id),
    academic_year   VARCHAR(9) NOT NULL,   -- ex: '2026-2027'
    annual_fee      INTEGER NOT NULL,       -- montant annuel en FCFA
    UNIQUE (program_id, academic_year)
);

-- 2. Plan de paiement par eleve
CREATE TABLE IF NOT EXISTS compta_payment_schedule (
    id              SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES larcauth_aecuser(id),
    academic_year   VARCHAR(9) NOT NULL,
    total_due       INTEGER NOT NULL,       -- montant total du
    payment_mode    VARCHAR(20) NOT NULL DEFAULT 'mensuel',  -- mensuel / trimestriel / annuel
    monthly_amount  INTEGER,                -- si mensuel : montant par mois
    term_amount     INTEGER,                -- si trimestriel : montant par trimestre
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE (student_id, academic_year)
);

-- 3. Paiements individuels
CREATE TABLE IF NOT EXISTS compta_payment (
    id              SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES larcauth_aecuser(id),
    amount          INTEGER NOT NULL,       -- montant verse en FCFA
    payment_date    DATE NOT NULL DEFAULT CURRENT_DATE,
    payment_method  VARCHAR(30) DEFAULT 'especes',  -- especes, cheque, virement, mobile_money
    reference       VARCHAR(100),           -- numero de cheque / reference virement
    received_by     INTEGER REFERENCES larcauth_aecuser(id),
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 4. Rappels envoyes
CREATE TABLE IF NOT EXISTS compta_reminder (
    id              SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES larcauth_aecuser(id),
    parent_id       INTEGER REFERENCES larcauth_aecuser(id),
    reminder_type   VARCHAR(20) DEFAULT 'email',  -- email, sms, whatsapp, courrier
    sent_at         TIMESTAMP DEFAULT NOW(),
    status          VARCHAR(20) DEFAULT 'envoye',  -- envoye, echec, lu
    message         TEXT,
    created_by      INTEGER REFERENCES larcauth_aecuser(id)
);

-- 5. Insertion baremes par defaut
INSERT INTO compta_fee_structure (program_id, academic_year, annual_fee)
VALUES
    -- Primaire / College : 2 500 000 FCFA
    (11, '2026-2027', 2500000),
    (12, '2026-2027', 2500000),
    (21, '2026-2027', 2500000),
    (22, '2026-2027', 2500000),
    -- Lycee / DP : 3 000 000 FCFA
    (13, '2026-2027', 3000000),
    (23, '2026-2027', 3000000)
ON CONFLICT (program_id, academic_year) DO NOTHING;
