BEGIN;

/* application */
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'application'
  ) THEN
    DROP TABLE public.application CASCADE;
  END IF;
END$$;

/* layout */
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'layout'
  ) THEN
    DROP TABLE public.layout CASCADE;
  END IF;
END$$;

/* scraper_run */
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'scraper_run'
  ) THEN
    DROP TABLE public.scraper_run CASCADE;
  END IF;
END$$;

/* section_type */
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'section_type'
  ) THEN
    DROP TABLE public.section_type CASCADE;
  END IF;
END$$;

/* theme */
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'theme'
  ) THEN
    DROP TABLE public.theme CASCADE;
  END IF;
END$$;

COMMIT;
