BEGIN;

-- 1) Drop FK from resume(job_id) -> job(id), if it exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'resume_job_id_fkey'
  ) THEN
    ALTER TABLE public.resume
      DROP CONSTRAINT resume_job_id_fkey;
  END IF;
END$$;

-- 2) Drop the job_id column from resume, if it exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'resume' AND column_name = 'job_id'
  ) THEN
    ALTER TABLE public.resume
      DROP COLUMN job_id;
  END IF;
END$$;

-- 3) Drop the job table (and its sequence) if it exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'job'
  ) THEN
    DROP TABLE public.job CASCADE;
  END IF;
END$$;

-- (Optional) Clean up grants on job sequence if it somehow remained (defensive)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relname = 'job_id_seq' AND c.relkind = 'S'
  ) THEN
    DROP SEQUENCE public.job_id_seq CASCADE;
  END IF;
END$$;

COMMIT;
