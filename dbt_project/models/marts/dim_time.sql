/*
  dim_time.sql
  ------------
  Time spine table: one row per calendar date covering the full range
  of session dates plus a 30-day buffer on each side. Required by
  MetricFlow for cumulative metrics and period-over-period comparisons.
*/

with date_range as (

    select
        min(session_date) - interval '30 days' as start_date,
        max(session_date) + interval '30 days' as end_date
    from {{ ref('fct_sessions') }}

),

spine as (

    select
        unnest(
            generate_series(
                (select start_date from date_range)::date,
                (select end_date   from date_range)::date,
                interval '1 day'
            )
        )::date as date_day

),

final as (

    select
        date_day,

        -- week / month / quarter boundaries
        date_trunc('week',    date_day)::date    as week_start,
        date_trunc('month',   date_day)::date    as month_start,
        date_trunc('quarter', date_day)::date    as quarter_start,

        -- calendar attributes
        extract(year    from date_day)::integer  as year_num,
        extract(month   from date_day)::integer  as month_num,
        extract(quarter from date_day)::integer  as quarter_num,
        dayname(date_day)                        as day_of_week_name,
        dayofweek(date_day) in (0, 6)            as is_weekend,
        extract(week from date_day)::integer     as week_of_year

    from spine

)

select * from final
