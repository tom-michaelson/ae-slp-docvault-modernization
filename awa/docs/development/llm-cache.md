# LLM Cache

LLM calls can be cached. Caching greatly improves iteration speed when working on large workflows. It can also be used as a cost-saving measure when re-running large workflows.

## How It Works

LLM caching hashes all the inputs that go into an LLM call, including the prompt and all model parameters. This hash is used to compute the cache key. The raw response from the LLM is recorded as the cached value.

When making an LLM call, we first check the cache for a matching key. If found, we return the cached value. If not, we make the LLM call and cache the result. This means that if a cache value is found, you will not see any LLM logs for the given call.

## Toggle On/Off

The global `use_cache` setting defaults to `true`.

LLM caching can be turned on or off using the `use_cache` flag in `config.yaml`. Per-model settings (if present) will override the global setting.

### Globally

::: code-group

```yaml[config.yaml]
llm:
    behavior:
        use_cache: true
```

:::

### Per-Model

::: code-group

```yaml[config.yaml]
llm:
  # ...
  models:
    - name: gpt41
      # ...
      use_cache: true
```

:::

## Clear the Cache

The cache is stored on the local filesystem at this path: `cache/llm`. To clear the cache, you can simply delete this directory.
