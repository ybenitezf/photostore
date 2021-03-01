# Photostore

Photo archive for adelante.cu

## development

Requires Python 3, node 12 and yarn

```bash
git clone https://github.com/ybenitezf/photostore
cd photostore
python3 -m venv env
. env/bin/activate
make dev
```

And run database migrations `flask db upgrade -d photostore/migrations` or `flask deploy db-upgrade`

After changes make a new version with:

```bash
$ bump2version patch # possible: major / minor / patch
$ git push
$ git push --tags
```

## tests

```bash
make test
```

Or with coverage

```bash
make coverage
```

## Generating distribution archives

```bash
make dist
```

## Install

REVIEW THIS

```bash
pip install https://github.com/ybenitezf/photostore/archive/master.tar.gz
```

## Admin commands

- `flask security fixpermissions`: Resolve permissions issues when posible
- `flask index reindex`: Reindex all objects for search, the index must exists
