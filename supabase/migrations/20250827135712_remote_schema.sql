

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE EXTENSION IF NOT EXISTS "pgsodium";






COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgjwt" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";





SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."application" (
    "id" integer NOT NULL,
    "user_id" integer NOT NULL,
    "job_id" integer NOT NULL,
    "resume_id" integer,
    "status" character varying(50),
    "applied_date" timestamp without time zone,
    "last_updated" timestamp without time zone,
    "notes" "text"
);


ALTER TABLE "public"."application" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."application_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."application_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."application_id_seq" OWNED BY "public"."application"."id";



CREATE TABLE IF NOT EXISTS "public"."job" (
    "id" integer NOT NULL,
    "slug" character varying(100),
    "title" character varying(200) NOT NULL,
    "company" character varying(100) NOT NULL,
    "location" character varying(100),
    "description" "text",
    "posted_at" timestamp without time zone,
    "remote" boolean DEFAULT false,
    "source" "text" DEFAULT 'NULL'::"text",
    "source_job_id" "text" DEFAULT 'NULL'::"text",
    "is_active" boolean DEFAULT true,
    "last_seen" "date",
    "url" "text" DEFAULT 'NULL'::"text",
    "salary_min" integer,
    "salary_max" integer,
    "salary_currency" character varying(10) DEFAULT 'USD'::character varying,
    "salary_period" character varying(20) DEFAULT 'yearly'::character varying,
    "experience_level" character varying(20),
    "employment_type" character varying(20),
    "industry" character varying(50),
    "company_size" character varying(20),
    "required_skills" "text"[],
    "benefits" "text",
    "application_deadline" timestamp without time zone,
    "education_required" character varying(50)
);


ALTER TABLE "public"."job" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."job_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."job_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."job_id_seq" OWNED BY "public"."job"."id";



CREATE TABLE IF NOT EXISTS "public"."layout" (
    "id" character varying(50) NOT NULL,
    "name" character varying(100) NOT NULL,
    "description" "text",
    "template" character varying(100) NOT NULL,
    "css_file" character varying(100) NOT NULL
);


ALTER TABLE "public"."layout" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."resume" (
    "id" integer NOT NULL,
    "user_id" integer NOT NULL,
    "job_id" integer,
    "resume_data" "json",
    "created_at" timestamp without time zone,
    "updated_at" timestamp without time zone,
    "title" "text" NOT NULL,
    "template" character varying(50) DEFAULT 'standard'::character varying
);


ALTER TABLE "public"."resume" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."resume_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."resume_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."resume_id_seq" OWNED BY "public"."resume"."id";



CREATE TABLE IF NOT EXISTS "public"."scraper_run" (
    "id" integer NOT NULL,
    "source" character varying(50) NOT NULL,
    "start_time" timestamp without time zone NOT NULL,
    "end_time" timestamp without time zone,
    "status" character varying(20),
    "jobs_found" integer,
    "jobs_added" integer,
    "keywords" character varying(255),
    "location" character varying(255),
    "error_message" "text"
);


ALTER TABLE "public"."scraper_run" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."scraper_run_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."scraper_run_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."scraper_run_id_seq" OWNED BY "public"."scraper_run"."id";



CREATE TABLE IF NOT EXISTS "public"."section_type" (
    "id" character varying(50) NOT NULL,
    "name" character varying(100) NOT NULL,
    "fields" "jsonb",
    "display" character varying(50)
);


ALTER TABLE "public"."section_type" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."subscription" (
    "id" integer NOT NULL,
    "user_id" integer NOT NULL,
    "gateway_type" character varying(50) DEFAULT 'stripe'::character varying NOT NULL,
    "gateway_customer_id" character varying(255),
    "gateway_subscription_id" character varying(255),
    "plan_id" character varying(50) NOT NULL,
    "status" character varying(50) DEFAULT 'pending'::character varying,
    "created_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    "current_period_start" timestamp without time zone,
    "current_period_end" timestamp without time zone,
    "cancel_at_period_end" boolean DEFAULT false
);


ALTER TABLE "public"."subscription" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."theme" (
    "id" character varying(50) NOT NULL,
    "name" character varying(100) NOT NULL,
    "colors" "jsonb" NOT NULL,
    "typography" "jsonb" NOT NULL
);


