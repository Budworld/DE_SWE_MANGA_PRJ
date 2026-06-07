with ranked as (
    select
        record,
        row_number() over (
            partition by record->>'scanlation_group_id'
            order by loaded_at desc, id desc
        ) as row_number
    from {{ source('silver', 'scanlation_group') }}
)

select
    record->>'scanlation_group_id' as scanlation_group_id,
    record->>'source_group_id' as source_group_id,
    record->>'name' as name,
    record->'alt_names' as alt_names,
    record->>'website' as website,
    record->>'discord' as discord,
    record->>'contact_email' as contact_email,
    record->>'description' as description,
    nullif(record->>'created_at', '')::timestamptz as created_at,
    nullif(record->>'updated_at', '')::timestamptz as updated_at,
    record->>'crawl_run_id' as crawl_run_id
from ranked
where row_number = 1
