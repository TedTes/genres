BEGIN;

-- =========================
-- USER table adjustments
-- =========================
-- Add columns if not present
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'user' AND column_name = 'optimization_count'
  ) THEN
    ALTER TABLE public."user"
      ADD COLUMN optimization_count integer DEFAULT 0;
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'user' AND column_name = 'last_optimization_at'
  ) THEN
    ALTER TABLE public."user"
      ADD COLUMN last_optimization_at timestamp without time zone;
  END IF;
END$$;

-- verification_sent_at: date -> timestamp (models.py uses DateTime)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'user'
      AND column_name = 'verification_sent_at'
      AND data_type = 'date'
  ) THEN
    ALTER TABLE public."user"
      ALTER COLUMN verification_sent_at TYPE timestamp without time zone
      USING verification_sent_at::timestamp;
  END IF;
END$$;

-- =========================
-- RESUME table adjustments
-- =========================

-- title: text -> varchar(200), set default 'Untitled Resume'
-- (remote has NOT NULL already; keep it)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'resume' AND column_name = 'title'
      AND data_type = 'text'
  ) THEN
    ALTER TABLE public.resume
      ALTER COLUMN title TYPE varchar(200) USING LEFT(title, 200);
  END IF;
END$$;

ALTER TABLE public.resume
  ALTER COLUMN title SET DEFAULT 'Untitled Resume';

-- template default -> 'professional_classic'
ALTER TABLE public.resume
  ALTER COLUMN template SET DEFAULT 'professional_classic';

-- created_at default now()
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'resume' AND column_name = 'created_at'
  ) THEN
    -- only set default if none is set already
    IF NOT EXISTS (
      SELECT 1
      FROM pg_attrdef d
      JOIN pg_class c ON c.oid = d.adrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
      JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.adnum
      WHERE n.nspname = 'public' AND c.relname = 'resume' AND a.attname = 'created_at'
    ) THEN
      ALTER TABLE public.resume
        ALTER COLUMN created_at SET DEFAULT now();
    END IF;
  END IF;
END$$;

-- updated_at default now() (NOTE: for true "on update" behavior, use a trigger)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'resume' AND column_name = 'updated_at'
  ) THEN
    IF NOT EXISTS (
      SELECT 1
      FROM pg_attrdef d
      JOIN pg_class c ON c.oid = d.adrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
      JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.adnum
      WHERE n.nspname = 'public' AND c.relname = 'resume' AND a.attname = 'updated_at'
    ) THEN
      ALTER TABLE public.resume
        ALTER COLUMN updated_at SET DEFAULT now();
    END IF;
  END IF;
END$$;

-- Add is_optimized and last_optimized_at if missing
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'resume' AND column_name = 'is_optimized'
  ) THEN
    ALTER TABLE public.resume
      ADD COLUMN is_optimized boolean DEFAULT false;
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'resume' AND column_name = 'last_optimized_at'
  ) THEN
    ALTER TABLE public.resume
      ADD COLUMN last_optimized_at timestamp without time zone;
  END IF;
END$$;

-- =========================
-- RESUME_OPTIMIZATIONS table (new)
-- =========================
-- Create sequence + table if not exists, following your project's pattern
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relname = 'resume_optimizations_id_seq' AND c.relkind = 'S'
  ) THEN
    CREATE SEQUENCE public.resume_optimizations_id_seq
      AS integer START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'resume_optimizations'
  ) THEN
    CREATE TABLE public.resume_optimizations (
      id integer NOT NULL,
      user_id integer NOT NULL,
      resume_id integer NOT NULL,
      original_resume_data json,
      job_description text,
      job_title varchar(200),
      company_name varchar(200),
      optimization_style varchar(50) DEFAULT 'balanced',
      optimized_resume_data json,
      match_score_before double precision,
      match_score_after double precision,
      missing_keywords json,
      added_keywords json,
      docx_url varchar(500),
      pdf_url varchar(500),
      processing_time_ms double precision,
      model_provider varchar(50),
      created_at timestamp without time zone DEFAULT now()
    );
  END IF;
END$$;

-- Default for id
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'resume_optimizations' AND column_name = 'id'
  ) THEN
    ALTER TABLE ONLY public.resume_optimizations
      ALTER COLUMN id SET DEFAULT nextval('public.resume_optimizations_id_seq'::regclass);
  END IF;
END$$;

-- Primary key
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.resume_optimizations'::regclass
      AND contype = 'p'
  ) THEN
    ALTER TABLE ONLY public.resume_optimizations
      ADD CONSTRAINT resume_optimizations_pkey PRIMARY KEY (id);
  END IF;
END$$;

-- Foreign keys
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'resume_optimizations_user_id_fkey'
  ) THEN
    ALTER TABLE ONLY public.resume_optimizations
      ADD CONSTRAINT resume_optimizations_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES public."user"(id);
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'resume_optimizations_resume_id_fkey'
  ) THEN
    ALTER TABLE ONLY public.resume_optimizations
      ADD CONSTRAINT resume_optimizations_resume_id_fkey
      FOREIGN KEY (resume_id) REFERENCES public.resume(id);
  END IF;
END$$;

COMMIT;
