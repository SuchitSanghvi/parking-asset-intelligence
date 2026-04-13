/*
  fct_sessions.sql
  ----------------
  Valid parking sessions only. Filters out:
    - Orphaned entries  (no matching exit)
    - Orphaned exits    (no matching entry)
    - Negative-duration sessions (clock-sync bugs)
    - Duplicate entries (camera misfires)

  Adds time-bucketing and calendar dimensions for analysis.

  Incrementally loaded using entry_ts as the watermark -- new sessions
  are appended on each run. Uses merge strategy with session_id as the
  unique key to handle late-arriving exit events.
*/

{{
    config(
        materialized='incremental',
        unique_key='session_id',
        on_schema_change='append_new_columns'
    )
}}

with sessions as (

    select * from {{ ref('int_sessions') }}
    {% if is_incremental() %}
    where entry_ts > (
        select coalesce(max(entry_ts), '1900-01-01'::timestamp)
        from {{ this }}
    )
    {% endif %}

),

valid as (

    select * from sessions
    where is_orphaned_entry    = false
      and is_orphaned_exit     = false
      and is_negative_duration = false
      and is_duplicate_entry   = false

),

local_events as (

    -- One row per (event_date, city) — prevents fan-out when multiple events
    -- occur in the same city on the same date.
    select distinct
        event_date,
        lower(city) as city
    from {{ ref('stg_local_events') }}

),

final as (

    select
        s.session_id,
        s.entry_event_id,
        s.exit_event_id,
        s.lot_id,
        s.license_plate,
        s.entry_ts,
        s.exit_ts,
        s.duration_minutes,
        s.amount_charged,
        s.payment_method,
        s.entry_camera_id,
        s.exit_camera_id,

        -- calendar dimensions
        cast(s.entry_ts as date)                            as session_date,
        dayofweek(s.entry_ts)                               as day_of_week_num,
        dayname(s.entry_ts)                                 as day_of_week,
        dayofweek(s.entry_ts) in (0, 6)                    as is_weekend,

        -- time-of-day bucket based on entry hour
        case
            when hour(s.entry_ts) between 5  and 11 then 'morning'
            when hour(s.entry_ts) between 12 and 16 then 'afternoon'
            when hour(s.entry_ts) between 17 and 20 then 'evening'
            else 'overnight'
        end                                                 as time_of_day_bucket,

        -- local event flag: true when an event occurred in this lot's city on the session date
        (le.event_date is not null)                         as has_local_event

    from valid s
    left join {{ ref('dim_lots') }} d on s.lot_id = d.lot_id
    left join local_events le
        on cast(s.entry_ts as date) = le.event_date
        and lower(d.city) = le.city

)

select * from final
