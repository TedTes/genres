ALTER TABLE job
    ADD COLUMN salary_min INTEGER,
    ADD COLUMN salary_max INTEGER,
    ADD COLUMN salary_currency VARCHAR(10) DEFAULT 'USD',
    ADD COLUMN salary_period VARCHAR(20) DEFAULT 'yearly',
    
    ADD COLUMN experience_level VARCHAR(20),
    ADD COLUMN employment_type VARCHAR(20),
    ADD COLUMN industry VARCHAR(50),
    ADD COLUMN company_size VARCHAR(20),
    
    ADD COLUMN required_skills TEXT[],

    ADD COLUMN benefits TEXT,
    ADD COLUMN application_deadline TIMESTAMP,
    ADD COLUMN education_required VARCHAR(50);
