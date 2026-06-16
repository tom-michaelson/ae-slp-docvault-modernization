:::danger Windows JSON CLI Quirks

On Windows, double quotes within JSON strings are not passed properly when using Powershell. You must do ONE of the following:

A) Use a bash shell (e.g. Git Bash)

B) Use single quotes within your JSON string, like this:

```powershell
uv run -m awa.main run -w awa-hello-world -i "{'name': 'World'}"
```

:::
