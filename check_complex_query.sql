SELECT
    ROUTINE_NAME AS Name,
    'Procedure/Function' AS Type
FROM
    information_schema.ROUTINES
WHERE
    ROUTINE_SCHEMA = 'mini_project'

UNION ALL

SELECT
    TABLE_NAME AS Name,
    'View' AS Type
FROM
    information_schema.TABLES
WHERE
    TABLE_SCHEMA = 'mini_project' AND TABLE_TYPE = 'VIEW'

UNION ALL

SELECT
    TRIGGER_NAME AS Name,
    'Trigger' AS Type
FROM
    information_schema.TRIGGERS
WHERE
    TRIGGER_SCHEMA = 'mini_project'

ORDER BY
    Name;