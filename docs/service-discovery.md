# Service discovery

```python
instances = await nacos.list_instances(
    app, "payments", group="DEFAULT_GROUP", healthy_only=True,
    cluster="BLUE", metadata={"region": "cn-east"},
)
selected = await nacos.get_one_healthy_instance(app, "payments", strategy="weight")
```

The adapter accepts SDK lists and dicts containing `hosts`, `instances`, or
nested `data`. Normalized rows contain IP, port, service/cluster names, weight,
healthy/enabled/ephemeral flags, and copied metadata. Malformed individual rows
are skipped. Selection strategies are `first`, `random`, and `weight`.

