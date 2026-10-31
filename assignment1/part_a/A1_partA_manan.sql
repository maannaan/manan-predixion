WITH buckets(bucket, sort_order) AS (
    VALUES ('Current', 1), ('1-30', 2), ('31-60', 3), ('61-90', 4), ('90+', 5)
),
classified AS (
    SELECT
        l.outstanding_amount,
        CASE
            WHEN CURRENT_DATE - l.due_date <= 0  THEN 'Current'
            WHEN CURRENT_DATE - l.due_date <= 30 THEN '1-30'
            WHEN CURRENT_DATE - l.due_date <= 60 THEN '31-60'
            WHEN CURRENT_DATE - l.due_date <= 90 THEN '61-90'
            ELSE '90+'
        END AS bucket
    FROM loans l
    WHERE l.outstanding_amount > 0
)
SELECT
    b.bucket,
    COUNT(c.bucket)                          AS loan_count,
    COALESCE(SUM(c.outstanding_amount), 0)   AS total_outstanding
FROM buckets b
LEFT JOIN classified c ON c.bucket = b.bucket
GROUP BY b.bucket, b.sort_order
ORDER BY b.sort_order;


SELECT
    l.loan_id,
    l.borrower_id,
    b.name,
    b.phone,
    l.due_date,
    CURRENT_DATE - l.due_date AS dpd,
    l.outstanding_amount
FROM loans l
JOIN borrowers b ON b.borrower_id = l.borrower_id
WHERE l.outstanding_amount > 0
  AND l.due_date < CURRENT_DATE
  AND NOT EXISTS (
        SELECT 1
        FROM call_logs cl
        WHERE cl.loan_id = l.loan_id
          AND cl.disposition IN ('CONNECTED', 'PTP', 'DISPUTE')
          AND cl.called_at >= now() - INTERVAL '7 days'
  )
ORDER BY dpd DESC, l.outstanding_amount DESC;


WITH ranked AS (
    SELECT
        l.borrower_id,
        p.payment_id,
        p.loan_id,
        p.amount,
        p.paid_at,
        LAG(p.paid_at) OVER w      AS previous_paid_at,
        ROW_NUMBER()  OVER (PARTITION BY l.borrower_id
                            ORDER BY p.paid_at DESC, p.payment_id DESC) AS rn
    FROM payments p
    JOIN loans l ON l.loan_id = p.loan_id
    WINDOW w AS (PARTITION BY l.borrower_id ORDER BY p.paid_at, p.payment_id)
)
SELECT
    borrower_id,
    payment_id        AS latest_payment_id,
    loan_id,
    amount            AS latest_amount,
    paid_at           AS latest_paid_at,
    previous_paid_at,
    paid_at - previous_paid_at AS gap_since_previous  -- INTERVAL
FROM ranked
WHERE rn = 1
ORDER BY borrower_id;


ALTER TABLE payments
    ADD CONSTRAINT payments_gateway_txn_id_key UNIQUE (gateway_txn_id);
ALTER TABLE payments
    ADD CONSTRAINT payments_amount_positive CHECK (amount > 0);
ALTER TABLE loans
    ADD CONSTRAINT loans_outstanding_non_negative CHECK (outstanding_amount >= 0);

CREATE INDEX idx_call_logs_loan_called_at
    ON call_logs (loan_id, called_at DESC)
    WHERE disposition IN ('CONNECTED', 'PTP', 'DISPUTE');
CREATE INDEX idx_loans_overdue
    ON loans (due_date)
    WHERE outstanding_amount > 0;

CREATE INDEX idx_payments_loan_paid_at ON payments (loan_id, paid_at, payment_id);
CREATE INDEX idx_loans_borrower        ON loans (borrower_id); 