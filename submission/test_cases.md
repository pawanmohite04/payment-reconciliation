# Test Cases

| ID | Scenario | Expected result |
|---|---|---|
| TC01 | Normal transaction has same transaction ID and amount in platform and bank | MATCHED |
| TC02 | 31 October platform transaction settles on 1 November | LATE_SETTLEMENT for October |
| TC03 | Three 10.004 platform entries settle at 10.00 each | Each MATCHED within row tolerance; aggregate variance 0.012 is flagged |
| TC04 | Same platform transaction ID occurs twice | DUPLICATE; unique transaction count counts it once |
| TC05 | Refund references an original payment absent from platform data | ORPHAN_REFUND |
| TC06 | Platform payment has no bank settlement in current or following month | MISSING_SETTLEMENT |
| TC07 | Bank settlement has no corresponding platform transaction | Appears in unmatched bank entries |
| TC08 | Invalid date or blank amount is supplied | Validation error is raised |
| TC09 | Unsupported currency is supplied | Validation error is raised |
