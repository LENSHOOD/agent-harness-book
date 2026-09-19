WITH dedup AS (
      SELECT *, ROW_NUMBER() OVER(PARTITION BY event_id, valid_from ORDER BY ingest_id) AS rn
      FROM semantic.subscription_revenue_v4
    ) SELECT month, province, plan,
      SUM(recognized_revenue_cny - COALESCE(refunds_cny,0)) AS net_revenue_cny,
      COUNT(DISTINCT account_id) AS accounts
    FROM dedup WHERE rn=1 AND account_id IS NOT NULL AND recognized_revenue_cny IS NOT NULL
      AND region='CN' AND month IN ('2026-06-01','2026-07-01')
    GROUP BY month, province, plan HAVING COUNT(DISTINCT account_id)>=20;