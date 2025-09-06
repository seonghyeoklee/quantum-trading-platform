-- Cleanup old Airflow tables from public schema
-- These tables are now in the airflow schema

DROP TABLE IF EXISTS public.ab_permission CASCADE;
DROP TABLE IF EXISTS public.ab_permission_view CASCADE;
DROP TABLE IF EXISTS public.ab_permission_view_role CASCADE;
DROP TABLE IF EXISTS public.ab_register_user CASCADE;
DROP TABLE IF EXISTS public.ab_role CASCADE;
DROP TABLE IF EXISTS public.ab_user CASCADE;
DROP TABLE IF EXISTS public.ab_user_role CASCADE;
DROP TABLE IF EXISTS public.ab_view_menu CASCADE;
DROP TABLE IF EXISTS public.alembic_version CASCADE;
DROP TABLE IF EXISTS public.callback_request CASCADE;
DROP TABLE IF EXISTS public.connection CASCADE;
DROP TABLE IF EXISTS public.dag CASCADE;
DROP TABLE IF EXISTS public.dag_code CASCADE;
DROP TABLE IF EXISTS public.dag_owner_attributes CASCADE;
DROP TABLE IF EXISTS public.dag_pickle CASCADE;
DROP TABLE IF EXISTS public.dag_run CASCADE;
DROP TABLE IF EXISTS public.dag_run_note CASCADE;
DROP TABLE IF EXISTS public.dag_schedule_dataset_reference CASCADE;
DROP TABLE IF EXISTS public.dag_tag CASCADE;
DROP TABLE IF EXISTS public.dag_warning CASCADE;
DROP TABLE IF EXISTS public.dagrun_dataset_event CASCADE;
DROP TABLE IF EXISTS public.log CASCADE;
DROP TABLE IF EXISTS public.slot_pool CASCADE;
DROP TABLE IF EXISTS public.task_instance CASCADE;
DROP TABLE IF EXISTS public.variable CASCADE;
DROP TABLE IF EXISTS public.xcom CASCADE;