ALTER TABLE "public"."theme" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user" (
    "id" integer NOT NULL,
    "username" character varying(80) NOT NULL,
    "email" character varying(120) NOT NULL,
    "password_hash" "text" NOT NULL,
    "verified" boolean DEFAULT false NOT NULL,
    "verification_sent_at" "date",
    "name" character varying(100),
    "phone" character varying(20),
    "location" character varying(100),
    "linkedin" character varying(200),
    "github" character varying(200),
    "website" character varying(200)
);


ALTER TABLE "public"."user" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."user_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."user_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."user_id_seq" OWNED BY "public"."user"."id";



ALTER TABLE ONLY "public"."application" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."application_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."job" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."job_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."resume" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."resume_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."scraper_run" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."scraper_run_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."user" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."user_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."application"
    ADD CONSTRAINT "application_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."job"
    ADD CONSTRAINT "job_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."job"
    ADD CONSTRAINT "job_slug_key" UNIQUE ("slug");



ALTER TABLE ONLY "public"."layout"
    ADD CONSTRAINT "layout_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."resume"
    ADD CONSTRAINT "resume_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."scraper_run"
    ADD CONSTRAINT "scraper_run_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."section_type"
    ADD CONSTRAINT "section_type_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."subscription"
    ADD CONSTRAINT "subscription_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."theme"
    ADD CONSTRAINT "theme_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user"
    ADD CONSTRAINT "user_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."user"
    ADD CONSTRAINT "user_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user"
    ADD CONSTRAINT "user_username_key" UNIQUE ("username");



ALTER TABLE ONLY "public"."application"
    ADD CONSTRAINT "application_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "public"."job"("id");



ALTER TABLE ONLY "public"."application"
    ADD CONSTRAINT "application_resume_id_fkey" FOREIGN KEY ("resume_id") REFERENCES "public"."resume"("id");



ALTER TABLE ONLY "public"."application"
    ADD CONSTRAINT "application_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id");



ALTER TABLE ONLY "public"."subscription"
    ADD CONSTRAINT "fk_user" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."resume"
    ADD CONSTRAINT "resume_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "public"."job"("id");



ALTER TABLE ONLY "public"."resume"
    ADD CONSTRAINT "resume_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id");





ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";












































































































































































































GRANT ALL ON TABLE "public"."application" TO "anon";
GRANT ALL ON TABLE "public"."application" TO "authenticated";
GRANT ALL ON TABLE "public"."application" TO "service_role";



GRANT ALL ON SEQUENCE "public"."application_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."application_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."application_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."job" TO "anon";
GRANT ALL ON TABLE "public"."job" TO "authenticated";
GRANT ALL ON TABLE "public"."job" TO "service_role";



GRANT ALL ON SEQUENCE "public"."job_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."job_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."job_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."layout" TO "anon";
GRANT ALL ON TABLE "public"."layout" TO "authenticated";
GRANT ALL ON TABLE "public"."layout" TO "service_role";



GRANT ALL ON TABLE "public"."resume" TO "anon";
GRANT ALL ON TABLE "public"."resume" TO "authenticated";
GRANT ALL ON TABLE "public"."resume" TO "service_role";



GRANT ALL ON SEQUENCE "public"."resume_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."resume_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."resume_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."scraper_run" TO "anon";
GRANT ALL ON TABLE "public"."scraper_run" TO "authenticated";
GRANT ALL ON TABLE "public"."scraper_run" TO "service_role";



GRANT ALL ON SEQUENCE "public"."scraper_run_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."scraper_run_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."scraper_run_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."section_type" TO "anon";
GRANT ALL ON TABLE "public"."section_type" TO "authenticated";
GRANT ALL ON TABLE "public"."section_type" TO "service_role";



GRANT ALL ON TABLE "public"."subscription" TO "anon";
GRANT ALL ON TABLE "public"."subscription" TO "authenticated";
GRANT ALL ON TABLE "public"."subscription" TO "service_role";



GRANT ALL ON TABLE "public"."theme" TO "anon";
GRANT ALL ON TABLE "public"."theme" TO "authenticated";
GRANT ALL ON TABLE "public"."theme" TO "service_role";



GRANT ALL ON TABLE "public"."user" TO "anon";
GRANT ALL ON TABLE "public"."user" TO "authenticated";
GRANT ALL ON TABLE "public"."user" TO "service_role";



GRANT ALL ON SEQUENCE "public"."user_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."user_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."user_id_seq" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "service_role";






























RESET ALL;
