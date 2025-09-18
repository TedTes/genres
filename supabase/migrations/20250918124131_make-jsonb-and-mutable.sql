-- If your columns are json already, these UPDATEs are harmless no-ops.

UPDATE resume_optimizations
SET optimized_resume_data = '{}'::jsonb
WHERE optimized_resume_data IS NULL;

UPDATE resume_optimizations
SET original_resume_data = '{}'::jsonb
WHERE original_resume_data IS NULL;

UPDATE resume_optimizations
SET missing_keywords = '[]'::jsonb
WHERE missing_keywords IS NULL;

UPDATE resume_optimizations
SET added_keywords = '[]'::jsonb
WHERE added_keywords IS NULL;

UPDATE resume
SET resume_data = '{}'::jsonb
WHERE resume_data IS NULL;

-- Convert to JSONB (if already json, this is a json -> jsonb cast)
ALTER TABLE resume_optimizations
  ALTER COLUMN optimized_resume_data TYPE jsonb USING optimized_resume_data::jsonb,
  ALTER COLUMN original_resume_data  TYPE jsonb USING original_resume_data::jsonb,
  ALTER COLUMN missing_keywords      TYPE jsonb USING missing_keywords::jsonb,
  ALTER COLUMN added_keywords        TYPE jsonb USING added_keywords::jsonb;

ALTER TABLE resume
  ALTER COLUMN resume_data TYPE jsonb USING resume_data::jsonb;

-- (Optional) set safe defaults so future inserts always have dict/list by default
ALTER TABLE resume_optimizations
  ALTER COLUMN optimized_resume_data SET DEFAULT '{}'::jsonb,
  ALTER COLUMN original_resume_data  SET DEFAULT '{}'::jsonb,
  ALTER COLUMN missing_keywords      SET DEFAULT '[]'::jsonb,
  ALTER COLUMN added_keywords        SET DEFAULT '[]'::jsonb;

ALTER TABLE resume
  ALTER COLUMN resume_data SET DEFAULT '{}'::jsonb;
