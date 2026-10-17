-- Sample GP back-office rule file (SQL-flavoured rule/script dialect).
-- Illustrates the constructs recognised by the GP analyzer.
INCLUDE common/valuation.gp
INCLUDE accounting/ledger.gp

RULE ComputeNav(fund_id, valuation_date)
    SELECT sum(market_value) AS total_assets
      FROM positions
     WHERE fund = :fund_id
       AND val_date = :valuation_date;

    SELECT sum(liability) AS total_liabilities
      FROM liabilities
     WHERE fund = :fund_id;

    IF total_assets - total_liabilities < 0 THEN
        SET nav = 0;
    ELSE
        SET nav = total_assets - total_liabilities;
    END
END

PROCEDURE PostAccountingEntry(entry_id, fund_id, amount)
    IF amount <> 0 THEN
        INSERT INTO ledger (entry_id, fund, amount) VALUES (:entry_id, :fund_id, :amount);
    END
END
