## 2. Clone the repo

<!--@include: ./clone.md-->

## 3. Initialize the solution

Run the following command in the root of the repo:

```bash
make install
```

If `make` doesn't work for you for any reason, open the makefile and run the commands within the `install` block.

## 4. Run the solution

Run the following command in the root of the repo:

```bash
make start
```

OR

```bash
uv run -m awa.main start
```

## 5. Confirm the solution is running

Navigate to the AWA UI at http://localhost:8000
