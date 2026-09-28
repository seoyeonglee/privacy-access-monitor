# Sample data

`sample_access_logs.csv` is a synthetic, public-safe demonstration dataset.

It contains:
- ordinary business-hour access events
- labeled examples of off-hours activity
- a geographic mismatch
- high-volume exports
- an unusual-system event
- a multi-customer access burst

The identifiers are fictional and no employer or customer data is used.

For a larger deterministic dataset, run:

```bash
python src/generate_data.py
```
