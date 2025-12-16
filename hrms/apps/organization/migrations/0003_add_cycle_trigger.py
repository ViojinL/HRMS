from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0002_alter_organization_create_by_alter_organization_id_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION check_org_cycle()
            RETURNS TRIGGER AS $$
            DECLARE
                cycle_exists BOOLEAN;
            BEGIN
                IF NEW.parent_org_id IS NULL THEN
                    RETURN NEW;
                END IF;

                IF NEW.parent_org_id = NEW.org_id THEN
                   RAISE EXCEPTION 'Organization cannot be its own parent';
                END IF;

                WITH RECURSIVE org_path AS (
                    SELECT org_id, parent_org_id
                    FROM organization
                    WHERE org_id = NEW.parent_org_id
                    UNION ALL
                    SELECT o.org_id, o.parent_org_id
                    FROM organization o
                    JOIN org_path p ON o.org_id = p.parent_org_id
                )
                SELECT EXISTS (
                    SELECT 1 FROM org_path WHERE org_id = NEW.org_id
                ) INTO cycle_exists;

                IF cycle_exists THEN
                    RAISE EXCEPTION 'Cycle detected in organization hierarchy';
                END IF;

                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trigger_check_org_cycle ON organization;
            CREATE TRIGGER trigger_check_org_cycle
            BEFORE INSERT OR UPDATE OF parent_org_id ON organization
            FOR EACH ROW
            EXECUTE FUNCTION check_org_cycle();
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS trigger_check_org_cycle ON organization;
            DROP FUNCTION IF EXISTS check_org_cycle;
            """
        ),
    ]
